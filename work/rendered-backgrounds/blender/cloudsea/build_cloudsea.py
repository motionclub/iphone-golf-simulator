"""Tileable cloud-sea tops (stratocumulus seen from above) with six-way lightmaps, rendered in Cycles
from our own volume. Replaces the painted CloudTops texture under the skyscraper deck; the game relights
it from the real sun (RenderedCloudSea shader).

  Blender -b --factory-startup --python build_cloudsea.py -- [--samples S] [--size N]

Volume: periodic fbm stratocumulus layer (bumpy domed tops, cells, gaps), one tile of 3 km,
rendered orthographic straight down at the centre of a 3x3 instanced tiling (so light from the
sides enters through neighbouring tiles = no seams). Lights: sun from +X, -X, +Y, -Y (low, 20 deg
elevation, the skyscraper's sun height), sun from straight above, and a uniform white sky.
Outputs (this folder): CloudSea_A.png (R=+X G=-X B=+Y A=-Y), CloudSea_B.png (R=top G=ambient
B=height A=1), cloudsea.json. Resumable: each render is skipped when its EXR exists.
"""
import bpy, sys, os, json, math, time
import numpy as np
import openvdb

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default):
    return type(default)(argv[argv.index(name) + 1]) if name in argv else default
SAMPLES = arg('--samples', 32); SIZE = arg('--size', 1024)
TILE = 30.0     # Blender units (100 m) -> 3 km
TOP = 5.0       # layer thickness (500 m)
VOX = .08
os.makedirs(os.path.join(HERE, 'renders'), exist_ok=True)

class Periodic:
    """Value noise on an n^3 lattice that tiles every `period` units in x and y."""
    def __init__(self, seed, n):
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

def density():
    nx = int(TILE / VOX); nz = int((TOP + 1.5) / VOX)
    xs = (np.arange(nx) + .5) * VOX; zs = (np.arange(nz) + .5) * VOX - .5
    X, Y, Z = np.meshgrid(xs, xs, zs, indexing='ij')
    def fbm(seed, base_cells, octaves, zscale):
        s, a, norm = 0, 1, 0
        for o in range(octaves):
            cells = base_cells * 2 ** o
            nz_ = Periodic(seed + o, cells)
            k = cells / TILE
            s = s + a * (nz_(X * k, Y * k, Z * k * zscale + o * 3.1) * 2 - 1); norm += a; a *= .5
        return s / norm
    # a field of cumulus heads: periodic domes (big cells), smaller domes riding on them (cauliflower)
    rng = np.random.default_rng(2026)
    gx, gy = X[..., 0], Y[..., 0]
    def domes(count, rmin, rmax, hmin, hmax, base):
        h = np.full(gx.shape, -10.0, np.float32)
        cx, cy = rng.uniform(0, TILE, count), rng.uniform(0, TILE, count)
        r, hh = rng.uniform(rmin, rmax, count), rng.uniform(hmin, hmax, count)
        for i in range(count):
            dx = (gx - cx[i] + TILE / 2) % TILE - TILE / 2; dy = (gy - cy[i] + TILE / 2) % TILE - TILE / 2
            q = 1 - (dx * dx + dy * dy) / (r[i] * r[i])
            h = np.maximum(h, np.where(q > 0, base(cx[i], cy[i]) + hh[i] * np.sqrt(np.clip(q, 0, 1)), -10))
        return h
    big = domes(70, 2.0, 3.6, 1.2, 2.6, lambda x, y: 1.2)
    big = np.maximum(big, 1.4)                                   # the deck under the heads is continuous
    small = domes(520, .5, 1.1, .3, .8, lambda x, y: 0)
    # small heads sit on the big ones: offset each by the big surface under it
    top2 = np.maximum(big, big - .35 + small)
    top = top2[..., None] + .25 * fbm(23, 24, 2, .4)
    bottom = .3 + .3 * fbm(41, 4, 2, 0)
    d = np.minimum(top - Z, Z - bottom)                          # >0 inside the layer
    d = d + .18 * fbm(53, 40, 2, 1.0)                            # billowy surface
    cov = np.clip(d / .3, 0, 1).astype(np.float32)
    return cov, top

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == 'METAL'
    sc.cycles.device = 'GPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 20; sc.cycles.volume_bounces = 16; sc.cycles.volume_step_rate = 1.5
    sc.render.resolution_x = sc.render.resolution_y = SIZE; sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '32'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0, 0, 0, 1); bg.inputs['Strength'].default_value = 0
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = TILE; cam.location = (TILE / 2, TILE / 2, 40); cam.rotation_euler = (0, 0, 0)
    cam.data.clip_end = 100
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.angle = math.radians(.6); sun.data.energy = 1.0
    return sc, cam, sun, bg

