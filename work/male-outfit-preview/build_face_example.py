"""Preview: sculpted facial structure + random hairstyle (+ the example outfit) on a COPY of the male lock."""
import sys, importlib, hashlib, json, random
from pathlib import Path
import numpy as np
import bpy

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = ROOT / 'work/male-outfit-preview'
AUTH = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend'
OUT = ROOT / 'ArtDir/hero/base_lock/preview/face_example'
PREVIEW = OUT / 'HeroBase_Male_FaceExample.blend'
if str(W) not in sys.path:
    sys.path.insert(0, str(W))
import preview_common as pc, shader_zones as sz, face_build as fb, render_setup as rs, outfit as of, outfit_parts as op, scene_ops as so, face_sculpt as fs, hair_gen as hg
for m in (pc, sz, fb, rs, of, op, so, fs, hg):
    importlib.reload(m)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(colorway='coral_court', seed=None, outfit=True, sculpt_params=None):
    OUT.mkdir(parents=True, exist_ok=True)
    auth_sha = sha(AUTH)
    bpy.ops.wm.open_mainfile(filepath=str(AUTH))
    bpy.ops.wm.save_as_mainfile(filepath=str(PREVIEW))
    body = bpy.data.objects['Body_M']
    for o in bpy.data.objects:
        if o.type == 'EMPTY':
            o.hide_render = True
    n_head = fs.sculpt(body, dict(fs.PR, **(sculpt_params or {})))
    skin = pc.material('Skin', fb.SKIN, .62, .27, sss=.02)
    body.data.materials.clear(); body.data.materials.append(skin)
    F = fb.Face(body)
    for ex in so.EXPRS:
        c = F.build(ex)
        for o in list(c.objects):
            if o.name.startswith('Blush'):
                me = o.data; bpy.data.objects.remove(o, do_unlink=True); bpy.data.meshes.remove(me)
    rs.setup()
    B = of.Body(body)
    M = op.get_mats(colorway)
    coll = pc.get_collection('Outfit_Example'); pc.clear_collection(coll)
    zmin = 0.0
    if outfit:
        shirt, _ = op.make_shirt(B, coll, M); op.make_emblem(coll, shirt, M)
        op.make_shorts(B, coll, M); op.make_socks(B, coll, M)
        shoes, _ = op.make_shoes(B, coll, M); op.make_wristbands(B, coll, M)
        zmin = min(v.co.z for v in shoes.data.vertices)
    rs.set_floor_z(zmin - 0.0003)
    hcoll = pc.get_collection('Hair_Example'); pc.clear_collection(hcoll)
    hair = hg.random_hair(B, hcoll, seed=seed)
    so.show_expression('happy')
    assert sha(AUTH) == auth_sha
    bpy.ops.wm.save_as_mainfile(filepath=str(PREVIEW))
    return dict(head_verts_sculpted=n_head, hair=hair, auth_sha=auth_sha, file=str(PREVIEW))
