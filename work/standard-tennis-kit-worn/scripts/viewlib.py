"""Shared preview/render helpers for the worn kit: body + staged npz parts with the 3-slot worn materials (0 fabric, 1 piping, 2 band).
All scenes are built in a fresh empty scene; the authority body is only READ (its geometry is copied into the scene)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
import render_setup as rs
from preview_common import material

SKIN = (0.80, 0.60, 0.46)
WHITE = (0.93, 0.93, 0.93)
BLACK = (0.035, 0.035, 0.04)
LIFT = {'male': 0.0285, 'female': 0.0235}


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def colorway_materials(cw):
    """(fabric, piping, band) preview stand-ins for the URP Lit materials.  white kit: white/white/BLACK band; black kit: black/white/WHITE band."""
    if cw == 'white':
        w = material('Std_White_Lit', WHITE, .62, .25)
        b = material('Std_Black_Lit', BLACK, .55, .25)
        return [w, w, b]
    b = material('Std_Black_Lit', BLACK, .55, .25)
    w = material('Std_White_Lit', WHITE, .62, .25)
    return [b, w, w]


def part_object(name, d, mats, tmp=None):
    """object from a staged npz dict (V, F, LN, M)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(d['V'], float).tolist(), [], np.asarray(d['F'], int).tolist())
    me.update()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set('material_index', np.minimum(np.asarray(d['M'], np.int32), len(mats) - 1))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    if 'LN' in d:
        try:
            me.normals_split_custom_set(np.asarray(d['LN'], float).reshape(-1, 3).tolist())
        except Exception as e:
            print('custom normals failed', name, e)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def body_object(gender, skin=SKIN):
    """copy of the authority body geometry (the blend is only read)."""
    blend, obj = (MALE_BLEND, 'Body_M') if gender == 'male' else (FEMALE_BLEND, 'Body_F')
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.objects = [obj]
    o = dst.objects[0]
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.clear()
    o.data.materials.append(material('Body_skin', skin, .55, .3))
    o.name = 'Body'
    return o


def load_part(name):
    z = np.load(f'{WORK}/data/{name}.npz')
    return {k: z[k] for k in z.files}


def shot_set(prefix, views, target, dist=6.4, lens=105, res=(520, 760), samples=32):
    paths = []
    for nm, az, el in views:
        p = f'{prefix}_{nm}.png'
        rs.shot(p, target, az, el, dist=dist, lens=lens, res=res)
        paths.append(p)
    return paths


def contact_sheet(paths, out, cols=None, pad=0):
    from PIL import Image
    ims = [Image.open(p).convert('RGB') for p in paths]
    cols = cols or len(ims)
    rows = math.ceil(len(ims) / cols)
    w, h = ims[0].size
    sheet = Image.new('RGB', (cols * w, rows * h))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(out)
    return out
