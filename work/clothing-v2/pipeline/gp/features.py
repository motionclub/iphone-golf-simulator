"""GARMENT PIPELINE: pose features of a frame from its bone matrices (root space), relative to the bind pose.
Used to (1) pick the stress pose library (worst frames per garment region) and (2) drive pose correctives at runtime
(the same features are computed in KitV2PoseCorrectives.cs)."""
import numpy as np

# (name, parent frame bone, segment start, segment end): segment direction expressed in the parent bone frame, rest-relative
SEGMENTS = [
    ('armL', 'UpperChest', 'LeftUpperArm', 'LeftLowerArm'), ('armR', 'UpperChest', 'RightUpperArm', 'RightLowerArm'),
    ('foreL', 'LeftUpperArm', 'LeftLowerArm', 'LeftHand'), ('foreR', 'RightUpperArm', 'RightLowerArm', 'RightHand'),
    ('thighL', 'Hips', 'LeftUpperLeg', 'LeftLowerLeg'), ('thighR', 'Hips', 'RightUpperLeg', 'RightLowerLeg'),
    ('shinL', 'LeftUpperLeg', 'LeftLowerLeg', 'LeftFoot'), ('shinR', 'RightUpperLeg', 'RightLowerLeg', 'RightFoot'),
    ('chest', 'Hips', 'Spine', 'Neck'), ('neck', 'UpperChest', 'Neck', 'Head'),
]
ROTS = [('trunk', 'Hips', 'UpperChest'), ('pelvis', None, 'Hips')]


def _pos(M, i): return M[..., i, :3, 3]


def _rot(M, i): return M[..., i, :3, :3]


def segment_dirs(hero, mats, rest):
    """-> dict name -> (F,3) unit direction in the parent's REST frame (rest-root axes: x = hero right, y = up, z = forward)."""
    b = hero.bidx
    mats = mats if mats.ndim == 4 else mats[None]
    out = {}
    for name, par, s, e in SEGMENTS:
        if par not in b or s not in b or e not in b: continue
        d = _pos(mats, b[e]) - _pos(mats, b[s])
        # parent rotation relative to rest: R = Rf @ Rr^T ; express d in the parent rest frame: Rr Rf^T d
        Rf, Rr = _rot(mats, b[par]), rest[b[par], :3, :3]
        d = np.einsum('ij,fkj,fk->fi', Rr, Rf, d)
        out[name] = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    return out


def rot_rel(hero, mats, rest, a, c):
    """rotation of c relative to a (rest-relative), as a rotation vector in a's rest frame (F,3), degrees."""
    b = hero.bidx
    mats = mats if mats.ndim == 4 else mats[None]
    Rc = np.einsum('fij,jk->fik', _rot(mats, b[c]), rest[b[c], :3, :3].T)       # world delta of c
    if a is None: Rd = Rc
    else:
        Ra = np.einsum('fij,jk->fik', _rot(mats, b[a]), rest[b[a], :3, :3].T)
        Rd = np.einsum('fji,fjk->fik', Ra, Rc)
    tr = np.clip((np.trace(Rd, axis1=1, axis2=2) - 1) / 2, -1, 1); ang = np.arccos(tr)
    ax = np.stack([Rd[:, 2, 1] - Rd[:, 1, 2], Rd[:, 0, 2] - Rd[:, 2, 0], Rd[:, 1, 0] - Rd[:, 0, 1]], 1)
    ax = ax / np.maximum(np.linalg.norm(ax, axis=1, keepdims=True), 1e-9)
    return np.degrees(ang)[:, None] * ax


def region_scores(hero, mats, rest):
    """named stress scores per frame (higher = harder for clothes), (F,) each."""
    D = segment_dirs(hero, mats, rest)
    R0 = segment_dirs(hero, rest[None], rest)
    s = {}
    ang = lambda a, b: np.degrees(np.arccos(np.clip((a * b).sum(-1), -1, 1)))
    for side, sg in (('L', -1.0), ('R', 1.0)):
        a = D['arm' + side]
        elev = ang(a, np.array([0, -1.0, 0]))                         # 0 hanging, 90 level, 180 overhead
        across = np.maximum(0, -a[:, 0] * sg) * np.maximum(0, a[:, 2])  # in front of and across the chest
        back = np.maximum(0, -a[:, 2])
        s['axilla_' + side] = elev
        s['across_' + side] = across * 100
        s['armback_' + side] = back * 100
        s['elbow_' + side] = ang(D['fore' + side], a)
        t = D['thigh' + side]
        s['hipflex_' + side] = ang(t, np.array([0, -1.0, 0])) * np.sign(t[:, 2] + 1e-6)
        s['hipabd_' + side] = np.abs(t[:, 0]) * 100
        s['knee_' + side] = ang(D['shin' + side], t)
    tr = rot_rel(hero, mats, rest, 'Hips', 'UpperChest')
    s['trunk_flex'] = np.abs(tr[:, 0]); s['trunk_twist'] = np.abs(tr[:, 1]); s['trunk_side'] = np.abs(tr[:, 2])
    s['shoulder_blade'] = s['across_L'] + s['across_R']
    s['overhead'] = np.minimum(s['axilla_L'], s['axilla_R'])
    s['side_seam_L'] = s['axilla_L'] * (1 + s['trunk_side'] / 30)
    s['side_seam_R'] = s['axilla_R'] * (1 + s['trunk_side'] / 30)
    s['waist'] = s['trunk_flex'] + .7 * s['trunk_twist'] + .7 * s['trunk_side']
    s['seat'] = np.maximum(s['hipflex_L'], s['hipflex_R'])
    s['kneel'] = np.maximum(s['knee_L'], s['knee_R']) + .5 * np.minimum(s['hipflex_L'], s['hipflex_R'])
    s['lunge'] = np.abs(s['hipflex_L'] - s['hipflex_R'])
    return s


def vector(hero, mats, rest):
    """compact feature vector per frame (F, K) for distances / correctives: segment directions (rest-relative) + trunk rotation."""
    D = segment_dirs(hero, mats, rest)
    parts = [D[k] for k in ('armL', 'armR', 'foreL', 'foreR', 'thighL', 'thighR', 'shinL', 'shinR', 'chest', 'neck') if k in D]
    tr = rot_rel(hero, mats, rest, 'Hips', 'UpperChest') / 90.0
    return np.concatenate(parts + [tr], 1)
