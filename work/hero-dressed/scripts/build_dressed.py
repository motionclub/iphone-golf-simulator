"""Build  export/HeroBase_<Hero>_Dressed.blend : the match-anim-set hero blend (rig + Body + Face + racket + 16 actions, untouched) PLUS the six White-kit pieces,
skinned to the hero's own rig.

  blender -b --factory-startup <work/match-anim-set/export/HeroBase_<Hero>_MatchAnims.blend> --python build_dressed.py -- <male|female>

Kit geometry (positions, topology, custom normals, UVs) is copied unchanged from work/tennis-shoes-fit/export/StandardKit_<Hero>.blend (world transform baked in -
it is identity for every White piece, checked and logged).  Only the material slots are renamed/merged into the seven roles and vertex-group weights are added
(D2 in GATE_DEFS_preregistered.md).  Tuning knobs come from the environment (DR_*) and are written to data/build_<hero>.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

from dcommon import *

tag = args_after_dashes()[0]
H = HERO[tag]
sc = bpy.context.scene


def envf(k, d):
    return float(os.environ.get(k, d))


# ---- tuning knobs (logged) ----------------------------------------------------------------------------------------------------------------
KNOBS = dict(
    cloth_iters=int(envf('DR_CLOTH_ITERS', 6)), cloth_factor=envf('DR_CLOTH_FACTOR', 0.5),
    bottom_iters=int(envf('DR_BOTTOM_ITERS', 6 if tag == 'male' else 2)), bottom_factor=envf('DR_BOTTOM_FACTOR', 0.5),
    sock_iters=int(envf('DR_SOCK_ITERS', 2)), sock_factor=envf('DR_SOCK_FACTOR', 0.5),
    shoe_iters=int(envf('DR_SHOE_ITERS', 0)), shoe_factor=envf('DR_SHOE_FACTOR', 0.5),
)
KNOBS['transfer'] = os.environ.get('DR_TRANSFER', 'nearest')          # 'nearest' (Data Transfer semantics) or 'ray' (weights of the body vertex under each kit point, harmonic fill elsewhere)
KNOBS['ray_blend'] = envf('DR_RAY_BLEND', 1.0)                       # 1 = pure ray transfer where covered; <1 mixes in the nearest-face transfer
KNOBS['fill_iters'] = int(envf('DR_FILL_ITERS', 400))
KNOBS['top_legs'] = int(envf('DR_TOP_LEGS', 1))
KNOBS['ray_gap'] = envf('DR_RAY_GAP', 0.035)
KNOBS['weld_eps'] = envf('DR_WELD_EPS', 0.0)
KNOBS['top_env'] = envf('DR_TOP_ENV', 0.0)
KNOBS['top_sleeve'] = envf('DR_TOP_SLEEVE', 0.0)
KNOBS['top_sleeve_R'] = envf('DR_TOP_SLEEVE_R', 0.07)
KNOBS['top_env_pow'] = envf('DR_TOP_ENV_POW', 3.0)
KNOBS['top_env_lo'] = envf('DR_TOP_ENV_LO', 0.025)
KNOBS['restrict_nearest'] = int(envf('DR_RESTRICT_NEAREST', 1))
KNOBS['skirt_env'] = envf('DR_SKIRT_ENV', 1.0 if tag == 'female' else 0.0)
KNOBS['skirt_env_pow'] = envf('DR_SKIRT_ENV_POW', 3.0)
KNOBS['skirt_ramp'] = envf('DR_SKIRT_RAMP', 0.0)
KNOBS['shoe_profile'] = int(envf('DR_SHOE_PROFILE', 1))
KNOBS['shoe_shift'] = envf('DR_SHOE_SHIFT', 0.0)
KNOBS['shoe_blend'] = envf('DR_SHOE_BLEND', 0.75)
KNOBS['shoe_ankle'] = int(envf('DR_SHOE_ANKLE', 0))
KNOBS['side_split'] = int(envf('DR_SIDE_SPLIT', 1))
KNOBS['bottom_hips'] = envf('DR_BOTTOM_HIPS', -1)         # <0: off; else the Hips share at the hem
KNOBS['bottom_hips_gain'] = envf('DR_BOTTOM_HIPS_GAIN', 1.0)
KNOBS['ray_tol'] = envf('DR_RAY_TOL', 0.004)
OUT_BLEND = os.environ.get('DR_OUT_BLEND', H['dressed'])

rig = bpy.data.objects[H['rig']]
body = bpy.data.objects[H['body']]
assert rig.type == 'ARMATURE' and body.type == 'MESH'
bones = [b.name for b in rig.data.bones if b.use_deform]
print('deform bones', len(bones), 'of', len(rig.data.bones))

# ---- the rig must be in its rest pose and nothing may be evaluated through an action while we read the bind pose ----------------------------
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
bpy.context.view_layer.update()

# ---- 1. append the White kit (objects + their empties + materials) -----------------------------------------------------------------------
with bpy.data.libraries.load(H['kit'], link=False) as (src, dst):
    want = [n for n in src.objects if n.endswith('_White')]
    dst.objects = want
loaded = {o.name: o for o in dst.objects if o}
for o in loaded.values():
    sc.collection.objects.link(o)
bpy.context.view_layer.update()
report = dict(tag=tag, knobs=KNOBS, pieces={}, kit_blend_sha=sha256_file(H['kit']), anim_blend_sha=sha256_file(H['anim']))
for piece in PIECES:
    obj = loaded[H['pieces'][piece]]
    mw = np.array(obj.matrix_world, np.float64)
    ident_err = float(np.abs(mw - np.eye(4)).max())
    report['pieces'][piece] = dict(source_object=obj.name, world_matrix_vs_identity=ident_err)
    if ident_err > 1e-9:
        print('NOTE', obj.name, 'has a non-identity world matrix, baking it into the mesh; max |M-I| =', ident_err)
        obj.data.transform(Matrix(mw.tolist()))
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    obj.matrix_parent_inverse = Matrix.Identity(4)
for n, o in list(loaded.items()):
    if o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

# ---- 2. role materials: slot -> role, merged ----------------------------------------------------------------------------------------------
std = {n: bpy.data.materials[n] for n in ('Std_White_Lit', 'Std_Black_Lit')}
role_cache = {}


def role_mat(role):
    if role not in role_cache:
        m = std[ROLE_SOURCE[role]].copy()
        m.name = role
        role_cache[role] = m
    return role_cache[role]


def remap_materials(obj, piece):
    me = obj.data
    npoly = len(me.polygons)
    mi = np.empty(npoly, np.int32)
    me.polygons.foreach_get('material_index', mi)
    mapping = ROLE_SLOTS[piece]
    order = []
    for slot in sorted(set(int(x) for x in mi)):
        r = mapping[slot]
        if r not in order:
            order.append(r)
    new_mi = np.array([order.index(mapping[int(s)]) for s in mi], np.int32)
    me.materials.clear()                      # resets every polygon to slot 0 (known pitfall): indices are written back below
    for r in order:
        me.materials.append(role_mat(r))
    me.polygons.foreach_set('material_index', new_mi)
    me.update()
    return order, [int((new_mi == i).sum()) for i in range(len(order))]


# ---- 3. weights transferred by name from the body (bind pose) -----------------------------------------------------------------------------
bco = mesh_co(body)
btri = mesh_tris(body.data)
Wb = bone_weight_matrix(body, bones)
bvh = BVHTree.FromPolygons([tuple(map(float, v)) for v in bco], [tuple(map(int, t)) for t in btri], epsilon=0.0)
print('body', len(bco), 'verts', len(btri), 'tris; weighted vertices', int((Wb.sum(1) > 0).sum()))


def barycentric(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00 = (v0 * v0).sum(1)
    d01 = (v0 * v1).sum(1)
    d11 = (v1 * v1).sum(1)
    d20 = (v2 * v0).sum(1)
    d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    den = np.where(np.abs(den) < 1e-18, 1e-18, den)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    u = 1 - v - w
    bary = np.stack([u, v, w], 1)
    bary = np.clip(bary, 0, None)
    return bary / bary.sum(1, keepdims=True)


# per-side body BVHs for the leg region live in piece_bvhs(): a medial hem vertex of the left leg tube must not take the right thigh's weights (the thighs are 4 mm apart at the crotch)
tri_cx = bco[btri].mean(1)[:, 0]
CROTCH_Z = envf('DR_CROTCH_Z', 0.82)


_bvh_cache = {}


def piece_bvhs(allowed):
    """BVHs over the body triangles a piece may take weights from: all three vertices carry >= 50 % of their weight on the piece's whitelisted bones (the skirt must not look up the hanging hand's
    faces, which folded into Hips and gave the skirt side Hips-heavy weights).  Returns {0: all, +1: x >= -4 mm half, -1: x <= 4 mm half} as (bvh, original triangle indices)."""
    key = frozenset(allowed) if (KNOBS['restrict_nearest'] and allowed) else None
    if key in _bvh_cache:
        return _bvh_cache[key]
    if key is None:
        sel = np.arange(len(btri))
    else:
        mass = np.zeros(len(bco))
        for j, n in enumerate(bones):
            if n in key:
                mass += Wb[:, j]
        sel = np.nonzero((mass >= 0.5)[btri].all(1))[0]
    out = {}
    for sgn, ss in ((0, sel), (+1, sel[tri_cx[sel] * 1 >= -0.004]), (-1, sel[tri_cx[sel] * -1 >= -0.004])):
        out[sgn] = (BVHTree.FromPolygons([tuple(map(float, v)) for v in bco], [tuple(map(int, btri[i])) for i in ss], epsilon=0.0), ss)
    _bvh_cache[key] = out
    return out


def transfer(kco, side_split=False, allowed=None):
    loc = np.empty_like(kco)
    tri = np.empty(len(kco), np.int64)
    dist = np.empty(len(kco))
    bvhs = piece_bvhs(allowed)
    for i, p in enumerate(kco):
        sg = (1 if p[0] > 0 else -1) if (side_split and p[2] < CROTCH_Z and abs(p[0]) > 0.0) else 0
        bv_, sel_ = bvhs[sg]
        l, n, idx, d = bv_.find_nearest(tuple(map(float, p)))
        idx = int(sel_[idx])
        loc[i] = l
        tri[i] = idx
        dist[i] = d
    t = btri[tri]
    bary = barycentric(loc, bco[t[:, 0]], bco[t[:, 1]], bco[t[:, 2]])
    W = (Wb[t[:, 0]] * bary[:, 0:1] + Wb[t[:, 1]] * bary[:, 1:2] + Wb[t[:, 2]] * bary[:, 2:3])
    return W, dist


PARENT = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
ARM_HEAD = {n for n in bones if ('Arm' in n or 'Hand' in n or any(k in n for k in ('Thumb', 'Index', 'Middle', 'Ring', 'Little')) or n in ('Head', 'Neck') or 'Shoulder' in n or n.endswith('Chest'))}


def allowed_set(piece):
    side = 'Left' if piece.endswith('_L') else 'Right'
    if piece == 'Top':
        a = {'Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'LeftShoulder', 'RightShoulder', 'LeftUpperArm', 'RightUpperArm', 'LeftLowerArm', 'RightLowerArm'}
        if KNOBS.get('top_legs'):
            a |= {'LeftUpperLeg', 'RightUpperLeg'}
        return a
    if piece == 'Bottom':
        return {'Hips', 'Spine', 'LeftUpperLeg', 'RightUpperLeg', 'LeftLowerLeg', 'RightLowerLeg'}
    return {side + 'LowerLeg', side + 'Foot', side + 'Toes'}


def fold_target(bone, piece, allowed):
    """Where the weight of a bone the piece may not use goes: the nearest allowed ancestor; Bottom folds arm / head / chest bones into Hips; sock / shoe into LowerLeg."""
    if piece == 'Bottom':
        return 'Hips'
    if piece.startswith(('Sock', 'Shoe')):
        return ('Left' if piece.endswith('_L') else 'Right') + 'LowerLeg'
    b = PARENT.get(bone)
    while b is not None and b not in allowed:
        b = PARENT.get(b)
    return b or 'Hips'


def fold_to_whitelist(W, piece):
    allowed = allowed_set(piece)
    W = W.copy()
    moved = 0.0
    for j, n in enumerate(bones):
        if n in allowed:
            continue
        col = W[:, j].copy()
        if col.max() <= 0:
            continue
        t = bones.index(fold_target(n, piece, allowed))
        assert bones[t] in allowed, (piece, n, bones[t])
        W[:, t] += col
        W[:, j] = 0
        moved += col.sum()
    report['pieces'][piece]['weight_folded_vertex_equiv'] = float(moved)
    return W


def smooth(W, edges, iters, factor):
    if iters <= 0:
        return W
    n = len(W)
    a, b = edges[:, 0], edges[:, 1]
    deg = np.bincount(np.concatenate([a, b]), minlength=n).astype(np.float64)
    deg[deg == 0] = 1
    for _ in range(iters):
        acc = np.zeros_like(W)
        np.add.at(acc, a, W[b])
        np.add.at(acc, b, W[a])
        W = (1 - factor) * W + factor * acc / deg[:, None]
    return W


def limit4(W):
    W = W.copy()
    W[W < 1e-3] = 0
    order = np.argsort(-W, axis=1)
    keep = np.zeros_like(W, bool)
    rows = np.arange(len(W))[:, None]
    keep[rows, order[:, :4]] = True
    W[~keep] = 0
    s = W.sum(1, keepdims=True)
    s[s == 0] = 1
    return W / s


bn_body = np.empty(len(bco) * 3, np.float32)
body.data.vertex_normals.foreach_get('vector', bn_body)
bn_body = bn_body.reshape(-1, 3).astype(np.float64)
BEAM = ((0, 0), (5e-4, 0), (-5e-4, 0), (0, 5e-4), (0, -5e-4))


def beam_origins(v, n):
    t1 = np.cross(n, [0.0, 0.0, 1.0] if abs(n[2]) < 0.9 else [1.0, 0.0, 0.0])
    t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)
    return [v + t1 * a + t2 * b for a, b in BEAM]


def ray_hits(bvh, o, d, maxd, limit=6):
    hits = []
    cur = np.array(o, float)
    travelled = 0.0
    for _ in range(limit):
        loc, nrm, idx, dist = bvh.ray_cast(tuple(map(float, cur)), tuple(map(float, d)), maxd - travelled)
        if loc is None:
            break
        travelled += dist
        hits.append((travelled, float(np.dot(np.array(nrm), d)), int(idx), np.array(loc)))
        cur = np.array(loc) + np.array(d) * 1e-6
        travelled += 1e-6
    return hits


def bary3(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-18:
        return np.array([1.0, 0.0, 0.0])
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.clip(np.array([1 - v - w, v, w]), 0, None)


def ray_transfer(kco, ktri, kedges, W_nearest):
    """weights of the body vertex under each kit point: every body vertex whose outward ray meets the piece exactly twice (inner wall, outer wall <= 12 mm behind)
    adds its weight vector to the corners of both hit triangles (barycentric); kit vertices that received mass keep that average, the rest is filled by harmonic diffusion."""
    bvk = BVHTree.FromPolygons([tuple(map(float, v)) for v in kco], [tuple(map(int, t)) for t in ktri], epsilon=0.0)
    S = np.zeros((len(kco), Wb.shape[1]))
    A = np.zeros(len(kco))
    nzone = 0
    for i in range(len(bco)):
        v, n = bco[i], bn_body[i]
        if bvk.find_nearest(tuple(map(float, v)), 0.08)[0] is None:
            continue
        good = 0
        for o in beam_origins(v, n):
            h = ray_hits(bvk, o, n, 1.0)
            if len(h) == 2 and h[0][1] < 0 and h[1][1] > 0 and h[1][0] - h[0][0] <= 0.012:
                good += 1
        if good < 3:
            continue
        h = ray_hits(bvk, v, n, 1.0)
        if not (len(h) == 2 and h[0][1] < 0 and h[1][1] > 0 and h[1][0] - h[0][0] <= 0.012):
            continue
        # mutual nearest: the body vertex must be (within 4 mm) the nearest body point to its own inner-wall hit, else the wall belongs to another body part
        if h[0][0] > KNOBS['ray_gap'] or bvh.find_nearest(tuple(map(float, h[0][3])))[3] < h[0][0] - KNOBS['ray_tol']:
            continue
        nzone += 1
        for (_, _, idx, loc) in h:
            t = ktri[idx]
            b = bary3(loc, kco[t[0]], kco[t[1]], kco[t[2]])
            for k in range(3):
                S[t[k]] += b[k] * Wb[i]
                A[t[k]] += b[k]
    known = A >= 0.1
    W = W_nearest.copy()
    Wr = np.zeros_like(W)
    Wr[known] = S[known] / A[known, None]
    # harmonic fill of the unknown vertices from the known ones (Dirichlet), starting from the nearest-face transfer
    a, b = kedges[:, 0], kedges[:, 1]
    n = len(kco)
    deg = np.bincount(np.concatenate([a, b]), minlength=n).astype(np.float64)
    deg[deg == 0] = 1
    X = Wr.copy()
    X[~known] = W_nearest[~known]
    for _ in range(KNOBS['fill_iters']):
        acc = np.zeros_like(X)
        np.add.at(acc, a, X[b])
        np.add.at(acc, b, X[a])
        Y = acc / deg[:, None]
        X[~known] = Y[~known]
    out = np.where(known[:, None], KNOBS['ray_blend'] * Wr + (1 - KNOBS['ray_blend']) * W_nearest, X)
    return out, dict(zone_n=nzone, known=int(known.sum()), verts=int(n))


def shoe_profile(W, kco, side):
    """A shoe bends where the foot bends: the Foot / Toes split of every shoe vertex follows the body's own profile along the foot axis (ankle joint -> toe joint),
    not the nearest body face (whose weights shift with the 28 mm sole offset).  The LowerLeg share (collar) keeps the transferred value."""
    ib = {b.name: b for b in rig.data.bones}
    f0 = np.array(ib[side + 'Foot'].head_local)
    t0_ = np.array(ib[side + 'Toes'].head_local)
    axis = t0_ - f0
    L2 = float(axis @ axis)
    jF, jT, jL = bones.index(side + 'Foot'), bones.index(side + 'Toes'), bones.index(side + 'LowerLeg')
    ub = ((bco - f0) @ axis) / L2
    foot_mass = Wb[:, jF] + Wb[:, jT]
    sel = (foot_mass > 0.9) & (np.sign(bco[:, 0]) == np.sign(f0[0]))
    bins = np.linspace(-0.4, 1.8, 45)
    prof = np.full(len(bins) - 1, np.nan)
    for i in range(len(bins) - 1):
        m = sel & (ub >= bins[i]) & (ub < bins[i + 1])
        if m.sum() >= 5:
            prof[i] = float((Wb[m, jT] / foot_mass[m]).mean())
    centers = 0.5 * (bins[:-1] + bins[1:])
    ok = ~np.isnan(prof)
    prof_s = np.maximum.accumulate(np.interp(centers, centers[ok], prof[ok]))        # monotone: Toes share only grows towards the toes
    u = ((kco - f0) @ axis) / L2
    f = np.interp(u + KNOBS['shoe_shift'], centers, prof_s)
    a = W[:, jF] + W[:, jT]
    if KNOBS['shoe_ankle']:
        # the LowerLeg share follows the body's own profile in HEIGHT (collar region only); the nearest-face value gave the heel counter 25-30 % LowerLeg weight, which lags behind the heel
        mass3 = Wb[:, jF] + Wb[:, jT] + Wb[:, jL]
        sel3 = (mass3 > 0.9) & (np.sign(bco[:, 0]) == np.sign(f0[0]))
        zb = np.linspace(0.0, 0.35, 36)
        gz = np.full(len(zb) - 1, np.nan)
        for i in range(len(zb) - 1):
            m = sel3 & (bco[:, 2] >= zb[i]) & (bco[:, 2] < zb[i + 1])
            if m.sum() >= 5:
                gz[i] = float((Wb[m, jL] / mass3[m]).mean())
        zc = 0.5 * (zb[:-1] + zb[1:])
        okz = ~np.isnan(gz)
        gz_s = np.maximum.accumulate(np.interp(zc, zc[okz], gz[okz]))
        lower = np.interp(kco[:, 2], zc, gz_s)
        a = 1.0 - lower
        out_lower = lower
    else:
        out_lower = None
    out = W.copy()
    out[:, jT] = (1 - KNOBS['shoe_blend']) * W[:, jT] + KNOBS['shoe_blend'] * a * f
    out[:, jF] = (1 - KNOBS['shoe_blend']) * W[:, jF] + KNOBS['shoe_blend'] * a * (1 - f)
    if out_lower is not None:
        out[:, jL] = (1 - KNOBS['shoe_blend']) * W[:, jL] + KNOBS['shoe_blend'] * out_lower
    report['pieces'][('Shoe_L' if side == 'Left' else 'Shoe_R')]['shoe_profile'] = dict(u_samples=[round(float(x), 3) for x in centers[ok][::4]], toes_share=[round(float(x), 3) for x in prof_s[ok][::4]])
    return out


kit_objs = {}
for piece in PIECES:
    src = loaded[H['pieces'][piece]]
    me = src.data
    me.name = KIT_NAME[piece]
    src.name = KIT_NAME[piece]
    kco = mesh_co(src)
    ed = np.empty(len(me.edges) * 2, np.int32)
    me.edges.foreach_get('vertices', ed)
    ed = ed.reshape(-1, 2)
    if piece.endswith('_L'):
        assert kco[:, 0].mean() > 0.05, (piece, 'expected the rig-left (x>0) piece')
    elif piece.endswith('_R'):
        assert kco[:, 0].mean() < -0.05, (piece, 'expected the rig-right (x<0) piece')
    W, dist = transfer(kco, side_split=(piece == 'Bottom' and KNOBS['side_split'] > 0), allowed=allowed_set(piece))
    if KNOBS['transfer'] == 'ray':
        Wn = W.copy()
        W, rinfo = ray_transfer(kco, mesh_tris(me), ed, W)
        report['pieces'][piece]['ray_transfer'] = rinfo
        if os.environ.get('DR_DUMP_W'):
            np.savez(f'{DATA}/wdump_{tag}_{piece}.npz', kco=kco, Wn=Wn, Wr=W, bones=np.array(bones))
    W = fold_to_whitelist(W, piece)
    if piece == 'Bottom' and KNOBS['skirt_ramp'] > 0:
        # loose cloth between the thighs (the skirt's front / back centre) follows BOTH thighs smoothly across the centre line instead of jumping from one thigh to the other;
        # vertices that hug a thigh (liner tubes, d <= 30 mm) keep their own side
        w_ = KNOBS['skirt_ramp']
        jL, jR = bones.index('LeftUpperLeg'), bones.index('RightUpperLeg')
        loose = (dist > 0.03) & (kco[:, 2] < CROTCH_Z)
        m = W[:, jL] + W[:, jR]
        tt = np.clip((kco[:, 0] + w_) / (2 * w_), 0, 1)
        share = tt * tt * (3 - 2 * tt)                       # Left share, smoothstep over x in [-w, w]
        W = W.copy()
        W[loose, jL] = (m * share)[loose]
        W[loose, jR] = (m * (1 - share))[loose]
        report['pieces'][piece]['skirt_ramp'] = dict(width=w_, loose_vertices=int(loose.sum()))
    if piece == 'Top' and KNOBS['top_sleeve'] > 0:
        # a vertex inside the sleeve tube (close to the upper-arm bone segment) belongs to the ARM even when the ribs are nearer (the female arm hangs 34 mm from the ribs: the underside of the sleeve
        # took chest weights and tore away from the arm in the forehand). Its weights come from the arm's own faces; a ramp (R .. R + 15 mm from the bone) hands over to the normal transfer.
        Rr = KNOBS['top_sleeve_R']
        Wn_ = W.copy()
        for side, sgn in (('Left', 1), ('Right', -1)):
            ua = rig.data.bones[side + 'UpperArm']
            a0, b0_ = np.array(ua.head_local), np.array(ua.tail_local)
            ab = b0_ - a0
            tt = ((kco - a0) @ ab) / (ab @ ab)
            dseg = np.linalg.norm(kco - (a0 + np.clip(tt, 0, 1)[:, None] * ab), axis=1)
            inside = (np.sign(kco[:, 0]) == sgn) & (tt > -0.05) & (tt < 1.05)
            sw = np.clip((Rr + 0.015 - dseg) / 0.015, 0, 1) * inside
            if sw.max() <= 0:
                continue
            bvs, sels = piece_bvhs({side + 'UpperArm', side + 'LowerArm', side + 'Shoulder'})[0]
            ids = np.nonzero(sw > 0)[0]
            Wa = np.zeros((len(ids), len(bones)))
            for q, i in enumerate(ids):
                l, n, idx, d = bvs.find_nearest(tuple(map(float, kco[i])))
                tri_ = btri[int(sels[idx])]
                bb = barycentric(np.array([l]), bco[tri_[0]][None], bco[tri_[1]][None], bco[tri_[2]][None])[0]
                Wa[q] = Wb[tri_[0]] * bb[0] + Wb[tri_[1]] * bb[1] + Wb[tri_[2]] * bb[2]
            W[ids] = (1 - sw[ids, None]) * Wn_[ids] + sw[ids, None] * Wa
        report['pieces'][piece]['top_sleeve'] = dict(R=Rr)
        W = fold_to_whitelist(W, piece)
    if piece == 'Top' and KNOBS['top_env'] > 0:
        # the loose part of the polo (the membrane between a hanging arm and the ribs, the hem) is far from both: envelope weights over the trunk and upper-arm bone segments make it a smooth bridge
        segsT = {}
        for n in ('Hips', 'Spine', 'Chest', 'UpperChest', 'LeftUpperArm', 'RightUpperArm', 'LeftUpperLeg', 'RightUpperLeg'):
            if n not in bones:
                continue
            bb = rig.data.bones[n]
            tail = np.array(bb.tail_local)
            if n == 'Hips':
                tail = np.array(rig.data.bones['Spine'].head_local)
            segsT[n] = (np.array(bb.head_local), tail)
        D = []
        for n, (a0, b0_) in segsT.items():
            ab = b0_ - a0
            tt = np.clip(((kco - a0) @ ab) / (ab @ ab), 0, 1)
            D.append(np.linalg.norm(kco - (a0 + tt[:, None] * ab), axis=1))
        D = np.stack(D, 1)
        Ew = 1.0 / (D + 0.02) ** KNOBS['top_env_pow']
        Ew /= Ew.sum(1, keepdims=True)
        env = np.zeros_like(W)
        for j, n in enumerate(segsT):
            env[:, bones.index(n)] = Ew[:, j]
        beta = np.clip((dist - KNOBS['top_env_lo']) / 0.02, 0, 1) * KNOBS['top_env']
        W = (1 - beta[:, None]) * W + beta[:, None] * env
        report['pieces'][piece]['top_env'] = dict(power=KNOBS['top_env_pow'], lo=KNOBS['top_env_lo'], blended_vertices=int((beta > 0.5).sum()))
    if piece == 'Bottom' and KNOBS['skirt_env'] > 0:
        # loose cloth is far from the body (a skirt hangs 30-100 mm off the thighs), so 'nearest body face' jumps between unrelated parts; its weights come from an ENVELOPE instead:
        # inverse-distance (power p) to the Hips / thigh bone segments - smooth, symmetric across the centre line, a skirt that hangs from the waist and flares over both thighs
        segs = {}
        for n in ('Hips', 'LeftUpperLeg', 'RightUpperLeg'):
            bb = rig.data.bones[n]
            segs[n] = (np.array(bb.head_local), np.array(bb.tail_local) if n != 'Hips' else np.array(rig.data.bones['Spine'].head_local))
        D = []
        for n, (a0, b0_) in segs.items():
            ab = b0_ - a0
            tt = np.clip(((kco - a0) @ ab) / (ab @ ab), 0, 1)
            D.append(np.linalg.norm(kco - (a0 + tt[:, None] * ab), axis=1))
        D = np.stack(D, 1)
        Ew = 1.0 / (D + 0.02) ** KNOBS['skirt_env_pow']
        Ew /= Ew.sum(1, keepdims=True)
        env = np.zeros_like(W)
        for j, n in enumerate(segs):
            env[:, bones.index(n)] = Ew[:, j]
        beta = np.clip((dist - 0.02) / 0.02, 0, 1) * KNOBS['skirt_env']
        W = (1 - beta[:, None]) * W + beta[:, None] * env
        report['pieces'][piece]['skirt_env'] = dict(power=KNOBS['skirt_env_pow'], blended_vertices=int((beta > 0.5).sum()))
    if piece.startswith('Shoe') and KNOBS['shoe_profile']:
        W = shoe_profile(W, kco, 'Left' if piece.endswith('_L') else 'Right')
    if piece == 'Bottom' and KNOBS['bottom_hips'] >= 0:
        # a skirt hangs from the waist: weights blend from 100 % Hips at the waist to (1 - bottom_hips) of the transferred weights at the hem
        zc = kco[:, 2]
        zt, zh = float(np.percentile(zc, 98)), float(np.percentile(zc, 2))
        t = np.clip((zt - zc) / max(zt - zh, 1e-6), 0, 1)
        sh = 1.0 - t * (1.0 - KNOBS['bottom_hips'])         # 1 at the waist, bottom_hips at the hem
        sh = sh * KNOBS['bottom_hips_gain']
        e = np.zeros_like(W)
        e[:, bones.index('Hips')] = 1.0
        W = (1 - sh[:, None]) * W + sh[:, None] * e
    cls = {'Top': 'cloth', 'Bottom': 'bottom', 'Sock_L': 'sock', 'Sock_R': 'sock', 'Shoe_L': 'shoe', 'Shoe_R': 'shoe'}[piece]
    iters = {'cloth': KNOBS['cloth_iters'], 'bottom': KNOBS['bottom_iters'], 'sock': KNOBS['sock_iters'], 'shoe': KNOBS['shoe_iters']}[cls]
    fac = {'cloth': KNOBS['cloth_factor'], 'bottom': KNOBS['bottom_factor'], 'sock': KNOBS['sock_factor'], 'shoe': KNOBS['shoe_factor']}[cls]
    W = smooth(W, ed, iters, fac)
    if KNOBS['weld_eps'] > 0:
        # coincident vertices of the kit that no edge connects (open seams, stacked rims, the lips of the double-walled hems; 0.9-1.2 mm apart) must move together: a 5 % weight difference between two
        # vertices 1 mm apart opens a 20 mm slit when the arm moves 40 cm against the torso (the female sleeve 'tear'). Weights are averaged over each cluster (union-find, <= weld_eps).
        from mathutils.kdtree import KDTree
        kd = KDTree(len(kco))
        for i_, v_ in enumerate(kco):
            kd.insert(tuple(map(float, v_)), i_)
        kd.balance()
        parent = list(range(len(kco)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        npairs = 0
        for i_, v_ in enumerate(kco):
            for (_, j_, d_) in kd.find_range(tuple(map(float, v_)), KNOBS['weld_eps']):
                if j_ > i_:
                    parent[find(j_)] = find(i_)
                    npairs += 1
        roots = np.array([find(i_) for i_ in range(len(kco))])
        Wm = np.zeros_like(W)
        cnt = np.bincount(roots, minlength=len(kco)).astype(np.float64)
        np.add.at(Wm, roots, W)
        W = Wm[roots] / cnt[roots][:, None]
        report['pieces'][piece]['weld'] = dict(eps_mm=KNOBS['weld_eps'] * 1000, pairs=npairs, clustered_vertices=int((cnt[roots] > 1).sum()))
    W = limit4(W)
    # clean vertex groups, then write
    for vg in list(src.vertex_groups):
        src.vertex_groups.remove(vg)
    groups = {}
    for j in range(len(bones)):
        if W[:, j].max() > 0:
            groups[j] = src.vertex_groups.new(name=bones[j])
    for i in range(len(W)):
        for j in np.nonzero(W[i])[0]:
            groups[int(j)].add([i], float(W[i, j]), 'REPLACE')
    order, counts = remap_materials(src, piece)
    # parent to the rig exactly like Body_*: object parent, identity inverse, armature modifier
    for m in list(src.modifiers):
        src.modifiers.remove(m)
    src.parent = rig
    src.parent_type = 'OBJECT'
    src.matrix_parent_inverse = Matrix.Identity(4)
    mod = src.modifiers.new('Armature', 'ARMATURE')
    mod.object = rig
    me.calc_loop_triangles()
    report['pieces'][piece].update(object=src.name, verts=len(kco), tris=len(me.loop_triangles), roles=order, faces_per_role=counts, smoothing=dict(cls=cls, iters=iters, factor=fac),
                                   nearest_body_distance_mm=dict(mean=float(dist.mean() * 1000), p99=float(np.percentile(dist, 99) * 1000), max=float(dist.max() * 1000)),
                                   influences_max=int((W > 0).sum(1).max()), bones_used=len(groups))
    kit_objs[piece] = src
    print(piece, report['pieces'][piece]['verts'], 'verts', report['pieces'][piece]['tris'], 'tris roles', order, 'influences<=', report['pieces'][piece]['influences_max'])

# material housekeeping
for m in list(bpy.data.materials):
    if m.users == 0:
        bpy.data.materials.remove(m)
report['materials'] = {m.name: [round(float(x), 5) for x in m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value] for m in bpy.data.materials if m.name.startswith('Kit_')}
report['triangles'] = {p: report['pieces'][p]['tris'] for p in PIECES}
report['kit_triangles_total'] = int(sum(report['triangles'].values()))
os.makedirs(DATA, exist_ok=True)
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
json.dump(report, open(f'{DATA}/build_{tag}.json', 'w'), indent=1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
print('SAVED', OUT_BLEND, os.path.getsize(OUT_BLEND))
