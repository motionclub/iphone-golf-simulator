"""Build the male outfit/expression example scene from the AUTHORITY blend (never saved back to it).

    exec(open(<this file>).read())  in the live Blender, or  blender -b --python build_example.py
Creates ArtDir/hero/base_lock/preview/outfit_example/HeroBase_Male_OutfitExample.blend
"""
import sys, importlib, shutil, hashlib
from pathlib import Path
import numpy as np
import bpy

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = ROOT / 'work/male-outfit-preview'
AUTH = ROOT / 'ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend'
OUT = ROOT / 'ArtDir/hero/base_lock/preview/outfit_example'
PREVIEW = OUT / 'HeroBase_Male_OutfitExample.blend'
FBX_HAIR = ROOT / 'ArtDir/hero/base_lock/unity_import/Hair_Default_Male.fbx'
if str(W) not in sys.path:
    sys.path.insert(0, str(W))
import preview_common as pc, shader_zones as sz, face_build as fb, render_setup as rs, outfit as of, outfit_parts as op, scene_ops as so
for m in (pc, sz, fb, rs, of, op, so):
    importlib.reload(m)

HAIR_ANCHOR = (0.0, -0.045, 1.5795952782462055)      # attachment anchor (y shifted to the current head centre)
YC = -0.045


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(colorway='coral_court'):
    OUT.mkdir(parents=True, exist_ok=True)
    auth_sha = sha(AUTH)
    bpy.ops.wm.open_mainfile(filepath=str(AUTH))
    bpy.ops.wm.save_as_mainfile(filepath=str(PREVIEW))        # from here on we only ever touch the preview copy
    assert bpy.data.filepath == str(PREVIEW)
    body = bpy.data.objects['Body_M']
    ref = np.array([v.co[:] for v in body.data.vertices], np.float32)
    for o in bpy.data.objects:
        if o.type == 'EMPTY':
            o.hide_render = True
    # --- skin
    skin = pc.material('Skin', fb.SKIN, .62, .27, sss=.02)
    body.data.materials.clear()
    body.data.materials.append(skin)
    # --- face layers (one collection per expression)
    F = fb.Face(body)
    for ex in so.EXPRS:
        F.build(ex)
    # drop the blush discs (read as stickers)
    for ex in so.EXPRS:
        c = bpy.data.collections['Face_' + ex]
        for o in list(c.objects):
            if o.name.startswith('Blush'):
                me = o.data
                bpy.data.objects.remove(o, do_unlink=True)
                bpy.data.meshes.remove(me)
    # --- studio
    rs.setup()
    # --- outfit
    coll = pc.get_collection('Outfit_Example')
    pc.clear_collection(coll)
    B = of.Body(body)
    M = op.get_mats(colorway)
    shirt, _ = op.make_shirt(B, coll, M)
    op.make_emblem(coll, shirt, M)
    shorts, _ = op.make_shorts(B, coll, M)
    socks, _ = op.make_socks(B, coll, M)
    shoes, _ = op.make_shoes(B, coll, M)
    op.make_wristbands(B, coll, M)
    zmin = min(v.co.z for v in shoes.data.vertices)
    rs.set_floor_z(zmin - 0.0003)
    # --- hair: project default hair asset (hanging locks trimmed) + scalp cap with a soft fade into the skin
    hcoll = pc.get_collection('Hair_Example')
    pc.clear_collection(hcoll)
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=str(FBX_HAIR))
    imp = [bpy.data.objects[n] for n in set(bpy.data.objects.keys()) - before]
    hair = [o for o in imp if o.type == 'MESH'][0]
    for o in imp:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        hcoll.objects.link(o)
    hair.name = 'Hair_M'
    hair.location = HAIR_ANCHOR
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(hair.data)
    bm.verts.ensure_lookup_table()
    seen = set()
    kill = []
    Mw = hair.matrix_world
    for v in bm.verts:
        if v.index in seen:
            continue
        comp = []
        stack = [v]
        seen.add(v.index)
        while stack:
            a = stack.pop()
            comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        if len(comp) == 90 and min((Mw @ c.co).z for c in comp) < 1.60:
            kill.extend(comp)
    bmesh.ops.delete(bm, geom=list(set(kill)), context='VERTS')
    bm.to_mesh(hair.data)
    bm.free()
    hair.data.materials.clear()
    hair.data.materials.append(M['Hair'])
    for p in hair.data.polygons:
        p.use_smooth = True

    def hairline(P):
        phi = np.degrees(np.arctan2(np.abs(P[:, 0]), -(P[:, 1] - YC)))
        return 1.640 - 0.012 * of.sm01(35, 85, phi) - 0.075 * of.sm01(100, 160, phi)

    capmat = sz.build_material('Outfit_HairCap', '#241810', [
        ('fade', '#7A5340', lambda Z: Z.inv(Z.up(Z.z, 1.574, 0.040))),
    ], rough=.58, spec=.3)
    cap, _ = of.build_shell(B, 'HairCap',
                            lambda V: (V[:, 2] >= hairline(V)) & (V[:, 2] > 1.50) & (np.abs(V[:, 0]) < 0.125),
                            lambda P0, idx: 0.0050 + 0.0030 * of.sm01(1.62, 1.70, P0[:, 2]), None, [capmat], hcoll,
                            snaps=[of.func_snap(lambda P: P[:, 2] < hairline(P) + 0.035, lambda P: hairline(P))],
                            thickness=0.0035, min_gap=0.0045, smooth_iters=12)
    so.show_expression('happy')
    # body untouched?
    now = np.array([v.co[:] for v in body.data.vertices], np.float32)
    assert np.array_equal(now, ref), 'Body_M coordinates changed'
    assert sha(AUTH) == auth_sha, 'authority blend changed'
    op.recolor(colorway)
    sz.set_colors('Outfit_HairCap', {'base': op.COLORWAYS[colorway]['Hair']['base']})
    return dict(body_verts=len(ref), auth_sha=auth_sha, zmin=zmin, objects=[o.name for o in coll.objects] + [o.name for o in hcoll.objects])


if __name__ == '__main__' or True:
    RESULT = build()
