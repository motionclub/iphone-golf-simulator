"""Cumulus cloud impostors with six-way lightmaps, rendered in Cycles from our own volumes.

  Blender -b --factory-startup --python build_clouds.py -- [--only N] [--samples S] [--size WxH]

For each cloud: a numpy SDF (smooth union of a hierarchy of spheres + fbm billows, flat base)
-> OpenVDB coverage grid -> Cycles volume (fine fbm erosion in the shader, Mie-like phase,
many bounces). Rendered orthographic from the front with a black world and one sun from each
of the six card axes, plus one render lit only by a uniform white sky (ambient), plus alpha.

Outputs (this folder):
  renders/cloud_NN_<light>.exr      raw float renders (deleted after packing unless --keep)
  CloudSixWay_A.png   R=light from +X (right)  G=light from above  B=light from behind   A=alpha
  CloudSixWay_B.png   R=light from -X (left)   G=light from below  B=light from the front A=ambient
  clouds.json         atlas rects, scale factors, cloud sizes in metres
Packing = 2 columns x 4 rows of WxH cells (default 1024x512 -> 2048x2048), sRGB-encoded.
"""
import bpy, sys, os, json, math, time
import numpy as np
import openvdb

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default
ONLY = arg('--only', -1)
SAMPLES = arg('--samples', 96)
CELL = tuple(int(v) for v in arg('--size', '1024x512').split('x'))
KEEP = '--keep' in argv
LIGHTSEL = arg('--lights', 'right,left,top,bottom,back,front,ambient').split(',')
BOUNCES = arg('--bounces', 16)
NCLOUD = 8
UNIT = 100.0  # metres per Blender unit
os.makedirs(os.path.join(HERE, 'renders'), exist_ok=True)
os.makedirs(os.path.join(HERE, 'vdb'), exist_ok=True)

# ---------------------------------------------------------------- noise
class Value3:
    def __init__(self, seed, n=48):
        self.n = n; self.g = np.random.default_rng(seed).random((n, n, n)).astype(np.float32)
    def __call__(self, x, y, z):
        n = self.n
        xi, yi, zi = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64), np.floor(z).astype(np.int64)
        fx, fy, fz = x - xi, y - yi, z - zi
        fx, fy, fz = [f * f * f * (f * (f * 6 - 15) + 10) for f in (fx, fy, fz)]
        out = 0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                    out = out + w * self.g[(xi + dx) % n, (yi + dy) % n, (zi + dz) % n]
        return out
def fbm(noise, x, y, z, octaves=4, lac=2.03, gain=.5):
    s, a, f, norm = 0, 1, 1, 0
    for o in range(octaves):
        s = s + a * (noise(x * f + o * 17.1, y * f + o * 5.3, z * f + o * 11.7) * 2 - 1); norm += a
        a *= gain; f *= lac
    return s / norm

