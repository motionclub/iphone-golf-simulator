"""Quick / proof renders of the dressed hero (EEVEE, Blender headless).

  blender -b export/HeroBase_<Hero>_Dressed.blend --python rview.py -- <male|female> <spec.json>

spec.json = {"shots": [{"clip":"Forehand","frame":20,"out":"/path.png","target":[x,y,z],"dist":3.0,"az":30,"el":10,"res":[540,675],
             "kit":true,"body":true,"clip_plane":null,"cutaway":false,"colors":{"Kit_Shirt":[r,g,b]}, "lens":50}], "court": false}
Azimuth is measured from the hero's FRONT (front = -Y in Blender): az 0 = camera in front, 90 = camera on the hero's left (x>0), 180 = behind.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector

from dcommon import *

a_ = args_after_dashes()
tag = a_[0]
spec = json.load(open(a_[1]))
H = HERO[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
for accessory in [bpy.data.objects.get('Hair_F')]:
    if accessory:
        accessory.hide_viewport=False;accessory.hide_set(False)
bpy.context.view_layer.update()


def lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def setup(court):
    for o in bpy.data.objects:
        if o.type in ('CAMERA', 'LIGHT'):
            o.hide_render = True
    sc.render.engine = 'BLENDER_EEVEE'
    try:
        sc.eevee.taa_render_samples = 24
        sc.eevee.use_shadows = True
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    sc.view_settings.view_transform = 'AgX'
    w = bpy.data.worlds.new('R_World')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*lin((0.52, 0.58, 0.66)), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    # floor
    me = bpy.data.meshes.new('R_Floor')
    r = 12.0
    me.from_pydata([(-r, -r, -0.0005), (r, -r, -0.0005), (r, r, -0.0005), (-r, r, -0.0005)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new('R_Floor', me)
    sc.collection.objects.link(fo)
    m = bpy.data.materials.new('R_FloorMat')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin((0.16, 0.34, 0.50)), 1)
    b.inputs['Roughness'].default_value = 0.85
    me.materials.append(m)

    def area(name, loc, power, size, target=(0, 0, 0.9)):
        d = bpy.data.lights.new(name, 'AREA')
        d.shape = 'DISK'
        d.energy = power
        d.size = size
        o = bpy.data.objects.new(name, d)
        sc.collection.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o
    # lights are placed around the hero in hero-front space; the key from camera-left-ish above, fill from the right, rim from behind
    area('R_Key', (-2.6, -3.4, 3.8), 900, 3.4)
    area('R_Fill', (3.2, -2.6, 2.0), 380, 3.6)
    area('R_Rim', (0.6, 3.2, 3.2), 560, 2.4)
    area('R_Top', (0.0, 0.0, 4.8), 240, 3.0)
    cd = bpy.data.cameras.new('R_Cam')
    cam = bpy.data.objects.new('R_Cam', cd)
    sc.collection.objects.link(cam)
    cd.clip_start, cd.clip_end = 0.05, 100
    sc.camera = cam
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False
    return cam, cd


# Diagnostic: match Unity's back-face culling and render-facing trouser LOD.
import bmesh
pants=bpy.data.objects.get('Golf_Trousers')
if pants:
 n=len(pants.data.vertices)//2
 bm=bmesh.new();bm.from_mesh(pants.data);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if all(v.index>=n for v in f.verts)],context='FACES')
 bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='BEAUTY',ngon_method='BEAUTY');bm.to_mesh(pants.data);bm.free()
for m in bpy.data.materials:
 if m.name.startswith('Golf_'):m.use_backface_culling=True
cam, cd = setup(spec.get('court', False))
kit_names = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Golf_')]
colors = {}
for sh in spec['shots']:
    if sh.get('clip'):
        activate_clip(rig, sh['clip'])
        sc.frame_set(-1);sc.frame_set(int(sh.get('frame', 0)))
    else:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.location = (0, 0, 0)
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)
        sc.frame_set(0)
    bpy.context.view_layer.update()
    # The same exported garment correctives are driven by joint directions in
    # Unity. Proof selects them by their measured anchor features, not clip name.
    correctables=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_') and o.get('GolfCorrectiveProfile') and o.data.shape_keys]
    for polo in correctables:
        import numpy as np
        profile = json.loads(polo['GolfCorrectiveProfile'])
        dirs = np.array([np.array(rig.pose.bones[b].head)-np.array(rig.pose.bones[a].head) for a,b in profile['segments']])
        dirs /= np.maximum(np.linalg.norm(dirs,axis=1)[:,None],1e-10)
        features = np.array([dirs[i]@dirs[j] for i in range(8) for j in range(i+1,8)])
        distances = np.array([np.mean((features-np.array(a['feature']))**2) for a in profile['anchors']])
        weights = np.maximum(distances,1e-10)**-2; weights /= weights.sum()
        for k,a in enumerate(profile['anchors'][1:],1):polo.data.shape_keys.key_blocks[a['shape']].value=float(weights[k])
        bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.name in kit_names:
            only = sh.get('only')
            hidden_glove = 'Golf_Glove_Left' if sh.get('handedness') == 'LH' else 'Golf_Glove_Right'
            o.hide_render = not sh.get('kit', True) or (only is not None and o.name not in only) or o.name == hidden_glove
        if o.name in (H['body'], H['face']):
            o.hide_render = not sh.get('body', True)
        if o.name.startswith('Kit_') or o.name in ('Racket_Classic', 'Grip', 'ButtCap', 'StringBed'):
            o.hide_render = True
    # colour overrides (linear sRGB -> BSDF base colour) for the roles
    for role, rgb in (sh.get('colors') or {}).items():
        m = bpy.data.materials.get(role)
        if m:
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*lin(rgb), 1)
    if sh.get('body_rgb'):
        for o in bpy.data.objects:
            if o.name == H['body']:
                for ms in o.data.materials:
                    if ms and ms.use_nodes:
                        ms.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*lin(sh['body_rgb']), 1)
    tx, ty, tz = sh.get('target', [0, 0, 0.9])
    if sh.get('body_vertex') is not None:
        dgv = bpy.context.evaluated_depsgraph_get()
        pv = evaluated_co(bpy.data.objects[H['body']], dgv)[int(sh['body_vertex'])]
        tx, ty, tz = float(pv[0]), float(pv[1]), float(pv[2])
    elif sh.get('follow'):
        bpos = rig.matrix_world @ rig.pose.bones[sh['follow']].head
        off = sh.get('offset', [0, 0, 0])
        tx, ty, tz = bpos.x + off[0], bpos.y + off[1], bpos.z + off[2]
    el = math.radians(sh.get('el', 8))
    az = math.radians(sh.get('az', 30))
    d = sh.get('dist', 4.0)
    # front = -Y; az measured toward +x (the hero's left)
    cam.location = (tx + d * math.cos(el) * math.sin(az), ty - d * math.cos(el) * math.cos(az), tz + d * math.sin(el))
    cam.rotation_euler = (Vector((tx, ty, tz)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = sh.get('lens', 50)
    cd.sensor_width = 36
    res = sh.get('res', [540, 675])
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.filepath = sh['out']
    os.makedirs(os.path.dirname(sh['out']), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print('RENDER', sh['out'])
