"""Build the hero rig (armature) in the current Blender scene from a rig spec (scripts/lm.py output), and debug-visualise it."""
import math

import numpy as np
import bpy
import bmesh
from mathutils import Matrix, Vector

from common import *


def build_armature(spec, rig_name, collection=None):
    """create the armature object (identity transform).  Bone roll: the bone's local Z axis is aligned with `zref` (projected)."""
    arm = bpy.data.armatures.new(rig_name)
    rig = bpy.data.objects.new(rig_name, arm)
    (collection or bpy.context.scene.collection).objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones
    for b in spec['bones']:
        e = eb.new(b['name'])
        e.head = Vector(b['head'])
        e.tail = Vector(b['tail'])
        e.use_deform = (b['name'] != 'Root')
        d = np.array(b['tail']) - np.array(b['head'])
        d /= np.linalg.norm(d)
        z = np.array(b['zref'], float)
        z = z - np.dot(z, d) * d
        if np.linalg.norm(z) < 1e-6:                  # zref parallel to the bone: pick any perpendicular
            z = np.cross(d, [1.0, 0.0, 0.0])
        z /= np.linalg.norm(z)
        e.align_roll(Vector(z))
    for b in spec['bones']:
        e = eb[b['name']]
        if b['parent']:
            e.parent = eb[b['parent']]
            e.use_connect = False          # joints are placed by measurement; connection is not forced
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.display_type = 'STICK'
    rig.show_in_front = True
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return rig


def bone_viz(rig, radius=0.006, name='BoneViz'):
    """debug mesh: a prism per bone + a small octahedron at every head (armatures do not render)."""
    bm = bmesh.new()
    for b in rig.data.bones:
        h, t = Vector(b.head_local), Vector(b.tail_local)
        d = (t - h)
        L = d.length
        if L < 1e-6:
            continue
        d.normalize()
        ref = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
        u = d.cross(ref).normalized()
        v = d.cross(u).normalized()
        r0, r1 = radius, radius * 0.45
        ring0 = [bm.verts.new(h + (u * math.cos(a) + v * math.sin(a)) * r0) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
        ring1 = [bm.verts.new(t + (u * math.cos(a) + v * math.sin(a)) * r1) for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
        for i in range(6):
            j = (i + 1) % 6
            bm.faces.new((ring0[i], ring0[j], ring1[j], ring1[i]))
        bm.faces.new(ring0[::-1])
        bm.faces.new(ring1)
        s = radius * 1.5
        c = [bm.verts.new(h + Vector(p) * s) for p in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        for a, b_, c_ in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
            bm.faces.new((c[a], c[b_], c[c_]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o
