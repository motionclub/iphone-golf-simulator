"""blender -b --factory-startup --python set_custom_normals.py -- <in.blend> <anorm.npz> <out.blend>
Body_F: per-vertex custom normals = default smooth normals everywhere, blended toward the analytic surface normals inside the weighted zone (anorm: N, idx, wz)."""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, bpy
import fl
inb, an, outb = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=inb)
ob = bpy.data.objects['Body_F']; me = ob.data
n = len(me.vertices)
Nd = np.empty(n * 3); me.vertices.foreach_get('normal', Nd); Nd = Nd.reshape(-1, 3)
d = np.load(an); idx = d['idx']; Na = d['N'][idx]; w = d['wz'][:, None] if 'wz' in d.files else 1.0
Nn = Nd.copy()
mix = w * Na + (1 - w) * Nd[idx]
Nn[idx] = mix / np.maximum(np.linalg.norm(mix, axis=1, keepdims=True), 1e-12)
me.normals_split_custom_set_from_vertices([tuple(v) for v in Nn])
print('custom normals set; has_custom_normals', me.has_custom_normals, 'zone verts', len(idx))
bpy.ops.wm.save_as_mainfile(filepath=outb)
