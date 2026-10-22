"""Dump the locked bodies (read-only) to npz for numpy-only analysis.
blender -b --factory-startup --python dump_bodies.py"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *

for tag in ('male', 'female'):
    reset_scene()
    o = load_body_copy(tag)
    co = mesh_co(o)
    tris = mesh_tris(o)
    me = o.data
    # per-vertex normals (corner-normal average is fine for probing)
    nrm = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('normal', nrm)
    np.savez_compressed(WORK / 'data' / f'{tag}_body.npz', co=co, tris=tris, nrm=nrm.reshape(-1, 3))
    print(tag, co.shape, tris.shape)
