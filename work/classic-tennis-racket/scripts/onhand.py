"""On-hand pipeline (both bodies): socket solve in the hand frame, A-pose scene with Hand_Racket parented to the (copied) body,
proof-only ready-stance scene (fingers wrapped on a copy, arm skinned on a copy). Runs inside Blender (headless).

blender -b --factory-startup --python run_onhand.py -- <male|female> <racket.blend> <out_dir> [phi U_g V_g roll]
The hero blends are only read via bpy.data.libraries.load into this session; nothing is saved over them."""
import sys, json, hashlib
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
from fitlib import *
import render_lib as R
import wrap as WR
import fingerwrap as FW
from armpose import ArmRig
import male_hand as MH
import female_hand as FH

R_WRAP = 0.0176      # grip surface envelope (max radius of the tape bands 0.0173) + 0.3 mm: fingers rest on the band crests
RACKET_OBJS = ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket')


def sha_arr(a):
    return hashlib.sha256(np.ascontiguousarray(np.round(a, 7)).tobytes()).hexdigest()


class Profile:
    """Everything body specific: hand subset + frame, fingers, arm rig and ready-stance parameters."""

    def __init__(self, tag, body):
        self.tag = tag
        self.co = mesh_co(body)
        self.tris = mesh_tris(body)
        co, tris = self.co, self.tris
        if tag == 'male':
            sel, c, u, v, p = MH.frame_from_body(co)
            self.sel, self.c, self.u, self.v, self.p = sel, c, u, v, p
            self.Q = MH.to_hand(co[sel], c, u, v, p)
            chains = MH.build_chains(self.Q)
            self.fingers = []
            for name, ch in chains.items():
                self.fingers.append(dict(name=name, member=ch.member, M=ch.J[0], d=ch.axis_dir,
                                         length=MH.FINGERS[name]['tip'] - MH.U_MCP))
            self.to_hand, self.from_hand = MH.to_hand, MH.from_hand
            self.extra_clear_idx = np.array([], int)
            S = np.array([-0.2102, -0.0291, 1.3896]); E = np.array([-0.3345, -0.0380, 1.1535]); Wr = np.array([-0.529, -0.081, 0.967])
            self.rig = ArmRig(S, E, Wr)
            self.pose = dict(adduct=16.0, flex=95.0, twist=0.0)
            self.view_tgt_ready = (-0.25, -0.30, 1.05)
            self.hand_tgt_apose = (-0.60, -0.12, 0.88)
            self.tris_hand_filter = lambda x: (x[:, 0] < -0.50) & (x[:, 2] < 1.0)
        else:
            parts = FH.hand_parts(co, tris)
            self.parts = parts
            idx, c, u, v, p = FH.frame_from_parts(co, parts)
            self.sel, self.c, self.u, self.v, self.p = idx, c, u, v, p
            self.Q = FH.to_hand(co[idx], c, u, v, p)
            pos = {int(i): k for k, i in enumerate(idx)}
            self.fingers = []
            for k, fm in enumerate(FH.finger_models(co, parts, c, u, v, p)):
                member = np.zeros(len(idx))
                for i in fm['idx']:
                    member[pos[int(i)]] = 1.0
                self.fingers.append(dict(name=f'finger{k}', member=member, M=fm['M'], d=fm['d'], length=fm['length']))
            self.to_hand, self.from_hand = FH.to_hand, FH.from_hand
            fa = parts['forearm']
            self.extra_clear_idx = fa[co[fa, 2] < 0.95]
            # the arm shell is only joined to the torso above z ~ 1.15 (armpit): flood-fill from the forearm below that height
            from collections import deque
            adj = {}
            for a_, b_, c_ in tris:
                for u_, v_ in ((a_, b_), (b_, c_), (c_, a_)):
                    adj.setdefault(int(u_), set()).add(int(v_)); adj.setdefault(int(v_), set()).add(int(u_))
            seen = set(int(i) for i in fa)
            dq = deque(seen)
            while dq:
                u_ = dq.popleft()
                for v_ in adj.get(u_, ()):
                    if v_ not in seen and co[v_, 2] < 1.15:
                        seen.add(v_); dq.append(v_)
            self.arm_idx = np.array(sorted(seen))
            S = np.array([-0.195, 0.0, 1.355]); E = np.array([-0.212, 0.0, 1.07]); Wr = np.array([-0.232, 0.0, 0.83])
            self.rig = ArmRig(S, E, Wr, r_in=0.0005, r_out=0.001, r_sh=0.05, r_el=0.06, ext=0.0)      # membership comes from the flood-filled arm set (force), not from distance
            self.pose = dict(adduct=0.0, flex=95.0, twist=90.0)
            self.view_tgt_ready = (-0.22, -0.28, 0.95)
            self.hand_tgt_apose = (-0.24, 0.0, 0.76)
            self.tris_hand_filter = lambda x: (x[:, 0] < -0.20) & (x[:, 2] < 0.83)
        # clearance samples: hand subset (+ forearm bottom for the female), vertices + edge midpoints + centroids
        idxmap = -np.ones(len(co), int)
        allidx = np.concatenate([self.sel, self.extra_clear_idx]).astype(int)
        idxmap[allidx] = np.arange(len(allidx))
        Qall = self.to_hand(co[allidx], c, u, v, p)
        Ts = idxmap[tris]
        Ts = Ts[np.all(Ts >= 0, axis=1)]
        qa, qb, qc = Qall[Ts[:, 0]], Qall[Ts[:, 1]], Qall[Ts[:, 2]]
        self.Qs = np.concatenate([Qall, (qa + qb) / 2, (qb + qc) / 2, (qc + qa) / 2, (qa + qb + qc) / 3])

    # ------------------------------------------------------------------ socket
    def socket(self, phi, U_g, V_g, roll, margin=0.0005):
        a = WR.axis_dir(phi)
        W_g = WR.lift_for_clearance(self.Qs, (U_g, V_g), a, margin=margin)
        O = np.array([U_g, V_g, W_g])
        return dict(phi=phi, U_g=U_g, V_g=V_g, roll=roll, W_g=float(W_g), a=a, O=O)

    def racket_matrix_rest(self, sk):
        """4x4 world matrix of the racket (Hand_Racket) in the REST (A-pose) body frame, columns X_r Y_r Z_r O."""
        c, u, v, p = self.c, self.u, self.v, self.p
        a = sk['a']
        a_w = a[0] * u + a[1] * v
        Y = a_w / np.linalg.norm(a_w)
        Z = p - np.dot(p, Y) * Y
        Z /= np.linalg.norm(Z)
        Z = rot_about(Y, np.radians(sk['roll'])) @ Z
        X = np.cross(Y, Z)
        Ow = c + sk['O'][0] * u + sk['O'][1] * v + sk['O'][2] * p
        M = np.eye(4)
        M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, Ow
        return M

    # ------------------------------------------------------------------ finger wrap (proof only, copy)
    def wrapped_positions(self, sk):
        Qn = self.Q.copy()
        infos = {}
        for f in self.fingers:
            out, info = FW.wrap_finger(self.Q, f['member'], f['M'], f['d'], None, sk['O'], sk['a'], R=R_WRAP, length=f['length'])
            Qn += (out - self.Q)
            infos[f['name']] = info
        return Qn, infos

    def posed_body(self, sk):
        Qn, infos = self.wrapped_positions(sk)
        co2 = self.co.copy()
        co2[self.sel] = self.from_hand(Qn, self.c, self.u, self.v, self.p)
        rig = self.rig
        force = np.zeros(len(self.co)); force[self.sel] = 1.0
        if hasattr(self, 'arm_idx'):
            force[self.arm_idx] = 1.0                  # female: whole arm shell below the armpit (flood fill), incl. the forearm bottom
        rig.force = force
        co3 = rig.skin(co2, self.pose['adduct'], self.pose['flex'], self.pose['twist'], P_rest=self.co)
        Mh = rig.rigid_hand(self.pose['adduct'], self.pose['flex'], self.pose['twist'])
        return co3, co2, Mh, Qn, infos


