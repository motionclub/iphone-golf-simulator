"""Dump world-space positions, loop topology and custom normals of the White kit pieces of a StandardKit blend (opened as the MAIN file, so matrix_world is valid)."""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np

from dcommon import *

tag = args_after_dashes()[0]
H = HERO[tag]
bpy.context.view_layer.update()
out = {}
for p in PIECES:
    o = bpy.data.objects[H['pieces'][p]]
    me = o.data
    M = np.array(o.matrix_world, np.float64)
    co = mesh_co(o) @ M[:3, :3].T + M[:3, 3]
    nl = len(me.loops)
    lv = np.empty(nl, np.int32)
    me.loops.foreach_get('vertex_index', lv)
    ls = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get('loop_start', ls)
    cn = np.empty(nl * 3, np.float32)
    if me.has_custom_normals:
        me.corner_normals.foreach_get('vector', cn)
    out[p] = dict(co=co, lv=lv, ls=ls, cn=cn.reshape(-1, 3), custom=bool(me.has_custom_normals), name=o.name)
np.savez(f'{DATA}/kitsource_{tag}.npz', **{f'{p}_{k}': v for p, d in out.items() for k, v in d.items() if k != 'name'})
print('KITSOURCE', tag, {p: len(d['co']) for p, d in out.items()})
