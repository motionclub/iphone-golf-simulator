"""Shared constants and helpers for DRESS_MATCH_HEROES (Blender 5.2 headless; numpy only exists in Blender's python)."""
import hashlib
import json
import math
import os
import sys

import numpy as np

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/hero-dressed'
DATA = WORK + '/data'
EXPORT = WORK + '/export'
PROOF = WORK + '/proof'
LOGS = WORK + '/logs'
ANIM = REPO + '/work/match-anim-set'
KITDIR = REPO + '/work/tennis-shoes-fit/export'
CLIP_TABLE = REPO + '/work/hero-mainstay/data/clip_table.json'

HERO = {
    'male': dict(label='Male', body='Body_M', face='Face_M', rig='Rig_Male', anim=ANIM + '/export/HeroBase_Male_MatchAnims.blend',
                 kit=KITDIR + '/StandardKit_Male.blend', dressed=EXPORT + '/HeroBase_Male_Dressed.blend', fbx=EXPORT + '/Male_Kit.fbx',
                 pieces=dict(Top='Kit_Top_Polo_M_White', Bottom='Kit_Bottom_Shorts_M_White', Sock_L='Kit_Sock_R_White', Sock_R='Kit_Sock_L_White',
                             Shoe_L='Kit_Shoe_R_White', Shoe_R='Kit_Shoe_L_White')),
    'female': dict(label='Female', body='Body_F', face='Face_F', rig='Rig_Female', anim=ANIM + '/export/HeroBase_Female_MatchAnims.blend',
                   kit=KITDIR + '/StandardKit_Female.blend', dressed=EXPORT + '/HeroBase_Female_Dressed.blend', fbx=EXPORT + '/Female_Kit.fbx',
                   pieces=dict(Top='Kit_Top_Polo_F_White', Bottom='Kit_Bottom_Skort_F_White', Sock_L='Kit_Sock_R_White', Sock_R='Kit_Sock_L_White',
                               Shoe_L='Kit_Shoe_R_White', Shoe_R='Kit_Shoe_L_White')),
}
# piece names are the RIG's sides: *_L is on LeftLowerLeg / LeftFoot (x > 0 in Blender); the kit blend names its pieces by x sign, so Sock_L comes from 'Kit_Sock_R_White'
PIECES = ['Top', 'Bottom', 'Sock_L', 'Sock_R', 'Shoe_L', 'Shoe_R']
KIT_NAME = {p: 'Kit_' + p for p in PIECES}           # object / Unity renderer names
# per piece: kit-blend slot index -> role material name (slots merged at export so every role is one material / one submesh)
ROLE_SLOTS = {
    'Top': {0: 'Kit_Shirt', 1: 'Kit_ShirtTrim'},
    'Bottom': {0: 'Kit_Shorts', 1: 'Kit_Shorts', 2: 'Kit_ShortsBand'},
    'Sock_L': {0: 'Kit_Sock', 1: 'Kit_Sock'}, 'Sock_R': {0: 'Kit_Sock', 1: 'Kit_Sock'},
    'Shoe_L': {0: 'Kit_Shoe', 1: 'Kit_Sole'}, 'Shoe_R': {0: 'Kit_Shoe', 1: 'Kit_Sole'},
}
# authored linear base colours (Std_White_Lit / Std_Black_Lit) per role in the WHITE kit
ROLE_SOURCE = {'Kit_Shirt': 'Std_White_Lit', 'Kit_ShirtTrim': 'Std_White_Lit', 'Kit_Shorts': 'Std_White_Lit', 'Kit_ShortsBand': 'Std_Black_Lit',
               'Kit_Shoe': 'Std_White_Lit', 'Kit_Sole': 'Std_White_Lit', 'Kit_Sock': 'Std_White_Lit'}
FPS = 30
CLIPS = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter', 'Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort',
         'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
GATE_POSES = [('ReadyIdle', 'start'), ('Forehand', 'contact'), ('Backhand', 'contact'), ('Serve', 'contact'), ('Overhead', 'contact'),
              ('ForehandWide', 'contact'), ('VolleyForehand', 'contact'), ('Return', 'contact')]


def args_after_dashes():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def contact_seconds(label):
    d = json.load(open(CLIP_TABLE))
    row = [h for h in d['heroes'] if h['sex'] == label][0]
    return {c['name']: float(c['contact']) for c in row['clips']}, {c['name']: float(c['length']) for c in row['clips']}


def pose_frame(clip, kind, contacts):
    """Blender frame of a gate pose: clip frames start at 0 (30 fps)."""
    return 0 if kind == 'start' else int(round(contacts[clip] * FPS))


def mesh_co(obj):
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    return co.reshape(-1, 3).astype(np.float64)


def mesh_tris(me):
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    t = np.empty(n * 3, np.int32)
    me.loop_triangles.foreach_get('vertices', t)
    return t.reshape(-1, 3)


def tri_material(me):
    n = len(me.loop_triangles)
    m = np.empty(n, np.int32)
    me.loop_triangles.foreach_get('material_index', m)
    return m


def bone_weight_matrix(obj, bone_names):
    """(nV, nB) dense weights of the vertex groups named like the bones."""
    idx = {vg.index: bone_names.index(vg.name) for vg in obj.vertex_groups if vg.name in bone_names}
    W = np.zeros((len(obj.data.vertices), len(bone_names)), np.float64)
    for v in obj.data.vertices:
        for g in v.groups:
            j = idx.get(g.group)
            if j is not None:
                W[v.index, j] += g.weight
    return W


def activate_clip(rig, name):
    import bpy
    act = bpy.data.actions[name]
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    return act


def evaluated_co(obj, depsgraph):
    """World-space evaluated vertex positions (armature modifier applied) as (n,3) float64."""
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3).astype(np.float64)
    M = np.array(ev.matrix_world, np.float64)
    return co @ M[:3, :3].T + M[:3, 3]
