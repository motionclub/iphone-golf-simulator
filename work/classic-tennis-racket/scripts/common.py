"""Shared helpers for the Classic racket work (runs inside Blender, headless).
Everything that touches a hero blend goes through load_body_copy(): a read-only library load into a
local copy, so the authority blends are never opened as main file and never saved."""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix, Quaternion

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
WORK = ROOT / 'work' / 'classic-tennis-racket'
HERO = ROOT / 'ArtDir' / 'hero' / 'base_lock' / 'blender'
BODIES = {
    'male': dict(blend=HERO / 'HeroBase_Male_Silhouette.blend', body='Body_M',
                 sha='fd04bc286f688b03ea25fbb57e1242bf2f5976c2dc7bbcdfdb0f68b622ab2347'),
    'female': dict(blend=HERO / 'HeroBase_Female.blend', body='Body_F',
                   sha='200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd'),
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def lin(c):
    return tuple(((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in c)


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mesh_co(obj, world=False):
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    if world:
        M = np.array(obj.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
    return co


def mesh_tris(obj):
    """Triangulated index array (n,3) of the polygon mesh (fan triangulation, fine for convex quads/ngons)."""
    me = obj.data
    me.calc_loop_triangles()
    t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get('vertices', t)
    return t.reshape(-1, 3)


def load_body_copy(tag, scene=None):
    """Returns the Body object of the locked blend, copied into the current (empty) file. Hero file untouched."""
    info = BODIES[tag]
    with bpy.data.libraries.load(str(info['blend']), link=False) as (src, dst):
        dst.objects = [info['body']]
    o = dst.objects[0]
    (scene or bpy.context.scene).collection.objects.link(o)
    return o


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    return sc


def args_after_dashes():
    return sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
