"""Fast numpy twin of the right-hand armature (linear blend skinning, flexion about each bone's local X) + analytic racket model, used to
search the grip placement and to close the fingers.  The result is always re-checked through Blender's real armature modifier
(handrig.verify_numpy_vs_blender) and against the real racket mesh (BVH), so nothing here is trusted on its own.

Conventions: everything in armature space (= world; the rig has an identity transform).  Angles in degrees, +flexion = towards the palm."""
import math
import numpy as np

FINGERS = ('index', 'middle', 'ring', 'pinky')


def rx(theta_rad):
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    M = np.eye(4)
    M[1, 1], M[1, 2], M[2, 1], M[2, 2] = c, -s, s, c
    return M


class NumpyLBS:
    def __init__(self, rig, hand_rest, weights):
        """rig: armature object; hand_rest: (n,3) rest positions of the hand vertices; weights: dict bone -> (n,) (sum to 1)."""
        self.names = [b.name for b in rig.data.bones]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.rest = [np.array(b.matrix_local) for b in rig.data.bones]
        self.parent = [self.idx[b.parent.name] if b.parent else -1 for b in rig.data.bones]
        self.rel = [self.rest[i] if self.parent[i] < 0 else np.linalg.inv(self.rest[self.parent[i]]) @ self.rest[i] for i in range(len(self.names))]
        self.inv_rest = [np.linalg.inv(m) for m in self.rest]
        self.X0 = np.asarray(hand_rest, float)
        self.Xh = np.concatenate([self.X0, np.ones((len(self.X0), 1))], axis=1)
        self.W = np.stack([weights.get(n, np.zeros(len(self.X0))) for n in self.names], 1)      # (n, nb)
        self.order = [i for i in range(len(self.names))]                                          # bones were created parent-first

    def skin_matrices(self, ang):
        P = [None] * len(self.names)
        for i in self.order:
            R = rx(math.radians(ang.get(self.names[i], 0.0)))
            P[i] = (self.rel[i] if self.parent[i] < 0 else P[self.parent[i]] @ self.rel[i]) @ R
        return [P[i] @ self.inv_rest[i] for i in range(len(self.names))]

    def skin(self, ang, subset=None):
        S = self.skin_matrices(ang)
        Xh = self.Xh if subset is None else self.Xh[subset]
        W = self.W if subset is None else self.W[subset]
        out = np.zeros((len(Xh), 3))
        for i, M in enumerate(S):
            w = W[:, i]
            nz = w > 1e-9
            if nz.any():
                out[nz] += w[nz, None] * (Xh[nz] @ M.T)[:, :3]
        return out


class RacketModel:
    """grip (+ butt cap) cylinder and the frame stem as capsules in the racket frame (+Y towards the head), placed by a 4x4 world matrix."""

    def __init__(self, M):
        self.M = np.asarray(M, float)
        self.o = self.M[:3, 3]
        self.a = self.M[:3, 1] / np.linalg.norm(self.M[:3, 1])

    def dist(self, X, margin_only=False):
        """unsigned-ish distance (m) from points X (n,3) to the racket surface: min over grip (R .0173, s in [-.0972,.099]), butt cap
        (R .019, s in [-.111,-.0972]) and the stem capsule (R .012, s in [.099,.19]); negative inside."""
        d = X - self.o
        s = d @ self.a
        radial = np.linalg.norm(d - s[:, None] * self.a, axis=1)

        def seg(lo, hi, R):
            sc = np.clip(s, lo, hi)
            r = np.sqrt(radial ** 2 + (s - sc) ** 2)
            return r - R
        return np.minimum(np.minimum(seg(-0.0972, 0.099, 0.0173), seg(-0.111, -0.0972, 0.019)), seg(0.099, 0.19, 0.012))


def close_digit_np(lbs, rk, ang, names, masks, top, start=None, margin=0.0003, n=60, subset=None):
    """sequential contact closing (see handrig.close_digit); pure numpy.  masks: list of 3 boolean arrays over the hand vertices."""
    cur = [ang[nm] for nm in names] if start is None else list(start)
    frozen = [False] * 3
    trace = []

    def state(s, st0):
        return [cur[k] if frozen[k] else st0[k] + (top[k] - st0[k]) * s for k in range(3)]

    def dists(st):
        tr = dict(ang)
        for k in range(3):
            tr[names[k]] = st[k]
        X = lbs.skin(tr)
        return [rk.dist(X[masks[k]]).min() if (not frozen[k] and masks[k].any()) else np.inf for k in range(3)]

    guard = 0
    while not all(frozen) and guard < 6:
        guard += 1
        st0 = list(cur)
        free = [k for k in range(3) if not frozen[k]]
        hit = None
        s_prev = 0.0
        for i in range(0, n + 1):
            s = i / n
            d = dists(state(s, st0))
            ks = [k for k in free if d[k] <= margin]
            if ks:
                hit = (min(ks), s_prev, s)
                break
            s_prev = s
        if hit is None:
            for k in free:
                cur[k] = top[k]
                frozen[k] = True
            trace.append(('free', list(cur)))
            break
        kmin, lo, hi = hit
        if lo == 0.0 and hi == 0.0:                     # touching at the start: this segment stays where it is
            for k in range(kmin + 1):
                frozen[k] = True
            trace.append(('start_contact', kmin + 1, list(cur)))
            continue
        for _ in range(10):
            mid = 0.5 * (lo + hi)
            if min(dists(state(mid, st0))[k] for k in free) <= margin:
                hi = mid
            else:
                lo = mid
        stt = state(lo, st0)
        for k in range(3):
            cur[k] = stt[k]
        for k in range(kmin + 1):
            frozen[k] = True
        trace.append(('contact_seg', kmin + 1, list(cur)))
    return cur, frozen, trace


def lift_for_clearance(X, c_uv_world, a, p, R=0.0173, margin=0.0004, w0=-0.02, w1=0.12):
    """smallest lift W (along p) so the infinite cylinder through (c_uv + W p) with direction a stays >= R + margin from every point X."""
    def clear(W):
        c = c_uv_world + W * p
        d = X - c
        s = d @ a
        r = np.linalg.norm(d - s[:, None] * a, axis=1)
        return (r - (R + margin)).min()
    lo, hi = w0, w1
    if clear(lo) >= 0:
        return lo
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if clear(mid) >= 0:
            hi = mid
        else:
            lo = mid
    return hi
