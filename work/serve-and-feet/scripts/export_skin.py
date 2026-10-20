"""Export the body skinning of a hero (rest vertices, up to 4 bone indices + weights per vertex) so foot-vertex heights can be computed per frame in numpy.

  blender -b <source MatchAnims blend> --python export_skin.py -- <male|female>

Writes work/serve-and-feet/data/skin_<hero>.npz.  Reads the source blend only (never saves it)."""
import json
import os
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
OUT = REPO + '/work/serve-and-feet/data'
SRC_DATA = REPO + '/work/match-anim-set/data'
tag = sys.argv[sys.argv.index('--') + 1]
body = bpy.data.objects['Body_M' if tag == 'male' else 'Body_F']
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
rigj = json.load(open(f'{SRC_DATA}/rig_{tag}.json'))
names = [b['name'] for b in rigj['bones']]
bidx = {n: i for i, n in enumerate(names)}
vg_to_bone = {vg.index: bidx.get(vg.name, -1) for vg in body.vertex_groups}
me = body.data
n = len(me.vertices)
co = np.empty(n * 3)
me.vertices.foreach_get('co', co)
co = co.reshape(-1, 3)
M = np.array(body.matrix_world)
assert np.abs(M - np.eye(4)).max() < 1e-9, 'body object transform is not identity'
assert np.abs(np.array(rig.matrix_world) - np.eye(4)).max() < 1e-9, 'rig object transform is not identity'
idx = np.zeros((n, 4), np.int32)
w = np.zeros((n, 4), np.float32)
for v in me.vertices:
    gs = sorted(((g.weight, vg_to_bone.get(g.group, -1)) for g in v.groups if vg_to_bone.get(g.group, -1) >= 0), reverse=True)[:4]
    for k, (wt, b) in enumerate(gs):
        idx[v.index, k] = b
        w[v.index, k] = wt
s = w.sum(1, keepdims=True)
w = np.where(s > 1e-9, w / np.maximum(s, 1e-9), w)
dom = idx[np.arange(n), np.argmax(w, 1)]
mods = [(m.type, m.object.name if getattr(m, 'object', None) else None) for m in body.modifiers]
np.savez_compressed(f'{OUT}/skin_{tag}.npz', co=co, idx=idx, w=w, dom=dom, names=np.array(names))
print('SKIN', tag, n, 'verts; mods', mods, 'foot verts L/R', int(np.isin(dom, [bidx['LeftFoot'], bidx['LeftToes']]).sum()), int(np.isin(dom, [bidx['RightFoot'], bidx['RightToes']]).sum()))