# ---------------------------------------------------------------- cloud shapes
def spheres_for(i):
    """Return (centres Nx3, radii N) in Blender units (100 m), base at z=0, roughly centred on x=y=0.
    Real cumulus: a flat base, a few rising turrets (stacked, narrowing spheres), cauliflower lobes
    on every exposed upper/outer surface, then smaller lobes on those."""
    rng = np.random.default_rng(1000 + i)
    kind = ['tower', 'cluster', 'wide', 'tower', 'cluster', 'wide', 'congestus', 'small'][i]
    W = {'tower': 8.5, 'cluster': 10, 'wide': 14, 'congestus': 10.5, 'small': 6}[kind] * rng.uniform(.9, 1.1)
    Hmax = {'tower': .78, 'cluster': .5, 'wide': .3, 'congestus': .85, 'small': .5}[kind] * W
    C, R = [], []
    nt = {'tower': 4, 'cluster': 6, 'wide': 8, 'congestus': 5, 'small': 3}[kind]
    xs = np.sort(rng.uniform(-.42, .42, nt)) * W * (.6 if kind == 'small' else 1)
    for x in xs:
        centre = 1 - abs(x) / (W * .5)
        H = Hmax * (.35 + .65 * centre) * rng.uniform(.6, 1.0)
        r0 = W * rng.uniform(.11, .16) * (.8 + .4 * centre)
        y = rng.uniform(-.6, .6)
        # a dome, not a pillar: wide body, a narrower cap, a head only if the turret is tall
        z, r = r0 * .5, r0
        while z < H:
            C.append((x + rng.uniform(-.2, .2) * r, y, z)); R.append(r)
            z += r * .55; r *= rng.uniform(.68, .8)
            if r < r0 * .3: break
    # base skirt between turrets
    for x in np.linspace(-.45 * W, .45 * W, int(W * 1.2)):
        r = W * .08 * rng.uniform(.8, 1.2); C.append((x, rng.uniform(-.5, .5), r * .55)); R.append(r)
    big = len(C)
    def lobes(idx, count, shrink, out):
        for j in idx:
            c, r = np.array(C[j]), R[j]
            for _ in range(count):
                d = rng.normal(size=3); d[1] *= .7; d[2] = d[2] * .9 + .55
                d /= np.linalg.norm(d)
                if d[2] < -.15: continue
                nr = r * shrink * rng.uniform(.75, 1.2)
                C.append(tuple(c + d * r * out)); R.append(nr)
    lobes(range(big), 10, .40, .80)
    mid = len(C)
    lobes(range(big, mid), 4, .45, .78)
    C, R = np.array(C, np.float32), np.array(R, np.float32)
    C[:, 2] = np.maximum(C[:, 2], R * .35)
    return C, R, kind

def coverage_grid(i, voxel):
    C, R, kind = spheres_for(i)
    lo = (C - R[:, None]).min(0) - .8; hi = (C + R[:, None]).max(0) + .8; lo[2] = -.3
    dims = np.ceil((hi - lo) / voxel).astype(int)
    xs = [lo[a] + (np.arange(dims[a]) + .5) * voxel for a in range(3)]
    X, Y, Z = np.meshgrid(*xs, indexing='ij')
    X, Y, Z = X.astype(np.float32), Y.astype(np.float32), Z.astype(np.float32)
    d = np.full(X.shape, 1e3, np.float32)
    for c, r in zip(C, R):
        k = .2 * r; ext = r + k + .1
        sl = tuple(slice(max(0, int((c[a] - ext - lo[a]) / voxel)), min(dims[a], int((c[a] + ext - lo[a]) / voxel) + 2)) for a in range(3))
        x, y, z = X[sl], Y[sl], Z[sl]
        di = np.sqrt((x - c[0]) ** 2 + (y - c[1]) ** 2 + (z - c[2]) ** 2) - r
        dd = d[sl]
        h = np.clip(.5 + .5 * (dd - di) / k, 0, 1)
        d[sl] = dd * (1 - h) + di * h - k * h * (1 - h)
    nz = Value3(77 + i)
    d += .22 * fbm(nz, X * .55, Y * .55, Z * .55, 3)           # large billow
    d += .12 * fbm(nz, X * 1.9 + 9, Y * 1.9, Z * 1.9, 3)
    d += .05 * fbm(nz, X * 4.6 + 3, Y * 4.6, Z * 4.6, 2)        # mid cauliflower
    base = .12 + .12 * fbm(nz, X * .3, Y * .3, Z * 0 + 3, 2)    # mostly flat, slightly ragged base
    d = np.maximum(d, (base - Z) * 1.5)
    cov = np.clip(-d / .3, 0, 1).astype(np.float32)
    return cov, lo, dims, kind

def write_vdb(i, voxel):
    cov, lo, dims, kind = coverage_grid(i, voxel)
    g = openvdb.FloatGrid(); g.copyFromArray(cov); g.name = 'density'
    g.transform = openvdb.createLinearTransform(voxelSize=voxel)
    path = os.path.join(HERE, 'vdb', f'cloud_{i:02d}.vdb'); openvdb.write(path, grids=[g])
    size = (dims * voxel)
    return path, lo, size, kind

