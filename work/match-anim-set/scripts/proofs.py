"""Proof renders from the baked blends (Blender headless, EEVEE).

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python proofs.py -- <male|female> cells            # contact / finish stills: behind + side
  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python proofs.py -- <male|female> frames [clip..]  # every frame of the clips, behind-the-court camera
  blender -b --factory-startup --python proofs.py -- <male|female> encode                                  # PNG frames -> proof/Review_<Hero>.mp4 (Blender's own H.264)

Cells go to proof/_cells/, frames to proof/_frames/<hero>/.  Nothing here writes outside work/match-anim-set/."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Matrix, Vector

from common import *

a_ = args_after_dashes()
tag, mode = a_[0], a_[1]
H = HERO[tag]
sc = bpy.context.scene
CELLS = PROOF + '/_cells'
FRAMES = PROOF + f'/_frames/{tag}'
RES = (540, 675)


def lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def material(name, rgb, rough=0.8, spec=0.05):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*lin(rgb), 1)
    b.inputs['Roughness'].default_value = rough
    for k in ('Specular IOR Level', 'Specular'):
        if k in b.inputs:
            b.inputs[k].default_value = spec
            break
    return m


def build_set(samples=24):
    """court floor + lines + world + lights; camera behind the baseline looking at the net over the player's shoulder"""
    for o in bpy.data.objects:
        if o.type in ('CAMERA', 'LIGHT'):
            o.hide_render = True
        if o.type == 'EMPTY' and not o.name.startswith('Hand_Racket'):
            o.hide_render = True
    sc.render.engine = 'BLENDER_EEVEE'
    try:
        sc.eevee.taa_render_samples = samples
        sc.eevee.use_shadows = True
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'None'
    w = bpy.data.worlds.new('Proof_World')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*lin((0.36, 0.42, 0.50)), 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.8

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
    z0 = -0.002
    m_green = material('Court_Green', (0.10, 0.30, 0.22), .85, .05)
    m_blue = material('Court_Blue', (0.13, 0.31, 0.52), .80, .08)
    m_line = material('Court_Line', (0.92, 0.92, 0.90), .70, .05)
    m_net = material('Net_Dark', (0.10, 0.11, 0.12), .9, .02)
    m_tape = material('Net_Tape', (0.9, 0.9, 0.88), .6, .05)
    m_wall = material('Backdrop_Green', (0.05, 0.18, 0.14), .95, .02)
    n = m_wall.node_tree.nodes['Principled BSDF']
    n.inputs['Emission Color'].default_value = (*lin((0.07, 0.24, 0.19)), 1)
    n.inputs['Emission Strength'].default_value = 1.0
    box('Court_Runoff', -40, 40, -48, 22, z0 - 0.02, z0, m_green)
    L, NET = 23.77, 11.885
    bl_y = 0.0
    box('Court_Inside', -5.485 - 0.6, 5.485 + 0.6, bl_y - L - 0.6, bl_y + 0.6, z0, z0 + 0.002, m_blue)
    lw = 0.05

    def line(x0, x1, y0, y1):
        return box('Court_Line', x0, x1, y0, y1, z0 + 0.002, z0 + 0.004, m_line)
    line(-5.485 - lw, 5.485 + lw, bl_y - lw, bl_y)
    line(-5.485 - lw, 5.485 + lw, bl_y - L, bl_y - L + lw)
    for x in (-5.485, -4.115, 4.115, 5.485):
        line(x - lw / 2, x + lw / 2, bl_y - L, bl_y)
    for yy in (bl_y - NET + 6.40, bl_y - NET - 6.40):
        line(-4.115, 4.115, yy - lw / 2, yy + lw / 2)
    line(-lw / 2, lw / 2, bl_y - NET - 6.40, bl_y - NET + 6.40)
    box('Net_Band', -6.4, 6.4, bl_y - NET - 0.02, bl_y - NET + 0.02, z0, z0 + 0.86, m_net)
    box('Net_Tape', -6.4, 6.4, bl_y - NET - 0.03, bl_y - NET + 0.03, z0 + 0.86, z0 + 0.914, m_tape)
    box('Backdrop_Screen', -30, 30, bl_y - L - 7.0, bl_y - L - 6.9, z0, z0 + 5.0, m_wall)

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
    area('PF_Key', (-3.2, 5.2, 4.2), 900, 3.4)
    area('PF_Fill', (3.6, 4.6, 2.2), 380, 3.6)
    area('PF_Rim', (0.8, -3.6, 3.8), 650, 2.4)
    area('PF_Top', (0.0, 0.5, 5.0), 220, 3.0)
    area('PF_Floor', (0.0, 3.5, 0.8), 160, 3.0)
    sun = bpy.data.lights.new('PF_Sun', 'SUN')
    sun.energy = 1.6
    so = bpy.data.objects.new('PF_Sun', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(58), 0, math.radians(180))
    cd = bpy.data.cameras.new('PF_Cam')
    cam = bpy.data.objects.new('PF_Cam', cd)
    sc.collection.objects.link(cam)
    cd.lens = 46
    cd.sensor_width = 36
    cd.clip_start, cd.clip_end = 0.05, 200
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.image_settings.media_type = 'IMAGE'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.film_transparent = False
    return cam


VIEWS = dict(behind=((0.0, 4.6, 2.0), (0.0, -0.1, 1.15)),                  # broadcast camera behind the baseline, over the player's shoulder
             side=((-4.4, 0.35, 1.6), (0.0, -0.1, 1.15)))                   # from the racket-hand side of the court (character right = world -X)


