"""Render camera-space normal maps (float EXR, RGB = n in camera space: x right, y up, z toward camera; A = coverage) of Body_M
at the plate-aligned views.  blender -b --factory-startup --python normals_render.py -- <blend> <outdir> [views comma list] [res_up]
Views: front,left,right,q3L,q3R  (same framing as render_panels.py: 2 px per plate px)"""
import sys, math
from pathlib import Path
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, h1render as HR
argv = sys.argv[sys.argv.index('--') + 1:]
blend = Path(argv[0]); out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
views = argv[2].split(',') if len(argv) > 2 else ['front', 'left', 'right', 'q3L', 'q3R']
up = int(argv[3]) if len(argv) > 3 else 2
bpy.ops.wm.open_mainfile(filepath=str(blend))
for o in bpy.data.objects:
    if o.type == 'EMPTY': o.hide_render = True
body = bpy.data.objects['Body_M']
face = bpy.data.objects.get('Face_M')
if face: face.hide_render = True            # skin form only


def nrm_material():
    m = bpy.data.materials.new('nrm_cam'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    vt = nt.nodes.new('ShaderNodeVectorTransform'); vt.vector_type = 'NORMAL'; vt.convert_from = 'WORLD'; vt.convert_to = 'CAMERA'
    nt.links.new(geo.outputs['Normal'], vt.inputs['Vector'])
    em = nt.nodes.new('ShaderNodeEmission'); out_ = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(vt.outputs['Vector'], em.inputs['Color'])      # raw (can be negative) -> clamp issue; handled below
    nt.links.new(em.outputs['Emission'], out_.inputs['Surface'])
    return m, nt, vt, em


# encode n*0.5+0.5 so negatives survive
m, nt, vt, em = nrm_material()
mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY_ADD'
mul.inputs[1].default_value = (0.5, 0.5, 0.5); mul.inputs[2].default_value = (0.5, 0.5, 0.5)
nt.links.new(vt.outputs['Vector'], mul.inputs[0]); nt.links.new(mul.outputs['Vector'], em.inputs['Color'])
body.data.materials.clear(); body.data.materials.append(m)

s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'
s.render.film_transparent = True
s.render.image_settings.file_format = 'OPEN_EXR'; s.render.image_settings.color_depth = '32'; s.render.image_settings.color_mode = 'RGBA'
s.view_settings.view_transform = 'Raw'; s.display_settings.display_device = 'sRGB'
try:
    s.eevee.taa_render_samples = 1
except Exception: pass
w_ = bpy.data.worlds.new('w_n'); s.world = w_; w_.use_nodes = True
w_.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
K = H.K
PAN = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
PUP_MID = {'q3L': 176.5, 'q3R': 589.5}
Q3_YAW = {'q3L': 41.0, 'q3R': 36.0}
cam = H.camera(); s.camera = cam
for name in views:
    if name == 'right':
        x0, y0, x1, y1 = 834, 62, 1271, 352
        w, h = x1 - x0, y1 - y0
        cyp = (y0 + y1) / 2; cxp = (x0 + x1) / 2
        tgt = (0.0, 0.065 - (1123.0 - cxp) * K, float(H.zrow(cyp))); az = 90; sc = w * K; res = (w * up, h * up)
    else:
        c = HR.cam_for(name, up)
        tgt, az, sc, res = c['target'], c['az'], c['scale'], c['res']
        if name in PUP_MID:
            x0_, y0_, x1_, y1_ = HR.SETS[name]['box']
            cxp = (x0_ + x1_) / 2; a_ = math.radians(Q3_YAW[name])
            ty = -0.1254 - ((PUP_MID[name] - cxp) * K) / math.sin(a_)
            tgt = (0.0, ty, c['target'][2]); az = Q3_YAW[name]
    # H.shot writes with the current engine format (png ext) -> set path ourselves
    from mathutils import Vector
    a = math.radians(az); t = Vector(tgt)
    cam.location = t + Vector((math.sin(a), -math.cos(a), 0.0)) * 3.0
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = sc
    s.render.resolution_x, s.render.resolution_y = res; s.render.resolution_percentage = 100
    s.render.filepath = str((out / f'{name}_nrm.exr').resolve())
    bpy.ops.render.render(write_still=True)
print('normals done', views)
