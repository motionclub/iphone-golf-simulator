"""Proof-only arm pose (shoulder adduction/abduction about the forward axis, elbow flexion, optional forearm twist) on a COPY of a hero body.
Linear blend skinning in world coordinates. Used to build the 'ready stance' proof images; the hero meshes are never touched."""
import numpy as np
from handpose import smoothstep, rot_about


def seg_dist(P, A, B):
    """Distance from points P (n,3) to segment AB."""
    AB = B - A
    t = np.clip(((P - A) @ AB) / (AB @ AB), 0, 1)
    return np.linalg.norm(P - (A + t[:, None] * AB), axis=1)


class ArmRig:
    """Joints S (shoulder), E (elbow), Wr (wrist) in world coordinates (rest pose)."""

    def __init__(self, S, E, Wr, r_in=0.075, r_out=0.115, r_sh=0.06, r_el=0.05, twist_len=0.20, ext=0.35):
        self.S, self.E, self.Wr = [np.asarray(x, float) for x in (S, E, Wr)]
        self.ext = ext
        self.r_in, self.r_out, self.r_sh, self.r_el, self.twist_len = r_in, r_out, r_sh, r_el, twist_len
        self.d_ua = (self.E - self.S) / np.linalg.norm(self.E - self.S)
        self.d_fa = (self.Wr - self.E) / np.linalg.norm(self.Wr - self.E)
        self.axis = (self.Wr - self.S) / np.linalg.norm(self.Wr - self.S)

    force = None            # optional (n,) array in [0,1] added to the membership (e.g. the whole hand vertex set)

    def member(self, P):
        d = np.minimum(seg_dist(P, self.S, self.E), seg_dist(P, self.E, self.Wr + (self.Wr - self.E) * self.ext))
        m = smoothstep((self.r_out - d) / (self.r_out - self.r_in))
        if self.force is not None and len(self.force) == len(P):
            m = np.maximum(m, self.force)
        return m

    def weights(self, P):
        m = self.member(P)
        t_s = (P - self.S) @ self.axis
        # elbow position along the same axis
        t_e = (self.E - self.S) @ self.axis
        s1 = smoothstep((t_s + self.r_sh) / (2 * self.r_sh)) * m
        s2 = smoothstep((t_s - t_e + self.r_el) / (2 * self.r_el)) * m
        return s1, s2

    def bone_mats(self, adduct_deg, flex_deg, forward=np.array([0.0, -1.0, 0.0])):
        # shoulder: rotate about the forward axis (positive = arm moves towards the body for the right arm)
        R1 = np.eye(4)
        R1[:3, :3] = rot_about(forward, np.radians(adduct_deg))
        R1[:3, 3] = self.S - R1[:3, :3] @ self.S
        # elbow hinge: d_fa x forward  (positive = forearm swings towards `forward`)
        h = np.cross(self.d_fa, forward)
        h /= np.linalg.norm(h)
        R2 = np.eye(4)
        R2[:3, :3] = rot_about(h, np.radians(flex_deg))
        R2[:3, 3] = self.E - R2[:3, :3] @ self.E
        M1 = R1
        M2 = R1 @ R2
        return M1, M2, h

    def twist(self, P, twist_deg):
        """Pre-twist (about the rest forearm axis through E, ramped along the forearm) applied before the elbow flexion."""
        if abs(twist_deg) < 1e-6:
            return P.copy()
        t = (P - self.E) @ self.d_fa
        ang = np.radians(twist_deg) * smoothstep(t / self.twist_len) * (self.member(P) > 0.5)
        out = P.copy()
        k = self.d_fa
        v = P - self.E
        cosA, sinA = np.cos(ang)[:, None], np.sin(ang)[:, None]
        vr = v * cosA + np.cross(k[None, :], v) * sinA + k[None, :] * ((v @ k)[:, None]) * (1 - cosA)
        sel = ang != 0
        out[sel] = self.E + vr[sel]
        return out

    def skin(self, P, adduct_deg, flex_deg, twist_deg=0.0, P_rest=None):
        """Skin P (n,3). Weights come from the REST positions (P_rest, default P) so that a hand that was already deformed
        (e.g. fingers wrapped round a grip) is carried rigidly by the arm instead of being re-weighted."""
        P = np.asarray(P, float)
        Pw = P if P_rest is None else np.asarray(P_rest, float)
        Pt = self.twist(P, twist_deg) if P_rest is None else self._twist_with(P, Pw, twist_deg)
        s1, s2 = self.weights(Pw)
        M1, M2, h = self.bone_mats(adduct_deg, flex_deg)
        Ph = np.concatenate([Pt, np.ones((len(P), 1))], axis=1)
        p1 = (Ph @ M1.T)[:, :3]
        p2 = (Ph @ M2.T)[:, :3]
        w0, w1, w2 = 1 - s1, s1 - s2, s2
        return w0[:, None] * P + w1[:, None] * p1 + w2[:, None] * p2

    def _twist_with(self, P, Pw, twist_deg):
        if abs(twist_deg) < 1e-6:
            return P.copy()
        t = (Pw - self.E) @ self.d_fa
        ang = np.radians(twist_deg) * smoothstep(t / self.twist_len) * (self.member(Pw) > 0.5)
        out = P.copy()
        k = self.d_fa
        v = P - self.E
        cosA, sinA = np.cos(ang)[:, None], np.sin(ang)[:, None]
        vr = v * cosA + np.cross(k[None, :], v) * sinA + k[None, :] * ((v @ k)[:, None]) * (1 - cosA)
        sel = ang != 0
        out[sel] = self.E + vr[sel]
        return out

    def rigid_hand(self, adduct_deg, flex_deg, twist_deg=0.0):
        """4x4 matrix of the hand (weight fully on the forearm bone), including the pre-twist about the forearm axis."""
        M1, M2, h = self.bone_mats(adduct_deg, flex_deg)
        Tw = np.eye(4)
        if abs(twist_deg) > 1e-6:
            Tw[:3, :3] = rot_about(self.d_fa, np.radians(twist_deg))
            Tw[:3, 3] = self.E - Tw[:3, :3] @ self.E
        return M2 @ Tw
