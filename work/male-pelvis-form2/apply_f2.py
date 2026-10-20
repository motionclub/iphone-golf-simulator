"""Guarded index-patch of the PELVIS FORM2 edit onto ANY current HeroBase_Male_Silhouette.blend (other chats install head/arms/hands/legs/torso concurrently).
blender -b --factory-startup --python apply_f2.py -- <current.blend> <out.blend> [--force]
Sets the vertices of export/f2_delta.npz (indices, base0, new; float32) to their NEW positions.
ABORTS unless every one of those vertices is either at its start-blend position (base0) or already at NEW (idempotent)."""
import os
import sys, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
a = sys.argv[sys.argv.index('--') + 1:]; src, out = a[0], a[1]; force = '--force' in a
D = np.load(W / os.environ.get('NP_DELTA', 'export/f2_delta.npz')); idx = D['indices']; f32 = lambda x: x.astype(np.float32).astype(np.float64)
b0, new = f32(D['base0']), f32(D['new'])
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Body_M'].data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
assert me.shape_keys is None
if len(V) <= idx.max(): raise SystemExit('ABORT: Body_M has fewer vertices than the PELVIS_FORM2 delta indexes')
cur = V[idx]; at0 = np.all(cur == b0, axis=1); atn = np.all(cur == new, axis=1); bad = ~(at0 | atn)
if bad.any() and not force: raise SystemExit(f'ABORT: {int(bad.sum())} pelvis-form2 vertices are at neither the start position nor the NEW position - edited by someone else; use --force to overwrite')
V[idx] = new; me.vertices.foreach_set('co', V.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('APPLY_F2_DONE', len(idx), 'vertices set;', int((at0 & ~atn).sum()), 'were at start,', int(atn.sum()), 'already at NEW,', int(bad.sum()), 'foreign ->', out, '| body verts', len(V))
