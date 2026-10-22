"""verify the assembled blend: topology, below-ring bit-identity, ring weld, loops.  blender -b --python verify_asm.py -- <assembled.blend> [json out]"""
import sys, json, collections
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f2-head/tools')
import numpy as np, bpy
import fl
argv = sys.argv[sys.argv.index('--') + 1:]
blend = argv[0]
bpy.ops.wm.open_mainfile(filepath=blend)
body = bpy.data.objects['Body_F']; me = body.data
V, F = fl.mesh_arrays(me)
# start
bpy.ops.wm.open_mainfile(filepath=str(fl.W / 'baseline/HeroBase_Female_start.blend'))
V0, F0 = fl.mesh_arrays(bpy.data.objects['Body_F'].data)
bpy.ops.wm.open_mainfile(filepath=blend)
body = bpy.data.objects['Body_F']; me = body.data
vm = json.load(open(blend.replace('.blend', '_vmap.json'))); o2n = np.array(vm['old2new']); nb = vm['n_body_kept']
ringd = np.load(fl.W / 'data/ring.npz'); ring = ringd['ring']
zone_faces = set(int(i) for i in ringd['zone_faces'])
# body vertices = old vertices used by kept faces
used_old = np.zeros(len(V0), bool)
for i, f in enumerate(F0):
    if i not in zone_faces: used_old[list(f)] = True
body_old = np.where(used_old)[0]
d = np.abs(V[o2n[body_old]] - V0[body_old].astype(np.float32)).max()
print('body vertices (below the collar ring and the ring itself):', len(body_old), 'max coordinate difference vs start:', float(d), 'm   bit-identical:', bool(d == 0.0))
res = dict(body_verts_compared=int(len(body_old)), max_diff_m=float(d), bit_identical=bool(d == 0.0))
# topology
cnt = collections.Counter()
for f in F:
    n = len(f)
    for i in range(n):
        a, b = int(f[i]), int(f[(i + 1) % n]); cnt[(min(a, b), max(a, b))] += 1
bnd = sum(1 for c in cnt.values() if c == 1); nonman = sum(1 for c in cnt.values() if c > 2)
print('faces', len(F), 'tris', sum(len(f) - 2 for f in F), 'boundary edges', bnd, 'non-manifold edges', nonman)
res.update(faces=len(F), tris=int(sum(len(f) - 2 for f in F)), boundary_edges=int(bnd), nonmanifold_edges=int(nonman))
# zone-restricted accounting: which vertices differ in position from start? none must be below ring: z of ring >= max z of untouched body? check z of all body verts
print('z range body', V[:nb, 2].min(), V[:nb, 2].max())
print('ring z range', V0[ring][:, 2].min(), V0[ring][:, 2].max())
res['ring_z_min'] = float(V0[ring][:, 2].min()); res['ring_z_max'] = float(V0[ring][:, 2].max())
print('vertex groups:', [g.name for g in body.vertex_groups])
print('materials:', [m.name for m in me.materials])
print('height', V[:, 2].max() - V[:, 2].min(), 'bbox min', V.min(0), 'max', V.max(0))
res['height_m'] = float(V[:, 2].max() - V[:, 2].min())
if len(argv) > 1: json.dump(res, open(argv[1], 'w'), indent=1)
