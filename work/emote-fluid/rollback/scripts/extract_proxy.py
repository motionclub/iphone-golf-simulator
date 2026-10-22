"""extract_proxy.py -- Blender (headless) on work/hero-dressed/export/HeroBase_<Hero>_Dressed.blend:  skin data of the meshes that act as collision PROXIES in the numpy solver.

  blender -b --factory-startup <dressed blend> --python extract_proxy.py -- <male|female>

Writes work/emote-overhaul/data/proxy_<tag>.npz with, per object (body, shirt, shorts): co (n,3) bind-pose vertex positions (object matrix applied), idx (n,4) bone indices (the order of
work/emotes/data/skin_<tag>.npz 'names'), w (n,4) weights (top 4, normalised), tris (m,3) vertex indices.  Checks that the body matches skin_<tag>.npz."""
import os
import sys

import numpy as np
import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
tag = sys.argv[sys.argv.index('--') + 1]
sk = np.load(f'{REPO}/work/emotes/data/skin_{tag}.npz', allow_pickle=True)
names = [str(n) for n in sk['names']]
bidx = {n: i for i, n in enumerate(names)}
BODY = 'Body_M' if tag == 'male' else 'Body_F'
out = {}
for key, nm in (('body', BODY), ('shirt', 'Kit_Top'), ('shorts', 'Kit_Bottom')):
    ob = bpy.data.objects[nm]
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(n, 3)
    M = np.array(ob.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    gname = {g.index: g.name for g in ob.vertex_groups}
    idx = np.zeros((n, 4), np.int32)
    w = np.zeros((n, 4), np.float32)
    for v in me.vertices:
        gs = sorted(((g.weight, bidx[gname[g.group]]) for g in v.groups if gname.get(g.group) in bidx), reverse=True)[:4]
        s = sum(x[0] for x in gs) or 1.0
        for k, (wt, bi) in enumerate(gs):
            idx[v.index, k], w[v.index, k] = bi, wt / s
    me.calc_loop_triangles()
    tris = np.array([lt.vertices[:] for lt in me.loop_triangles], np.int32)
    out[key + '_co'], out[key + '_idx'], out[key + '_w'], out[key + '_tris'] = co, idx, w, tris
    print('PROXY', key, nm, n, 'verts', len(tris), 'tris', 'matrix identity' if np.allclose(M, np.eye(4)) else 'matrix applied')
d = np.abs(out['body_co'] - sk['co']).max() if len(sk['co']) == len(out['body_co']) else -1
print('BODY_vs_skin_npz max |dco| =', d, '(verts %d vs %d)' % (len(out['body_co']), len(sk['co'])))
os.makedirs(f'{REPO}/work/emote-overhaul/data', exist_ok=True)
np.savez_compressed(f'{REPO}/work/emote-overhaul/data/proxy_{tag}.npz', names=np.array(names), **out)
print('PROXY_DONE', tag)
