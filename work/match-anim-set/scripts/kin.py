"""Numpy kinematics of the fitted hero rig (pure numpy, no bpy).

Pose = one 3x3 *basis* rotation per bone (the pose-bone rotation, expressed in the bone's rest frame) + a location for the Hips.
FK follows Blender's evaluation exactly:   M_pose[i] = M_pose[parent] @ (M_rest[parent]^-1 @ M_rest[i]) @ basis[i].

Authoring frame (used by the clip definitions): (r, f, u) = (the hero's right, forward, up), origin on the ground under the Root bone.
World (Blender) = (-r, -f, u) + Root origin, because the heroes face -Y and their right is -X.
"""
import json
import math

import numpy as np

# ----------------------------------------------------------------------------------------------------- rotations
def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def axis_angle(axis, ang):
    axis = np.asarray(axis, float)
    n = np.linalg.norm(axis)
    if n < 1e-12 or abs(ang) < 1e-14:
        return np.eye(3)
    a = axis / n
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def mat_to_quat(R):
    """3x3 rotation -> (w, x, y, z), w >= 0 not enforced."""
    R = np.asarray(R, float)
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def quat_to_mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                     w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def qconj(q):
    return np.array([q[0], -q[1], -q[2], -q[3]])


def qslerp(a, b, t):
    d = float(np.dot(a, b))
    if d < 0:
        b = -b
        d = -d
    if d > 0.9995:
        r = a + t * (b - a)
        return r / np.linalg.norm(r)
    th = math.acos(min(1.0, d))
    return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)


def qlog(q):
    v = q[1:]
    n = np.linalg.norm(v)
    if n < 1e-12:
        return np.zeros(3)
    return v / n * math.atan2(n, q[0])


def qexp(v):
    n = np.linalg.norm(v)
    if n < 1e-12:
        return np.array([1.0, 0, 0, 0])
    return np.concatenate([[math.cos(n)], v / n * math.sin(n)])


def mat_pow(R, w):
    """R^w for a rotation matrix (axis-angle scaling)."""
    q = mat_to_quat(R)
    if q[0] < 0:
        q = -q
    ang = 2 * math.acos(min(1.0, q[0]))
    s = math.sqrt(max(0.0, 1 - q[0] ** 2))
    if s < 1e-9:
        return np.eye(3)
    return axis_angle(q[1:] / s, ang * w)


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def frame_from_yx(y, x_hint):
    """right-handed rotation matrix with columns (X, Y, Z): Y = y, X = x_hint made orthogonal to Y, Z = X x Y."""
    y = unit(y)
    x = np.asarray(x_hint, float) - np.dot(x_hint, y) * y
    x = unit(x)
    z = np.cross(x, y)
    return np.stack([x, y, z], 1)


# ----------------------------------------------------------------------------------------------------- authoring frame
def a2w(v):
    """authoring (r, f, u) -> world direction (-r, -f, u)."""
    v = np.asarray(v, float)
    return np.array([-v[0], -v[1], v[2]])


def w2a(v):
    v = np.asarray(v, float)
    return np.array([-v[0], -v[1], v[2]])


# ----------------------------------------------------------------------------------------------------- the rig
class Rig:
    def __init__(self, path_or_dict):
        d = json.load(open(path_or_dict)) if isinstance(path_or_dict, str) else path_or_dict
        self.tag = d['tag']
        self.data = d
        self.names = [b['name'] for b in d['bones']]
        self.idx = {n: i for i, n in enumerate(self.names)}
        n = len(self.names)
        self.n = n
        self.parent = np.array([self.idx[b['parent']] if b['parent'] else -1 for b in d['bones']])
        self.Mrest = np.array([b['matrix_local'] for b in d['bones']], float)         # (n,4,4) armature space
        self.Rrest = self.Mrest[:, :3, :3].copy()
        self.hrest = self.Mrest[:, :3, 3].copy()
        self.length = np.array([b['length'] for b in d['bones']])
        self.rel_rot = np.zeros((n, 3, 3))
        self.rel_off = np.zeros((n, 3))
        for i in range(n):
            p = self.parent[i]
            if p < 0:
                self.rel_rot[i] = self.Rrest[i]
                self.rel_off[i] = self.hrest[i]
            else:
                self.rel_rot[i] = self.Rrest[p].T @ self.Rrest[i]
                self.rel_off[i] = self.Rrest[p].T @ (self.hrest[i] - self.hrest[p])
        self.tail_rest = np.array([b['tail'] for b in d['bones']], float)
        self.J = {k: np.array(v) for k, v in d['joints'].items()}
        self.measures = d['measures']
        self.root_origin = self.hrest[self.idx['Root']].copy()           # (0, y_root, 0)

    # --- FK
    def fk(self, basis, hips_loc=None):
        """basis: (n,3,3) local rotations (bone rest frame).  returns Q (n,3,3) world orientations and P (n,3) head positions."""
        n = self.n
        Q = np.zeros((n, 3, 3))
        P = np.zeros((n, 3))
        for i in range(n):
            p = self.parent[i]
            loc = np.zeros(3)
            if hips_loc is not None and self.names[i] == 'Hips':
                loc = np.asarray(hips_loc, float)
            if p < 0:
                Q[i] = self.rel_rot[i] @ basis[i]
                P[i] = self.rel_off[i] + self.rel_rot[i] @ loc
            else:
                Q[i] = Q[p] @ self.rel_rot[i] @ basis[i]
                P[i] = P[p] + Q[p] @ (self.rel_off[i] + self.rel_rot[i] @ loc)
        return Q, P

    def basis_from_world(self, Q_world, i):
        """basis rotation that gives bone i the world orientation Q_world given its parent's current world orientation (call with parent solved)."""
        raise NotImplementedError

    def bi(self, name):
        return self.idx[name]
