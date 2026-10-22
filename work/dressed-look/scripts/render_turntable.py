"""White-kit turntable of one dressed hero, camera behind the court, written straight to H.264 MP4 by Blender (no external ffmpeg).

  blender -b export/HeroBase_<Sex>_Dressed.blend --python render_turntable.py -- <male|female> <out.mp4> [--frames N] [--res S] [--samples N] [--test]

The character turns 360 degrees about the vertical axis on a pivot (a runtime empty, never saved); the camera and the lights stay where a
broadcast camera behind the baseline would be, looking towards the net over the player's shoulder.  Starts with the player's back to the
camera and turns so the racket hand (character right = world -X) comes round first, then the front.  The dressed blend is not saved."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
from preview_common import material, lin
from mathutils import Vector

a_ = args_after_dashes()
tag, out_mp4 = a_[0], a_[1]
opt = lambda k, d=None: (a_[a_.index(k) + 1] if k in a_ else d)
N = int(opt('--frames', 192))
RES_W = int(opt('--res', 1080))
RES_H = int(round(RES_W * 1.25))
SAMPLES = int(opt('--samples', 32))
TEST = '--test' in a_
H = HERO[tag]
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type in ('LIGHT', 'CAMERA'):
        o.hide_render = True
bpy.data.collections['Kit_Black'].hide_render = True
bpy.data.collections['Kit_Black'].hide_viewport = True
bpy.data.collections['Kit_White'].hide_render = False
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == 'Kit_Black':
        lc.hide_viewport = True
    if lc.name == 'Kit_White':
        lc.hide_viewport = False
sc.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects['Rig_Hand_R']
shoe_min = min(mesh_co(o, world=True)[:, 2].min() for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Kit_Shoe') and 'White' in o.name)

# ---- the turn: pivot at the origin; the rig is the root of the whole dressed character (body, face, sockets, kit, racket all hang below it)
piv = bpy.data.objects.new('Turntable_Pivot', None)
sc.collection.objects.link(piv)
rig.parent = piv
rig.parent_type = 'OBJECT'
rig.matrix_parent_inverse = Matrix.Identity(4)
piv.rotation_mode = 'XYZ'
sc.frame_start, sc.frame_end = 1, N
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'      # constant angular speed (new keyframes are linear)
piv.rotation_euler = (0, 0, 0)
piv.keyframe_insert('rotation_euler', frame=1)
piv.rotation_euler = (0, 0, -2 * math.pi)             # -Z: from the back, the racket hand (right side) comes round first
piv.keyframe_insert('rotation_euler', frame=N + 1)
piv.rotation_euler = (0, 0, 0)

# ---- court floor + lines (hard court blue inside the lines, green run-off), player standing on the baseline, net ahead (-Y)
def box(name, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    me.from_pydata(v, [], f)
    me.update()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    me.materials.append(mat)
    return o

z0 = shoe_min - 0.002
m_green = material('Court_Green', (0.10, 0.30, 0.22), .85, .05)
m_blue = material('Court_Blue', (0.13, 0.31, 0.52), .80, .08)
m_line = material('Court_Line', (0.92, 0.92, 0.90), .70, .05)
m_net = material('Net_Dark', (0.10, 0.11, 0.12), .9, .02)
m_tape = material('Net_Tape', (0.9, 0.9, 0.88), .6, .05)
m_wall = material('Backdrop_Green', (0.05, 0.18, 0.14), .95, .02)
_n = m_wall.node_tree.nodes['Principled BSDF']
_n.inputs['Emission Color'].default_value = (*lin((0.07, 0.24, 0.19)), 1)
_n.inputs['Emission Strength'].default_value = 1.0
box('Court_Runoff', -40, 40, -48, 22, z0 - 0.02, z0, m_green)
L, NET = 23.77, 11.885
bl_y = 0.0                                              # near baseline (the player's feet are on it), the net is ahead (-Y)
box('Court_Inside', -5.485 - 0.6, 5.485 + 0.6, bl_y - L - 0.6, bl_y + 0.6, z0, z0 + 0.002, m_blue)
lw = 0.05
def line(x0, x1, y0, y1):
    return box('Court_Line', x0, x1, y0, y1, z0 + 0.002, z0 + 0.004, m_line)
line(-5.485 - lw, 5.485 + lw, bl_y - lw, bl_y)                      # near baseline
line(-5.485 - lw, 5.485 + lw, bl_y - L, bl_y - L + lw)              # far baseline
for x in (-5.485, -4.115, 4.115, 5.485):
    line(x - lw / 2, x + lw / 2, bl_y - L, bl_y)                    # doubles / singles side lines
for yy in (bl_y - NET + 6.40, bl_y - NET - 6.40):
    line(-4.115, 4.115, yy - lw / 2, yy + lw / 2)                   # service lines
line(-lw / 2, lw / 2, bl_y - NET - 6.40, bl_y - NET + 6.40)         # centre service line
line(-lw / 2, lw / 2, bl_y - L, bl_y - L + 0.30)                    # far centre mark (the near one would sit between the player's feet)
box('Net_Band', -6.4, 6.4, bl_y - NET - 0.02, bl_y - NET + 0.02, z0, z0 + 0.86, m_net)
box('Net_Tape', -6.4, 6.4, bl_y - NET - 0.03, bl_y - NET + 0.03, z0 + 0.86, z0 + 0.914, m_tape)
box('Backdrop_Screen', -30, 30, bl_y - L - 7.0, bl_y - L - 6.9, z0, z0 + 5.0, m_wall)

# ---- world + lights (static: a broadcast rig behind the baseline)
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = SAMPLES
    sc.eevee.use_shadows = True
    sc.eevee.use_raytracing = True
except Exception:
    pass
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'None'
w = bpy.data.worlds.get('TT_World') or bpy.data.worlds.new('TT_World')
sc.world = w
w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (*lin((0.36, 0.42, 0.50)), 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.8


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


area('TT_Key', (-3.2, 5.2, 4.2), 900, 3.4)
area('TT_Fill', (3.6, 4.6, 2.2), 380, 3.6)
area('TT_Rim', (0.8, -3.6, 3.8), 650, 2.4)
area('TT_Top', (0.0, 0.5, 5.0), 220, 3.0)
area('TT_Floor', (0.0, 3.5, 0.8), 160, 3.0)
sun = bpy.data.lights.new('TT_Sun', 'SUN')
sun.energy = 1.6
so = bpy.data.objects.new('TT_Sun', sun)
sc.collection.objects.link(so)
so.rotation_euler = (math.radians(58), 0, math.radians(180))      # from behind the camera, high: even daylight on the court and the screen

# ---- behind-the-court camera: behind and above the player, looking over the shoulder towards the net
cd = bpy.data.cameras.new('TT_Camera')
cam = bpy.data.objects.new('TT_Camera', cd)
sc.collection.objects.link(cam)
sc.camera = cam
cd.lens = 62
cd.sensor_width = 36
cd.clip_start, cd.clip_end = 0.05, 200
cam_loc = Vector((0.0, 4.35, 2.05))
tgt = Vector((0.0, -0.1, 0.92))
cam.location = cam_loc
cam.rotation_euler = (tgt - cam_loc).to_track_quat('-Z', 'Y').to_euler()
sc.render.resolution_x, sc.render.resolution_y = RES_W, RES_H
sc.render.resolution_percentage = 100
r = sc.render
r.image_settings.media_type = 'VIDEO'
r.image_settings.file_format = 'FFMPEG'
r.ffmpeg.format = 'MPEG4'
r.ffmpeg.codec = 'H264'
r.ffmpeg.constant_rate_factor = 'HIGH'
r.ffmpeg.ffmpeg_preset = 'GOOD'
r.ffmpeg.audio_codec = 'NONE'
r.fps = 24
if TEST:
    sc.frame_end = min(N, 6)
still = opt('--still')
if still is not None:                                 # single PNG of one frame (for checking the composition)
    r.image_settings.media_type = 'IMAGE'
    r.image_settings.file_format = 'PNG'
    sc.frame_set(int(still))
    r.filepath = out_mp4
    bpy.ops.render.render(write_still=True)
    print('STILL_DONE', out_mp4)
else:
    r.filepath = out_mp4
    bpy.ops.render.render(animation=True)
    print('TURNTABLE_DONE', tag, out_mp4, 'frames', sc.frame_end)
