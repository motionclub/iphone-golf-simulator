"""Shared helpers for the outfit/face preview (runs inside Blender, live or headless)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

S = 1.7 / 593        # metres per plate pixel (plate calibration used by every HeroBase script)


def lin(c):
    return tuple(((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in c)


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def material(name, rgb, rough=.62, spec=.27, sheen=0.0, sss=0.0, replace=True):
    """Principled material from an sRGB colour (0..1 triple or hex string)."""
    if isinstance(rgb, str):
        rgb = hex_rgb(rgb)
    old = bpy.data.materials.get(name)
    if old is not None and replace:
        bpy.data.materials.remove(old)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*lin(rgb), 1)
    n = m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value = m.diffuse_color
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = 0
    for k in ('Specular IOR Level',):
        if k in n.inputs:
            n.inputs[k].default_value = spec
    if sheen and 'Sheen Weight' in n.inputs:
        n.inputs['Sheen Weight'].default_value = sheen
    if sss and 'Subsurface Weight' in n.inputs:
        n.inputs['Subsurface Weight'].default_value = sss
        n.inputs['Subsurface Radius'].default_value = (.012, .006, .003)
    return m


def body_bvh(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


def make_mesh_obj(name, verts, faces, mat, collection, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    collection.objects.link(o)
    if mat is not None:
        me.materials.append(mat)
    b = bmesh.new()
    b.from_mesh(me)
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    b.to_mesh(me)
    b.free()
    for f in me.polygons:
        f.use_smooth = smooth
    return o


def get_collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def clear_collection(c):
    for o in list(c.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and getattr(me, 'users', 1) == 0:
            if isinstance(me, bpy.types.Mesh):
                bpy.data.meshes.remove(me)