def material():
    m = bpy.data.materials.new('Cloud'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'density'
    # fine billows from 4D noise on a torus (x, y wrapped) so the tile stays seamless
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    def op(kind, a, b=None, val=None):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = kind
        nt.links.new(a, n.inputs[0]) if not isinstance(a, (int, float)) else n.inputs[0].__setattr__('default_value', a)
        if b is not None: nt.links.new(b, n.inputs[1]) if not isinstance(b, (int, float)) else n.inputs[1].__setattr__('default_value', b)
        return n.outputs[0]
    R_ = TILE / (2 * math.pi)
    ax = op('MULTIPLY', sep.outputs['X'], 2 * math.pi / TILE); ay = op('MULTIPLY', sep.outputs['Y'], 2 * math.pi / TILE)
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(op('MULTIPLY', op('COSINE', ax), R_), comb.inputs[0]); nt.links.new(op('MULTIPLY', op('SINE', ax), R_), comb.inputs[1])
    nt.links.new(op('MULTIPLY', op('COSINE', ay), R_), comb.inputs[2])
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.noise_dimensions = '4D'
    noise.inputs['Scale'].default_value = 3.0; noise.inputs['Detail'].default_value = 8; noise.inputs['Roughness'].default_value = .6
    nt.links.new(comb.outputs[0], noise.inputs['Vector'])
    # W must wrap too: sin(ay)*R plus a small Z term
    nt.links.new(op('ADD', op('MULTIPLY', op('SINE', ay), R_), op('MULTIPLY', sep.outputs['Z'], 1.0)), noise.inputs['W'])
    ero = op('MULTIPLY', op('SUBTRACT', 1.0, noise.outputs['Fac']), .7)
    dens = nt.nodes.new('ShaderNodeMath'); dens.operation = 'MULTIPLY'; dens.use_clamp = True
    nt.links.new(op('SUBTRACT', attr.outputs['Fac'], ero), dens.inputs[0]); dens.inputs[1].default_value = 3.0
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 9.0
    nt.links.new(dens.outputs[0], mul.inputs[0])
    scat = nt.nodes.new('ShaderNodeVolumeScatter'); scat.inputs['Anisotropy'].default_value = .55
    nt.links.new(mul.outputs[0], scat.inputs['Density']); nt.links.new(scat.outputs[0], out.inputs['Volume'])
    return m

LIGHTS = {  # travel direction of the light
    'px': (-math.cos(math.radians(20)), 0, -math.sin(math.radians(20))),
    'nx': (math.cos(math.radians(20)), 0, -math.sin(math.radians(20))),
    'py': (0, -math.cos(math.radians(20)), -math.sin(math.radians(20))),
    'ny': (0, math.cos(math.radians(20)), -math.sin(math.radians(20))),
    'top': (0, 0, -1),
}

def main():
    t0 = time.time()
    cov, top = density()
    print('[cloudsea] density', cov.shape, f'{time.time() - t0:.1f}s', flush=True)
    path = os.path.join(HERE, 'cloudsea.vdb')
    g = openvdb.FloatGrid(); g.copyFromArray(cov); g.name = 'density'; g.transform = openvdb.createLinearTransform(voxelSize=VOX)
    openvdb.write(path, grids=[g])
    sc, cam, sun, bg = setup(); mat = material()
    vol = bpy.data.volumes.new('sea'); vol.filepath = path; vol.materials.append(mat)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            ob = bpy.data.objects.new(f'sea_{i}_{j}', vol); sc.collection.objects.link(ob); ob.location = (i * TILE, j * TILE, -.5)
    from mathutils import Vector
    outs = {}
    for name, travel in LIGHTS.items():
        sun.rotation_euler = Vector(travel).to_track_quat('-Z', 'Y').to_euler()
        f = os.path.join(HERE, 'renders', f'{name}.exr'); sc.render.filepath = f
        if not (os.path.exists(f) and os.path.getsize(f) > 0): bpy.ops.render.render(write_still=True)
        outs[name] = f; print('[cloudsea]', name, f'{time.time() - t0:.0f}s', flush=True)
    sun.hide_render = True; bg.inputs['Color'].default_value = (1, 1, 1, 1); bg.inputs['Strength'].default_value = 1
    f = os.path.join(HERE, 'renders', 'ambient.exr'); sc.render.filepath = f
    if not (os.path.exists(f) and os.path.getsize(f) > 0): bpy.ops.render.render(write_still=True)
    outs['ambient'] = f
    def load(p):
        im = bpy.data.images.load(p); a = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im); return a
    M = {k: load(v)[..., 0] for k, v in outs.items()}
    peak = max(np.percentile(M[k], 99.7) for k in LIGHTS); pa = np.percentile(M['ambient'], 99.7)
    def nrm(x, p): return np.clip(x / p, 0, 1)
    A = np.dstack([nrm(M['px'], peak), nrm(M['nx'], peak), nrm(M['py'], peak), nrm(M['ny'], peak)])
    B = np.dstack([nrm(M['top'], peak), nrm(M['ambient'], pa), np.zeros_like(M['top']), np.ones_like(M['top'])])
    for name, arr in (('CloudSea_A.png', A), ('CloudSea_B.png', B)):
        enc = srgb(arr)                      # sRGB in all four channels; the shader decodes alpha itself
        img = bpy.data.images.new(name, arr.shape[1], arr.shape[0], alpha=True)
        img.pixels[:] = enc.astype(np.float32).ravel(); img.filepath_raw = os.path.join(HERE, name); img.file_format = 'PNG'; img.save()
    json.dump(dict(tile_m=TILE * 100, layer_m=TOP * 100, sun_elevation_side_deg=20, sun_peak=float(peak), ambient_peak=float(pa),
                   channels=dict(A='R=+X G=-X B=+Y(north) A=-Y, sun 20 deg high (sRGB, alpha too)', B='R=sun overhead G=uniform sky B=0 A=1')),
              open(os.path.join(HERE, 'cloudsea.json'), 'w'), indent=1)
    print('[cloudsea] done', f'{time.time() - t0:.0f}s', flush=True)

def srgb(x):
    x = np.clip(x, 0, 1); return np.where(x <= .0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - .055)

main()
