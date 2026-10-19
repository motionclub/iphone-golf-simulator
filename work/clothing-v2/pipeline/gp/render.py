"""GARMENT PIPELINE: GPU id renders in headless Blender (gpu offscreen; ~8 ms per 200k-triangle view).
Each triangle carries a uint32 id; the image returns the front-most id and its linear depth (metres from the camera plane).
Root space: Y up, hero faces +Z. Orthographic views around a centre."""
import math
import numpy as np
import gpu
try:
    gpu.init()
except Exception:
    pass
from gpu_extras.batch import batch_for_shader  # noqa: F401 (loads the module)
import mathutils

_SH = None


def shader():
    global _SH
    if _SH is None:
        io = gpu.types.GPUStageInterfaceInfo("gp_ids")
        io.flat('UINT', 'fid')
        io.smooth('FLOAT', 'dep')
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant('MAT4', 'mvp')
        info.push_constant('MAT4', 'view')
        info.vertex_in(0, 'VEC3', 'pos')
        info.vertex_in(1, 'UINT', 'id')
        info.vertex_out(io)
        info.fragment_out(0, 'VEC4', 'col')
        info.vertex_source("void main(){fid=id; dep=-(view*vec4(pos,1.0)).z; gl_Position=mvp*vec4(pos,1.0);}")
        info.fragment_source("void main(){uint v=fid; col=vec4(float(v&255u),float((v>>8u)&255u),float((v>>16u)&255u),float((v>>24u)&255u))/255.0;}")
        _SH = gpu.shader.create_from_info(info)
    return _SH


def view_dirs(az_n=8, els=(-20.0, 10.0, 40.0)):
    out = []
    for e in els:
        for k in range(az_n):
            a = 2 * math.pi * k / az_n
            out.append((a, math.radians(e)))
    return out


def view_matrix(centre, az, el, dist=4.0):
    """camera looking at centre from azimuth az (0 = in front of the hero, +Z) and elevation el."""
    d = mathutils.Vector((math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)))
    eye = mathutils.Vector(centre) + d * dist
    z = d.normalized()
    x = mathutils.Vector((0, 1, 0)).cross(z).normalized()
    y = z.cross(x)
    R = mathutils.Matrix((x, y, z))          # rows
    V = mathutils.Matrix.Identity(4)
    V[0][0:3], V[1][0:3], V[2][0:3] = R[0], R[1], R[2]
    t = -(R @ eye)
    V[0][3], V[1][3], V[2][3] = t
    return V


def footprint_gb():
    """this process's physical footprint in GB (macOS proc_pid_rusage ri_phys_footprint: includes GPU memory, which RSS does not).
    Background Blender never releases per-draw GPU work (~200 MB per cover frame, 10-18), so long stages stop their chunk at a limit."""
    try:
        import ctypes, os as _os, struct
        buf = ctypes.create_string_buffer(512)                # rusage_info_v0 is 96 bytes: a roomy buffer, no struct overrun
        lib = ctypes.CDLL('/usr/lib/libproc.dylib')
        if lib.proc_pid_rusage(ctypes.c_int(_os.getpid()), ctypes.c_int(0), buf) == 0:
            return struct.unpack_from('<Q', buf.raw, 72)[0] / 1e9      # uuid[16] + 7 x uint64 -> ri_phys_footprint
    except Exception:
        pass
    return 0.0


MEM_LIMIT_GB = float(__import__('os').environ.get('GP_MEM_GB', 4.0))


def ortho(half_w, half_h, near=0.5, far=8.0):
    P = mathutils.Matrix.Identity(4)
    P[0][0] = 1 / half_w; P[1][1] = 1 / half_h
    P[2][2] = -2 / (far - near); P[2][3] = -(far + near) / (far - near)
    return P


class Renderer:
    def __init__(self, W=512, H=640, half_h=1.0):
        self.W, self.H = W, H
        self.half_h, self.half_w = half_h, half_h * W / H
        self.off = gpu.types.GPUOffScreen(W, H, format='RGBA8')
        self.P = ortho(self.half_w, self.half_h)
        self.fmt = gpu.types.GPUVertFormat()
        self.fmt.attr_add(id='pos', comp_type='F32', len=3, fetch_mode='FLOAT')
        self.fmt.attr_add(id='id', comp_type='U32', len=1, fetch_mode='INT')
        self.mpp = 2 * half_h / H                # metres per pixel
        # background Blender kept every per-call read-back allocation (70 MB/frame -> 45 GB covers, 10-18): the colour / depth
        # read-backs reuse two fixed buffers (vertex buffers cannot be refilled once drawn)
        self._col = gpu.types.Buffer('UBYTE', W * H * 4)
        self._dep = gpu.types.Buffer('FLOAT', W * H)

    def batch(self, P, tri, ids):
        """P (n,3), tri (m,3), ids (m,) uint32 -> GPU batch of unindexed triangles."""
        v = np.ascontiguousarray(P[tri].reshape(-1, 3), np.float32)
        i = np.ascontiguousarray(np.repeat(ids.astype(np.uint32), 3))
        vbo = gpu.types.GPUVertBuf(self.fmt, len(v))
        vbo.attr_fill('pos', v); vbo.attr_fill('id', i)
        return gpu.types.GPUBatch(type='TRIS', buf=vbo)

    def draw(self, batches, V):
        """-> ids (H,W) uint32 (0 = background), depth (H,W) float metres (inf = background)."""
        sh = shader()
        mvp = self.P @ V
        with self.off.bind():
            fb = gpu.state.active_framebuffer_get()
            fb.clear(color=(0, 0, 0, 0), depth=1.0)
            gpu.state.depth_test_set('LESS'); gpu.state.depth_mask_set(True)
            gpu.state.face_culling_set('NONE')
            sh.bind(); sh.uniform_float('mvp', mvp); sh.uniform_float('view', V)
            for b in batches: b.draw(sh)
            col = fb.read_color(0, 0, self.W, self.H, 4, 0, 'UBYTE', data=self._col)
            dep = fb.read_depth(0, 0, self.W, self.H, data=self._dep)
        col.dimensions = self.W * self.H * 4
        c = np.frombuffer(col, np.uint8).reshape(self.H, self.W, 4).astype(np.uint32)
        ids = c[..., 0] | (c[..., 1] << 8) | (c[..., 2] << 16) | (c[..., 3] << 24)
        dep.dimensions = self.W * self.H
        z = np.frombuffer(dep, np.float32).reshape(self.H, self.W).astype(np.float64)
        near, far = 0.5, 8.0
        lin = np.where(z < 1.0, near + z * (far - near), np.inf)   # ortho: depth is linear in [near, far]
        return ids[::-1], lin[::-1]                                   # row 0 = top


