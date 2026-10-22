"""Guarded index-patch of the FORM3 torso edit onto ANY current HeroBase_Male_Silhouette.blend (other chats install head/arms/hands/legs concurrently).
blender -b --factory-startup --python apply_form3.py -- <current.blend> <out.blend> [--force]
Sets the torso-zone vertices of export/form3_zone_delta.npz (all |x|<0.20, 0.77<=z<1.352) to their FORM3 values.
ABORTS unless every one of those vertices is either at its FORM2 position (base0) or already at FORM3 (idempotent)."""
import sys, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso3')
a = sys.argv[sys.argv.index('--') + 1:]; src, out = a[0], a[1]; force = '--force' in a
D = np.load(W / 'export/form3_zone_delta.npz'); idx = D['indices']; f32 = lambda x: x.astype(np.float32).astype(np.float64)
b0, new = f32(D['base0']), f32(D['new'])
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Body_M'].data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
assert me.shape_keys is None
if len(V) <= idx.max(): raise SystemExit('ABORT: Body_M has fewer vertices than the FORM3 delta indexes')
cur = V[idx]; at0 = np.all(cur == b0, axis=1); atn = np.all(cur == new, axis=1); bad = ~(at0 | atn)
if bad.any() and not force: raise SystemExit(f'ABORT: {int(bad.sum())} torso-zone vertices are at neither the FORM2 start nor the FORM3 position - edited by someone else; use --force to overwrite')
V[idx] = new; me.vertices.foreach_set('co', V.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('APPLY_FORM3_DONE', len(idx), 'vertices set;', int((at0 & ~atn).sum()), 'were at FORM2,', int(atn.sum()), 'already at FORM3,', int(bad.sum()), 'foreign ->', out, '| body verts', len(V))