def set_view(cam, view, root_xy=(0.0, 0.0)):
    loc, tgt = VIEWS[view]
    loc = Vector((loc[0] + root_xy[0] * (0 if view == 'behind' else 1), loc[1], loc[2]))
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - loc).to_track_quat('-Z', 'Y').to_euler()


def activate(clip):
    rig = bpy.data.objects[H['rig']]
    act = bpy.data.actions[clip]
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    return rig, act


def render_still(cam, view, path):
    set_view(cam, view)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


meta = json.load(open(f'{DATA}/bake_{tag}.json'))['clips']
A = np.load(f'{DATA}/anim_{tag}.npz')

if mode == 'cells':
    os.makedirs(CELLS, exist_ok=True)
    cam = build_set()
    out = {}
    FPSF = float(FPS)
    for clip in (a_[2:] or CLIPS):
        rig, act = activate(clip)
        nF = int(round(act.frame_end)) + 1
        c = meta[clip]
        if c['contact_s'] is not None:
            ci = int(round(c['contact_s'] * FPSF))
            sweet = A[clip + '/sweet']
            v = np.linalg.norm(np.diff(sweet, axis=0), axis=1) * FPSF
            ipk = int(v.argmax())
            vpk = float(v.max())
            run, runs, start = 0, [], None
            for k in range(ipk + 1, len(v)):
                if v[k] <= 0.12 * vpk:
                    if run == 0:
                        start = k
                    run += 1
                else:
                    if run:
                        runs.append((start, run))
                    run = 0
            if run:
                runs.append((start, run))
            fin = (runs[0][0] + runs[0][1] // 2) if runs else nF - 1
            cells = [('contact', ci), ('finish', min(fin, nF - 1))]
        else:
            cells = [('mid', nF // 2), ('end', nF - 1)]
        out[clip] = {}
        for lab, fr in cells:
            sc.frame_set(fr)
            bpy.context.view_layer.update()
            for view in ('behind', 'side'):
                p = f'{CELLS}/{tag}_{clip}_{lab}_{view}.png'
                render_still(cam, view, p)
            out[clip][lab] = fr
        print('CELLS', clip, out[clip])
    json.dump(out, open(f'{CELLS}/{tag}_cells.json', 'w'), indent=1)
    print('CELLS_DONE', tag)

elif mode == 'frames':
    names = a_[2:] or CLIPS
    os.makedirs(FRAMES, exist_ok=True)
    cam = build_set(samples=20)
    for clip in names:
        rig, act = activate(clip)
        nF = int(round(act.frame_end)) + 1
        for fr in range(nF):
            sc.frame_set(fr)
            bpy.context.view_layer.update()
            render_still(cam, 'behind', f'{FRAMES}/{clip}_{fr:03d}.png')
        print('FRAMES', clip, nF)
    print('FRAMES_DONE', tag)

elif mode == 'sideframes':
    # extra progress renders from the racket-hand side camera, written OUTSIDE the repo (a_[2] = output dir); not a deliverable
    outdir = a_[2]
    os.makedirs(outdir, exist_ok=True)
    cam = build_set(samples=20)
    for clip in CLIPS:
        rig, act = activate(clip)
        nF = int(round(act.frame_end)) + 1
        for fr in range(nF):
            sc.frame_set(fr)
            bpy.context.view_layer.update()
            render_still(cam, 'side', f'{outdir}/{clip}_{fr:03d}.png')
        print('SIDEFRAMES', clip, nF)
    print('SIDEFRAMES_DONE', tag)

elif mode == 'encode':
    # frames were annotated by annotate.py (Pillow lives outside Blender); Blender's own H.264 writer builds the mp4 from the image sequence
    ann_dir = PROOF + f'/_frames_annotated/{tag}'
    seq = sorted(os.path.join(ann_dir, f) for f in os.listdir(ann_dir) if f.endswith('.png'))
    out_mp4 = PROOF + f'/Review_{H["label"]}.mp4'
    scn = bpy.data.scenes.new('encode')
    bpy.context.window.scene = scn if bpy.context.window else bpy.context.scene
    scn = bpy.context.scene if not bpy.context.window else scn
    se = scn.sequence_editor_create() if scn.sequence_editor is None else scn.sequence_editor
    coll = se.strips if hasattr(se, 'strips') else se.sequences
    strip = coll.new_image('review', seq[0], channel=1, frame_start=1, fit_method='STRETCH')
    for p in seq[1:]:
        strip.elements.append(os.path.basename(p))
    r = scn.render
    r.resolution_x, r.resolution_y = RES[0], RES[1] - (RES[1] % 2)         # H.264 needs even sizes (675 -> 674, the strip is stretched by 0.15 %)
    r.resolution_percentage = 100
    r.fps = 30
    r.fps_base = 1.0
    scn.frame_start, scn.frame_end = 1, len(seq)
    r.use_sequencer = True
    r.image_settings.media_type = 'VIDEO'
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.constant_rate_factor = 'HIGH'
    r.ffmpeg.ffmpeg_preset = 'GOOD'
    r.ffmpeg.audio_codec = 'NONE'
    r.filepath = out_mp4
    bpy.ops.render.render(animation=True, scene=scn.name)
    print('ENCODE_DONE', tag, out_mp4, len(seq))
