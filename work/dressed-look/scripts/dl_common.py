"""Shared helpers for the DRESSED_LOOK job (runs inside Blender 5.2, headless; numpy only exists in Blender's python).

Rules baked in here:
  * the five source blends are only ever READ (open_mainfile is followed by an immediate save_as to work/dressed-look/ or
    they are read through bpy.data.libraries.load); nothing in the repo's art directory is touched;
  * "mesh hash" = SHA-256 over the geometry of a mesh datablock (positions, face topology, custom normals, UVs, material
    indices, sharp flags). Vertex-group weights, modifiers, selection/hide flags are NOT part of it (documented in the gate defs).
"""
import hashlib
import json
import math
import os
import sys

import numpy as np
import bpy
from mathutils import Matrix, Vector

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/dressed-look'
DATA = WORK + '/data'
EXPORT = WORK + '/export'
PROOF = WORK + '/proof'
RAW = PROOF + '/raw'

SRC = dict(
    male_body=REPO + '/work/male-pelvis-form3/export/merged_fd04bc28.blend',
    female_body=REPO + '/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend',
    kit_male=REPO + '/work/standard-tennis-kit-worn/export/StandardKit_Male.blend',
    kit_female=REPO + '/work/standard-tennis-kit-worn/export/StandardKit_Female.blend',
    racket=REPO + '/work/classic-tennis-racket/export/Racket_Classic.blend',
    socket_json=REPO + '/work/classic-tennis-racket/export/racket_classic_socket.json',
)
SHA = dict(
    male_body='d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781',
    female_body='a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1',
    kit_male='ad07a7b9ba984b0f220f975b9fe1b0c1b7068d9897c7e6f96e44f70d23aa77a9',
    kit_female='f19a9c03789b7af343c56b005ed587137e8764779d31c3109942156ee71eaf4e',
    racket='53e83714856a14c1533653b3fce3e164dfb17e9c58c995cbdb325d86eec7e8ba',
)

HERO = {
    'male': dict(label='Male', body='Body_M', face='Face_M', body_src='male_body', kit_src='kit_male',
                 polo='Kit_Top_Polo_M', bottom='Kit_Bottom_Shorts_M', fitref='FitRef_Body_M'),
    'female': dict(label='Female', body='Body_F', face='Face_F', body_src='female_body', kit_src='kit_female',
                   polo='Kit_Top_Polo_F', bottom='Kit_Bottom_Skort_F', fitref='FitRef_Body_F'),
}
COLORS = ('White', 'Black')
SOCKETS = ('Chest_Top', 'Hip_Bottom', 'Foot_L_Shoe', 'Foot_R_Shoe')


def piece_names(tag, color):
    """(piece object name in the kit blend, socket it belongs to)."""
    h = HERO[tag]
    return [
        (f"{h['polo']}_{color}", 'Chest_Top'),
        (f"{h['bottom']}_{color}", 'Hip_Bottom'),
        (f'Kit_Sock_L_{color}', 'Foot_L_Shoe'),
        (f'Kit_Shoe_L_{color}', 'Foot_L_Shoe'),
        (f'Kit_Sock_R_{color}', 'Foot_R_Shoe'),
        (f'Kit_Shoe_R_{color}', 'Foot_R_Shoe'),
    ]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def verify_sources():
    out = {}
    for k, want in SHA.items():
        got = sha256_file(SRC[k])
        out[k] = dict(path=SRC[k], sha256=got, expected=want, ok=(got == want))
    return out


# --------------------------------------------------------------------------- mesh access / hashing
def mesh_co(obj, world=False):
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    if world:
        M = np.array(obj.matrix_world, np.float64)
        co = co.astype(np.float64) @ M[:3, :3].T + M[:3, 3]
    return co


def mesh_tris(obj):
    me = obj.data
    me.calc_loop_triangles()
    t = np.empty(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get('vertices', t)
    return t.reshape(-1, 3)


def _h(h, arr):
    a = np.ascontiguousarray(arr)
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes())


def mesh_geometry_hash(me):
    """SHA-256 of the geometry of a mesh datablock (see module docstring for what is / is not covered)."""
    h = hashlib.sha256()
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', co)
    _h(h, co)
    nl, npoly = len(me.loops), len(me.polygons)
    cv = np.empty(nl, np.int32)
    me.loops.foreach_get('vertex_index', cv)
    _h(h, cv)
    ls = np.empty(npoly, np.int32)
    me.polygons.foreach_get('loop_start', ls)
    _h(h, ls)
    ed = np.empty(len(me.edges) * 2, np.int32)
    me.edges.foreach_get('vertices', ed)
    _h(h, ed)
    mi = np.empty(npoly, np.int32)
    me.polygons.foreach_get('material_index', mi)
    _h(h, mi)
    sm = np.empty(npoly, np.uint8)
    me.polygons.foreach_get('use_smooth', sm)
    _h(h, sm)
    # custom (split) normals, if any
    if me.has_custom_normals:
        cn = np.empty(nl * 3, np.float32)
        me.corner_normals.foreach_get('vector', cn)
        _h(h, cn)
    else:
        h.update(b'no-custom-normals')
    for uv in me.uv_layers:
        uvd = np.empty(nl * 2, np.float32)
        uv.data.foreach_get('uv', uvd)
        h.update(uv.name.encode())
        _h(h, uvd)
    for a in me.attributes:                    # sharp_edge / sharp_face / custom_normal (INT16_2D) / material_index ...
        if a.name.startswith('.') or a.name in ('position',):
            continue
        try:
            dt = a.data_type
            if dt in ('BOOLEAN',):
                arr = np.empty(len(a.data), np.uint8)
                a.data.foreach_get('value', arr)
            elif dt in ('INT',):
                arr = np.empty(len(a.data), np.int32)
                a.data.foreach_get('value', arr)
            elif dt in ('FLOAT',):
                arr = np.empty(len(a.data), np.float32)
                a.data.foreach_get('value', arr)
            elif dt == 'INT16_2D':
                arr = np.empty(len(a.data) * 2, np.int16)
                a.data.foreach_get('value', arr)
            elif dt == 'FLOAT2':
                arr = np.empty(len(a.data) * 2, np.float32)
                a.data.foreach_get('vector', arr)
            else:
                continue
            h.update(a.name.encode())
            _h(h, arr)
        except Exception as e:                  # pragma: no cover - attribute types we cannot read are skipped, but recorded
            h.update(('unreadable:' + a.name).encode())
    return h.hexdigest()


def world_exact_hash(obj):
    """SHA-256 of the raw float64 world-space vertex positions (no rounding): equal hashes = bit-identical world positions."""
    return hashlib.sha256(np.ascontiguousarray(mesh_co(obj, world=True)).tobytes()).hexdigest()


def world_hash(obj, decimals=7):
    return hashlib.sha256(np.ascontiguousarray(np.round(mesh_co(obj, world=True), decimals)).tobytes()).hexdigest()


def args_after_dashes():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def lin(c):
    return tuple(((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in c)


def mat_hash(m4):
    return [[round(float(x), 7) for x in row] for row in m4]
