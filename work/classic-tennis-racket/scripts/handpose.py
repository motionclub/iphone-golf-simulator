"""Proof-only hand posing on a COPY of the hero hand (numpy linear-blend skinning in the hand frame).

Hand frame coordinates (U, V, Wp): U along the fingers, V towards the thumb, Wp = palm normal (p = v x u).
The hero mesh is never modified: `pose()` returns new vertex positions for the hand vertex subset only.
"""
import numpy as np


def rot_about(axis, ang):
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * (K @ K)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def rodrigues(axis, ang):
    return rot_about(axis, ang)


class Chain:
    """A digit: joints J[k] (3,) in hand-frame coords, hinge axes h[k], blend radii r[k]; weights by distance along `axis_dir`."""

    def __init__(self, name, joints, hinges, radii, axis_dir, member):
        self.name = name
        self.J = [np.asarray(j, float) for j in joints]
        self.h = [np.asarray(h, float) / np.linalg.norm(h) for h in hinges]
        self.r = radii
        self.axis_dir = np.asarray(axis_dir, float) / np.linalg.norm(axis_dir)
        self.member = member            # (n,) float membership weight 0..1 of each hand vertex in this digit

    def bone_weights(self, Q):
        """(n, nb+1) weights: column 0 = parent (palm), k = bone k."""
        n = len(Q)
        s = []
        for j, r in zip(self.J, self.r):
            t = (Q - j) @ self.axis_dir
            s.append(smoothstep((t + r) / (2 * r)))
        s = np.stack(s, 1) * self.member[:, None]            # (n, nj)
        W = np.zeros((n, len(self.J) + 1))
        W[:, 0] = 1 - s[:, 0]
        for k in range(len(self.J)):
            nxt = s[:, k + 1] if k + 1 < len(self.J) else 0.0
            W[:, k + 1] = s[:, k] - nxt
        return W

    def bone_matrices(self, angles):
        """List of 4x4 matrices (hand-frame) for bones 1..nb."""
        mats = []
        M = np.eye(4)
        for j, h, a in zip(self.J, self.h, angles):
            R = np.eye(4)
            R[:3, :3] = rodrigues(h, a)
            R[:3, 3] = j - R[:3, :3] @ j
            M = M @ R
            mats.append(M.copy())
        return mats


def apply_chain(Q, chain, angles, W=None):
    """Skin the hand-frame points Q (n,3) with the chain; returns displaced points (only the digit's influence)."""
    if W is None:
        W = chain.bone_weights(Q)
    mats = chain.bone_matrices(angles)
    Qh = np.concatenate([Q, np.ones((len(Q), 1))], axis=1)
    out = W[:, 0:1] * Q
    for k, M in enumerate(mats):
        out = out + W[:, k + 1:k + 2] * (Qh @ M.T)[:, :3]
    return out
