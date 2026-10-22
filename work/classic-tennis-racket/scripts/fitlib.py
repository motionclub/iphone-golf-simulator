"""Hand frames, grip placement and exact clearance / intersection tests (runs inside Blender, headless).

Right hand = the character's right = world -X (the hero faces -Y).
Hand frame (all unit vectors, right handed):
    u : along the fingers (wrist -> finger tips)
    v : across the palm, towards the THUMB side
    p : palm normal = v x u   (points out of the palm, i.e. towards where the palm faces)
Racket frame in that hand (eastern/continental-ish hold):
    Y_r (shaft, towards the head) = cos(phi) * v + sin(phi) * u      (head leaves on the thumb/index side, butt on the heel)
    Z_r (hitting-face normal)     = p rotated about Y_r by `roll`
    X_r = Y_r x Z_r
"""
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

from common import *


def hand_frame_from_points(P, z_cut=None):
    """PCA frame of a hand point cloud. Returns c, u, v, p (u down the fingers, v towards the thumb (+front for the
    right hand in the A-pose), p = v x u palm normal)."""
    c = P.mean(0)
    U, S, Vt = np.linalg.svd(P - c, full_matrices=False)
    u, v = Vt[0], Vt[1]
    if u[2] > 0:
        u = -u
    return c, u, v, S


def rot_about(axis, ang):
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * (K @ K)


def racket_axes(u, v, p, phi_deg, roll_deg):
    phi, roll = np.radians(phi_deg), np.radians(roll_deg)
    Y = np.cos(phi) * v + np.sin(phi) * u
    Y /= np.linalg.norm(Y)
    Z0 = p - np.dot(p, Y) * Y
    Z0 /= np.linalg.norm(Z0)
    Z = rot_about(Y, roll) @ Z0
    X = np.cross(Y, Z)
    return X, Y, Z


def bvh_of(obj_or_meshdata, depsgraph=None):
    dg = depsgraph or bpy.context.evaluated_depsgraph_get()
    if isinstance(obj_or_meshdata, bpy.types.Object):
        return BVHTree.FromObject(obj_or_meshdata, dg)
    raise TypeError


def bvh_from_arrays(V, T):
    return BVHTree.FromPolygons([tuple(map(float, v)) for v in V], [tuple(int(i) for i in t) for t in T], epsilon=0.0)


def signed_clearance(tree, pts):
    """Signed distance (m) of points to the closed mesh in `tree`: + outside, - inside (nearest-face-normal test)."""
    d = np.empty(len(pts))
    for i, q in enumerate(pts):
        loc, nrm, idx, dist = tree.find_nearest(Vector(q))
        if loc is None:
            d[i] = 1.0
            continue
        s = np.dot(np.array(q) - np.array(loc), np.array(nrm))
        d[i] = dist if s >= 0 else -dist
    return d


def surface_samples(V, T, per_tri_min=0.003):
    """Vertices + edge midpoints + centroid of each triangle -> denser point set for clearance tests."""
    V = np.asarray(V)
    T = np.asarray(T)
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    pts = [V, (a + b) / 2, (b + c) / 2, (c + a) / 2, (a + b + c) / 3]
    return np.concatenate(pts, axis=0)


def tri_overlap_count(treeA, treeB):
    return len(treeA.overlap(treeB))