def load_racket(racket_blend):
    with bpy.data.libraries.load(str(racket_blend), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in RACKET_OBJS]
    parts = {o.name: o for o in dst.objects}
    for o in parts.values():
        bpy.context.scene.collection.objects.link(o)
    return parts


def grey_body_material(body, rgb=(0.30, 0.30, 0.32)):
    mat = bpy.data.materials.new('Proof_Grey')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1)
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
    body.data.materials.clear()
    body.data.materials.append(mat)
    return mat


def bvh_world(o):
    """BVH of an object's mesh in WORLD space (BVHTree.FromObject is object-space!)."""
    mw = np.array(o.matrix_world)
    V = mesh_co(o) @ mw[:3, :3].T + mw[:3, 3]
    return bvh_from_arrays(V, mesh_tris(o))


def racket_vs_body(parts, body_tree, dg=None):
    return {n: tri_overlap_count(bvh_world(parts[n]), body_tree) for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')}


def min_clearance(parts, body_tree, only=('Grip', 'ButtCap', 'Racket_Classic', 'StringBed')):
    pts = []
    for n in only:
        o = parts[n]
        mw = np.array(o.matrix_world)
        V = mesh_co(o)
        T = mesh_tris(o)
        S = surface_samples(V, T)
        pts.append(S @ mw[:3, :3].T + mw[:3, 3])
    d = signed_clearance(body_tree, np.concatenate(pts))
    return float(d.min())
