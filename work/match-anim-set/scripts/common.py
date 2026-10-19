"""Shared constants and helpers for the MATCH_ANIM_BUILD job (runs inside Blender 5.2 headless; numpy only exists in Blender's python).

The mesh geometry hash is the dressed-look job's definition, copied unchanged (see GATE_DEFS_preregistered.md)."""
import hashlib
import json
import math
import os
import sys

import numpy as np

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = os.environ.get('MA_WORK', REPO + '/work/match-anim-set')   # MA_WORK: build into a copy (FRAME_RATE_60 experiments) without touching the installed set
DATA = WORK + '/data'
EXPORT = WORK + '/export'
PROOF = WORK + '/proof'
SCRIPTS = WORK + '/scripts'

SRC = dict(
    male=REPO + '/work/male-pelvis-form3/export/merged_fd04bc28.blend',
    female=REPO + '/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend',
    racket=REPO + '/work/classic-tennis-racket/export/Racket_Classic.blend',
    socket_json=REPO + '/work/classic-tennis-racket/export/racket_classic_socket.json',
)
SHA = dict(
    male='d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781',
    female='a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1',
    racket='53e83714856a14c1533653b3fce3e164dfb17e9c58c995cbdb325d86eec7e8ba',
)
HERO = {
    'male': dict(label='Male', body='Body_M', face='Face_M', hair=None, rig='Rig_Male', blend=EXPORT + '/HeroBase_Male_MatchAnims.blend'),
    'female': dict(label='Female', body='Body_F', face='Face_F', hair='Hair_F', rig='Rig_Female', blend=EXPORT + '/HeroBase_Female_MatchAnims.blend'),
}
FPS = int(os.environ.get('MA_FPS', 30))   # MA_FPS=60: solve and bake on a 60 Hz grid (default 30 = the installed set)
CLIPS = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter', 'Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort',
         'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
CAPS = dict(ReadyIdle=2.4, SplitToForehand=0.6, SplitToBackhand=0.6, RecoverCenter=0.8, Forehand=1.2, ForehandOpen=1.0, ForehandWide=1.3,
            ForehandShort=1.0, Backhand=1.2, BackhandWide=1.3, SliceApproach=1.2, Serve=1.6, Return=0.9, VolleyForehand=0.7, VolleyBackhand=0.7,
            Overhead=1.2)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def args_after_dashes():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


# --------------------------------------------------------------------------- mesh hashing (dressed-look definition, unchanged)
def _h(h, arr):
    a = np.ascontiguousarray(arr)
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes())


def mesh_geometry_hash(me):
    """SHA-256 of the geometry of a mesh datablock: positions, topology, material indices, smooth flags, custom normals, UVs, attributes.
    Vertex-group weights, modifiers, parenting, selection/hide flags and object transforms are NOT part of it."""
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
    for a in me.attributes:
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
        except Exception:
            h.update(('unreadable:' + a.name).encode())
    return h.hexdigest()


def original_vgroups_hash(obj, names):
    """SHA-256 over the vertex groups that existed in the source (names + per-vertex weights)."""
    h = hashlib.sha256()
    idx = {vg.index: vg.name for vg in obj.vertex_groups}
    rows = []
    for v in obj.data.vertices:
        for g in v.groups:
            nm = idx.get(g.group)
            if nm in names:
                rows.append((v.index, nm, round(float(g.weight), 7)))
    rows.sort()
    h.update(json.dumps([sorted(names)]).encode())
    h.update(json.dumps(rows).encode())
    return h.hexdigest()


def mesh_co(obj, world=False):
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3).astype(np.float64)
    if world:
        M = np.array(obj.matrix_world, np.float64)
        co = co @ M[:3, :3].T + M[:3, 3]
    return co
