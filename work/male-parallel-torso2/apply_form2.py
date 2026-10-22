"""Guarded rebase of the torso FORM2 edit onto ANY current HeroBase_Male_Silhouette.blend (other chats may have installed head/arms/legs).
blender -b --factory-startup --python apply_form2.py -- <current.blend> <out.blend> [--force]
Sets the torso-zone vertices in export/form2_zone_delta.npz (all inside the torso zone, none at z >= 1.352) to their FORM2 values.
ABORTS unless every one of those vertices is at the torso-PASS start position, or at the first FORM2 install (v1), or already at FORM2 (idempotent)."""
import sys, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2')
a = sys.argv[sys.argv.index('--') + 1:]; src, out = a[0], a[1]; force = '--force' in a
D = np.load(W / 'export/form2_zone_delta.npz'); idx = D['indices']; f32 = lambda x: x.astype(np.float32).astype(np.float64)
b0, b1, new = f32(D['base0']), f32(D['base1']), f32(D['new'])
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Body_M'].data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
assert me.shape_keys is None
if len(V) <= idx.max(): raise SystemExit('Body_M vertex count differs from the FORM2 start blend -> cannot rebase')
cur = V[idx]; at0 = np.all(cur == b0, axis=1); at1 = np.all(cur == b1, axis=1); atn = np.all(cur == new, axis=1); bad = ~(at0 | at1 | atn)
if bad.any() and not force: raise SystemExit(f'ABORT: {int(bad.sum())} torso-zone vertices are at none of the known states (PASS start / FORM2 v1 / FORM2) - edited by someone else; use --force to overwrite')
V[idx] = new; me.vertices.foreach_set('co', V.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
print('APPLY_FORM2_DONE', len(idx), 'vertices set;', int((at0 & ~atn).sum()), 'were at PASS start,', int((at1 & ~at0 & ~atn).sum()), 'at FORM2 v1,', int(atn.sum()), 'already at FORM2,', int(bad.sum()), 'foreign ->', out)
