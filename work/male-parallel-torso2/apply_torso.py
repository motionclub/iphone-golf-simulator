"""Rebase the torso edit onto ANY newer HeroBase_Male_Silhouette.blend (e.g. after the head/arms/legs chats installed theirs).
blender -b --factory-startup --python apply_torso.py -- <current.blend> <out.blend> [--force]
Moves only the vertices listed in export/torso_zone_delta.npz (indices into Body_M, all inside the torso zone z 0.77..1.40, |x|<=0.205/0.28).
Aborts if any of those vertices is no longer at its start-SHA position (someone else edited the torso zone) unless --force."""
import sys, numpy as np, bpy
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-torso2')
a = sys.argv[sys.argv.index('--') + 1:]; src, out = a[0], a[1]; force = '--force' in a
D = np.load(W / 'export/torso_zone_delta.npz'); idx = D['indices']; base = D['base']; new = D['new']
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Body_M'].data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
assert me.shape_keys is None
if V[idx].shape != base.shape or len(V) < idx.max() + 1: raise SystemExit('Body_M vertex count/topology differs from the torso start blend -> cannot rebase')
dirty = np.any(V[idx] != base, axis=1)
if dirty.any() and not force: raise SystemExit(f'ABORT: {int(dirty.sum())} torso-zone vertices were edited since the torso start SHA (use --force to overwrite them)')
V[idx] = new; me.vertices.foreach_set('co', V.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out, compress=False); print('APPLY_TORSO_DONE', len(idx), 'vertices set ->', out, '(overwrote', int(dirty.sum()), 'dirty)')
