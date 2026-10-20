"""Quick preview scenes (body + garments) and shared material helpers."""
import sys, math
import numpy as np
import bpy
from kitlib import *
import render_setup as rs
from preview_common import material, lin

SKIN = (0.80, 0.60, 0.46)


def fresh_scene():
    _MATS.clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def add_mesh(name, V, F, mat=None, smooth=True, mats=None, face_mat=None):
    o = make_object(name, V, F, smooth=smooth)
    if mats:
        for m in mats:
            o.data.materials.append(m)
        if face_mat is not None:
            o.data.polygons.foreach_set('material_index', np.asarray(face_mat, np.int32))
    elif mat is not None:
        o.data.materials.append(mat)
    return o


def preview(body, garments, out_prefix, views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), res=(520, 760),
            target=(0, -0.05, 0.86), dist=6.4, lens=105, samples=32, body_color=SKIN, hide_body=False, bg=None):
    """body: (V,F) or None; garments: list of (name, V, F, rgb) ; renders views to out_prefix_<view>.png"""
    fresh_scene()
    if body is not None and not hide_body:
        add_mesh('Body', body[0], body[1], material('Body_skin', body_color, .55, .3))
    for name, V, F, rgb in garments:
        add_mesh(name, V, F, material('M_' + name, rgb, .62, .25))
    rs.setup(samples=samples)
    paths = []
    for nm, az, el in views:
        p = f'{out_prefix}_{nm}.png'
        rs.shot(p, target, az, el, dist=dist, lens=lens, res=res)
        paths.append(p)
    return paths


WHITE = (0.93, 0.93, 0.93)
BLACK = (0.035, 0.035, 0.04)
PIPE = (0.93, 0.93, 0.93)


_MATS = {}


def kit_materials(colorway):
    """returns (main, piping) preview materials (Principled stand-ins for URP Lit); cached per scene."""
    key = colorway
    m = _MATS.get(key)
    if m is not None:
        try:
            if m[0].name and m[1].name and m[0].name in bpy.data.materials:
                return m
        except Exception:
            pass
    if colorway == 'white':
        w = material('Std_White_Lit', WHITE, .62, .25)
        res = (w, w)
    else:
        res = (material('Std_Black_Lit', BLACK, .55, .25), material('Std_White_Lit', PIPE, .55, .25))
    _MATS[key] = res
    return res


def add_garment(name, V, F, N, M, colorway='white', collection=None):
    """mesh object with custom normals + 2 material slots (0 main, 1 piping)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(np.asarray(V, float).tolist(), [], np.asarray(F, int).tolist())
    me.update()
    o = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    main, pipe = kit_materials(colorway)
    me.materials.append(main)
    me.materials.append(pipe)
    me.polygons.foreach_set('material_index', np.asarray(M, np.int32))
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    try:
        me.normals_split_custom_set_from_vertices(np.asarray(N, float).tolist())
    except Exception as e:
        print('custom normals failed', e)
    return o


def preview_garments(body, garments, out_prefix, colorway='white', views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)),
                     res=(520, 760), target=(0, -0.05, 0.86), dist=6.4, lens=105, samples=32, body_color=SKIN, lift=0.0):
    """garments: list of (name, V, F, N, M); lift raises the whole character (shoes with a sole thickness stand on the floor)."""
    fresh_scene()
    off = np.array([0, 0, lift])
    if body is not None:
        add_mesh('Body', body[0] + off, body[1], material('Body_skin', body_color, .55, .3))
    for name, V, F, N, M in garments:
        add_garment(name, V + off, F, N, M, colorway)
    target = (target[0], target[1], target[2] + lift)
    rs.setup(samples=samples)
    paths = []
    for nm, az, el in views:
        p = f'{out_prefix}_{nm}.png'
        rs.shot(p, target, az, el, dist=dist, lens=lens, res=res)
        paths.append(p)
    return paths