# ---------------------------------------------------------------- scene
def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == 'METAL'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = BOUNCES + 4; sc.cycles.volume_bounces = BOUNCES; sc.cycles.transparent_max_bounces = 8
    sc.cycles.volume_step_rate = 1.5; sc.cycles.volume_preview_step_rate = 1.0
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = CELL; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.angle = math.radians(.6); sun.data.energy = 1.0
    return sc, cam, sun, bg

def cloud_material():
    m = bpy.data.materials.new('Cloud'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'density'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.noise_dimensions = '3D'
    noise.inputs['Scale'].default_value = 3.2; noise.inputs['Detail'].default_value = 9; noise.inputs['Roughness'].default_value = .62
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    # density = saturate((coverage - (1 - noise) * .6) * 3.2) * D
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'SUBTRACT'; m1.inputs[0].default_value = 1
    nt.links.new(noise.outputs['Fac'], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = .75
    nt.links.new(m1.outputs[0], m2.inputs[0])
    m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'SUBTRACT'
    nt.links.new(attr.outputs['Fac'], m3.inputs[0]); nt.links.new(m2.outputs[0], m3.inputs[1])
    m4 = nt.nodes.new('ShaderNodeMath'); m4.operation = 'MULTIPLY'; m4.inputs[1].default_value = 3.2; m4.use_clamp = True
    nt.links.new(m3.outputs[0], m4.inputs[0])
    m5 = nt.nodes.new('ShaderNodeMath'); m5.operation = 'MULTIPLY'; m5.inputs[1].default_value = 9.0  # extinction per 100 m
    nt.links.new(m4.outputs[0], m5.inputs[0])
    scat = nt.nodes.new('ShaderNodeVolumeScatter')
    scat.inputs['Color'].default_value = (1, 1, 1, 1)
    scat.inputs['Anisotropy'].default_value = .55   # HG: a silver lining without Mie's huge spike
    nt.links.new(m5.outputs[0], scat.inputs['Density'])
    nt.links.new(scat.outputs[0], out.inputs['Volume'])
    return m

LIGHTS = {  # name -> direction the light TRAVELS (camera looks along +Y, right=+X, up=+Z)
    'right': (-1, 0, 0), 'left': (1, 0, 0), 'top': (0, 0, -1), 'bottom': (0, 0, 1),
    'back': (0, -1, 0), 'front': (0, 1, 0),
}

def aim(obj, travel):
    from mathutils import Vector
    obj.rotation_euler = Vector(travel).to_track_quat('-Z', 'Y').to_euler()

def render_cloud(i, sc, cam, sun, bg, mat):
    t0 = time.time()
    path, lo, size, kind = write_vdb(i, voxel=.07)
    vol = bpy.data.volumes.new(f'cloud_{i:02d}'); vol.filepath = path
    ob = bpy.data.objects.new(f'cloud_{i:02d}', vol); sc.collection.objects.link(ob)
    ob.location = lo; vol.materials.append(mat)
    # frame: width along X, height along Z, keep CELL aspect
    cx, cz = lo[0] + size[0] / 2, lo[2] + size[2] / 2
    aspect = CELL[0] / CELL[1]
    scale = max(size[0], size[2] * aspect) * 1.04
    cam.data.ortho_scale = scale
    cam.location = (cx, lo[1] - 40, cz); cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.clip_end = 200
    outs = {}
    for name, travel in [(n, t) for n, t in LIGHTS.items() if n in LIGHTSEL]:
        aim(sun, travel); sun.hide_render = False; bg.inputs['Strength'].default_value = 0
        f = os.path.join(HERE, 'renders', f'cloud_{i:02d}_{name}.exr'); sc.render.filepath = f
        (os.path.exists(f) and os.path.getsize(f) > 0) or bpy.ops.render.render(write_still=True)  # resumable
        outs[name] = f
    if 'ambient' not in LIGHTSEL:
        bpy.data.objects.remove(ob); bpy.data.volumes.remove(vol); return dict(index=i, files=outs)
    sun.hide_render = True; bg.inputs['Color'].default_value = (1, 1, 1, 1); bg.inputs['Strength'].default_value = 1
    f = os.path.join(HERE, 'renders', f'cloud_{i:02d}_ambient.exr'); sc.render.filepath = f
    (os.path.exists(f) and os.path.getsize(f) > 0) or bpy.ops.render.render(write_still=True)  # resumable
    outs['ambient'] = f
    bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0; sun.hide_render = False
    bpy.data.objects.remove(ob); bpy.data.volumes.remove(vol)
    print(f'[clouds] cloud {i} {kind} size_m={(size * UNIT).round(0).tolist()} in {time.time() - t0:.1f}s', flush=True)
    return dict(index=i, kind=kind, width_m=float(scale * UNIT), height_m=float(scale / aspect * UNIT),
                base_from_bottom=float((0 - (cz - scale / aspect / 2)) / (scale / aspect)), files=outs)

def load_exr(path):
    img = bpy.data.images.load(path); a = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img); return a

def srgb(x):
    x = np.clip(x, 0, 1); return np.where(x <= .0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - .055)

def pack(infos):
    W, H = CELL; A = np.zeros((H * 4, W * 2, 4), np.float32); B = np.zeros_like(A)
    maps = {}
    for info in infos:
        maps[info['index']] = {k: load_exr(f) for k, f in info['files'].items()}
    peak_sun = max(np.percentile(m[k][..., 0], 99.7) for m in maps.values() for k in LIGHTS)
    peak_amb = max(np.percentile(m['ambient'][..., 0], 99.7) for m in maps.values())
    for info in infos:
        i = info['index']; m = maps[i]; col, row = i % 2, i // 2
        alpha = m['front'][..., 3]
        def lum(k, peak):
            # straight (un-premultiplied) radiance so bilinear edges stay correct after alpha blend
            return np.where(alpha > 1e-3, m[k][..., 0] / np.maximum(alpha, 1e-3), 0) / peak
        cellA = np.dstack([lum('right', peak_sun), lum('top', peak_sun), lum('back', peak_sun), alpha])
        cellB = np.dstack([lum('left', peak_sun), lum('bottom', peak_sun), lum('front', peak_sun), lum('ambient', peak_amb)])
        y0 = row * H  # Blender pixel rows start at the bottom; keep that (Unity UV origin is bottom-left too)
        A[y0:y0 + H, col * W:(col + 1) * W] = cellA; B[y0:y0 + H, col * W:(col + 1) * W] = cellB
        info['uv_rect'] = [col / 2, row / 4, .5, .25]
    for name, arr in (('CloudSixWay_A.png', A), ('CloudSixWay_B.png', B)):
        enc = arr.copy(); enc[..., :3] = srgb(enc[..., :3])
        if name.endswith('B.png'): enc[..., 3] = srgb(enc[..., 3])
        img = bpy.data.images.new(name, arr.shape[1], arr.shape[0], alpha=True)
        img.pixels[:] = np.clip(enc, 0, 1).ravel(); img.filepath_raw = os.path.join(HERE, name)
        img.file_format = 'PNG'; img.save()
    return float(peak_sun), float(peak_amb)

def main():
    sc, cam, sun, bg = setup_scene(); mat = cloud_material()
    idx = [ONLY] if ONLY >= 0 else list(range(NCLOUD))
    infos = [render_cloud(i, sc, cam, sun, bg, mat) for i in idx]
    if ONLY < 0:
        ps, pa = pack(infos)
        for info in infos: info.pop('files')
        json.dump(dict(cell=CELL, atlas=[CELL[0] * 2, CELL[1] * 4], unit_m=UNIT, sun_peak=ps, ambient_peak=pa,
                       channels=dict(A='R=light from +X, G=from above, B=from behind (backlit), A=alpha',
                                     B='R=from -X, G=from below, B=from the front, A=ambient (uniform sky)'),
                       clouds=infos), open(os.path.join(HERE, 'clouds.json'), 'w'), indent=1)
        if not KEEP:
            import shutil; shutil.rmtree(os.path.join(HERE, 'renders')); shutil.rmtree(os.path.join(HERE, 'vdb'))
    print('[clouds] done', flush=True)

main()