def open3(mask):
    """3x3 binary opening (removes isolated specks)."""
    m = mask
    e = m.copy()
    e[1:] &= m[:-1]; e[:-1] &= m[1:]; e[:, 1:] &= m[:, :-1]; e[:, :-1] &= m[:, 1:]
    d = e.copy()
    d[1:] |= e[:-1]; d[:-1] |= e[1:]; d[:, 1:] |= e[:, :-1]; d[:, :-1] |= e[:, 1:]
    return d & m


_LOOK = None


def look_shader():
    global _LOOK
    if _LOOK is None:
        io = gpu.types.GPUStageInterfaceInfo("gp_look")
        io.smooth('VEC3', 'nn')
        io.flat('VEC3', 'cc')
        info = gpu.types.GPUShaderCreateInfo()
        info.push_constant('MAT4', 'mvp')
        info.push_constant('MAT4', 'view')
        info.vertex_in(0, 'VEC3', 'pos')
        info.vertex_in(1, 'VEC3', 'nrm')
        info.vertex_in(2, 'VEC3', 'col')
        info.vertex_out(io)
        info.fragment_out(0, 'VEC4', 'fc')
        info.vertex_source("void main(){nn=(view*vec4(nrm,0.0)).xyz; cc=col; gl_Position=mvp*vec4(pos,1.0);}")
        info.fragment_source("void main(){vec3 n=normalize(nn); if(!gl_FrontFacing) n=-n; float d=abs(dot(n,normalize(vec3(.35,.55,.75))));"
                             "float r=pow(max(0.0,1.0-abs(n.z)),3.0)*.25; fc=vec4(cc*(.32+.68*d)+r,1.0);}")
        _LOOK = gpu.shader.create_from_info(info)
    return _LOOK


def look_batch(R, P, tri, colour, N=None):
    if N is None:
        fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
        N = np.zeros_like(P)
        for k in range(3): np.add.at(N, tri[:, k], fn)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    fmt = gpu.types.GPUVertFormat()
    fmt.attr_add(id='pos', comp_type='F32', len=3, fetch_mode='FLOAT')
    fmt.attr_add(id='nrm', comp_type='F32', len=3, fetch_mode='FLOAT')
    fmt.attr_add(id='col', comp_type='F32', len=3, fetch_mode='FLOAT')
    v = np.ascontiguousarray(P[tri].reshape(-1, 3), np.float32)
    nn = np.ascontiguousarray(N[tri].reshape(-1, 3), np.float32)
    c = np.ascontiguousarray(np.broadcast_to(np.asarray(colour, np.float32), (len(v), 3)) if np.ndim(colour) == 1 else np.repeat(np.asarray(colour, np.float32), 3, 0))
    vbo = gpu.types.GPUVertBuf(fmt, len(v))
    vbo.attr_fill('pos', v); vbo.attr_fill('nrm', nn); vbo.attr_fill('col', c)
    return gpu.types.GPUBatch(type='TRIS', buf=vbo)


def look_draw(R, batches, V, bg=(.93, .93, .95)):
    sh = look_shader()
    with R.off.bind():
        fb = gpu.state.active_framebuffer_get()
        fb.clear(color=(*bg, 1), depth=1.0)
        gpu.state.depth_test_set('LESS'); gpu.state.depth_mask_set(True); gpu.state.face_culling_set('NONE')
        sh.bind(); sh.uniform_float('mvp', R.P @ V); sh.uniform_float('view', V)
        for b in batches: b.draw(sh)
        col = fb.read_color(0, 0, R.W, R.H, 4, 0, 'UBYTE')
    col.dimensions = R.W * R.H * 4
    return np.frombuffer(col, np.uint8).reshape(R.H, R.W, 4)[::-1, :, :3].copy()


def write_png(path, img):
    import zlib, struct
    img = np.ascontiguousarray(img, np.uint8)
    h, w = img.shape[:2]; ch = 1 if img.ndim == 2 else img.shape[2]
    raw = b''.join(b'\x00' + img[y].tobytes() for y in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    ct = {1: 0, 3: 2, 4: 6}[ch]
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, ct, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
