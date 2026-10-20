"""Blender-side helpers: load baseline, apply coords, clay renders. Run inside Blender (-b --python)."""
import bpy, numpy as np, math, json, sys
from mathutils import Vector
from pathlib import Path
W = Path(__file__).resolve().parent
BASE = W/'baseline/HeroBase_Male_Silhouette.blend'

def load(coords=None, blend=None):
    bpy.ops.wm.open_mainfile(filepath=str(blend or BASE))
    o = bpy.data.objects['Body_M']; me = o.data
    if coords is not None:
        co = np.load(coords) if isinstance(coords,(str,Path)) else coords
        assert len(co)==len(me.vertices)
        me.vertices.foreach_set('co', co.astype(np.float32).ravel()); me.update()
    return o

def clay_setup(cavity=True):
    s = bpy.context.scene
    s.render.engine = 'BLENDER_WORKBENCH'
    sh = s.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.62,0.62,0.62)
    try:
        sh.show_cavity = cavity; sh.cavity_type='BOTH'; sh.cavity_ridge_factor=0.6; sh.cavity_valley_factor=0.9
    except Exception as ex: print('cavity?',ex)
    s.render.film_transparent = False
    s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
    try: s.view_settings.view_transform = 'Standard'
    except Exception: pass
    s.world = s.world or bpy.data.worlds.new('w')
    s.world.color = (0.14,0.14,0.15)
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name!='Body_M': o.hide_render=True

_cam = None
def camera():
    global _cam
    if _cam is None:
        src = bpy.data.objects['Locked_bald_front']
        d = src.data.copy(); d.background_images.clear(); d.type='ORTHO'
        _cam = bpy.data.objects.new('Tmp_cam', d); bpy.context.scene.collection.objects.link(_cam)
    return _cam

def shot(path, target, az=0, el=0, scale=0.5, res=(900,900), dist=6.0, roll=0):
    """az: 0=front (camera at -Y looking +Y), 90 = camera at +X looking -X (left side of figure's... see notes)."""
    s = bpy.context.scene; cam = camera(); s.camera = cam
    a = math.radians(az); e = math.radians(el); t = Vector(target)
    cam.location = t + Vector((math.sin(a)*math.cos(e), -math.cos(a)*math.cos(e), math.sin(e)))*dist
    cam.rotation_euler = (t-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale = scale; cam.data.clip_end = 50
    s.render.resolution_x, s.render.resolution_y = res
    s.render.filepath = str(Path(path).resolve()); bpy.ops.render.render(write_still=True)


# ---------- plate-aligned head panels (same framing as male_head_detail.jpg panels) ----------
K_PLATE = 0.0013043874429196725
def head_panels(pre, views=('front','left','q3R','q3L')):
    k = K_PLATE
    zc = 1.7046599388122559 - ((66+352)/2 - 76)*k
    ycl = 0.065 + ((440+834)/2 - 712)*k
    W1, H1, Wl = 410, 286, 394
    if 'front' in views: shot(f'{pre}_front.png', (0,-0.04,zc), 0, 0, W1*k, (W1*3, H1*3))
    if 'left'  in views: shot(f'{pre}_left.png',  (0,ycl,zc), 90, 0, Wl*k, (Wl*3, H1*3))
    if 'q3R'   in views: shot(f'{pre}_q3R.png',   (0,-0.03,zc), -38, 0, Wl*k, (Wl*3, H1*3))
    if 'q3L'   in views: shot(f'{pre}_q3L.png',   (0,-0.03,zc), 38, 0, W1*k, (W1*3, H1*3))


def locked_render(cam_name, path, res=(1280, 720)):
    """Clay RGB render through one of the Locked_* cameras (same framing as the plates)."""
    s = bpy.context.scene
    clay_setup()
    s.render.film_transparent = False
    s.camera = bpy.data.objects[cam_name]
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.filepath = str(Path(path).resolve())
    bpy.ops.render.render(write_still=True)
