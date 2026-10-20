"""Fit-body registry: authority bodies + staged candidates used as extra collision references (never edited)."""
import hashlib, os, time
import numpy as np
import bpy
from kitlib import *
from sdf import Grid, body_sdf

CAND = {
    'male': [
        ('male_authority', MALE_BLEND, 'Body_M'),
        ('male_pelvis_f2', ROOT + '/work/male-pelvis-form2/export/merged_fd04bc28.blend', 'Body_M'),
    ],
    'female': [
        ('female_authority', FEMALE_BLEND, 'Body_F'),
        ('female_arms_cand', ROOT + '/work/female-arms-form2/export/HeroBase_Female_arms_candidate.blend', 'Body_F'),
        ('female_composite', ROOT + '/work/female-torso-form4/export/PREVIEW_form4_torso_plus_limbs_plus_arms_UNOFFICIAL.blend', 'Body_F'),
    ],
}
SHA = {'male_authority': MALE_SHA, 'female_authority': FEMALE_SHA,
       'female_arms_cand': '573ab4431d83f8651936f0081ad3bda9c6890c56ee5dce3061140198c9455f0e'}


def sha256(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load_set(gender, which=None):
    """list of dict(name, V, F, tree).  Verifies the authority / user-listed SHAs."""
    out = []
    for name, path, obj in CAND[gender]:
        if which is not None and name not in which:
            continue
        if name in SHA:
            s = sha256(path)
            assert s == SHA[name], f'{name}: SHA mismatch {s}'
        bpy.ops.wm.open_mainfile(filepath=path)
        V, F = mesh_arrays(bpy.data.objects[obj])
        out.append(dict(name=name, V=V, F=F, tree=bvh_from(V, F), path=path))
    return out


def cached_sdf(gender, bodies, lo, hi, h, tag, band=0.09, fit=False, mask_fn=None):
    """body SDF over a box, union of the given bodies; cached on disk keyed by the box + body names."""
    key = hashlib.md5((gender + tag + str(np.round(lo, 4)) + str(np.round(hi, 4)) + str(h) + str(band) + (('mask' + str(_FEMALE_SPLIT_Z) + str(_FEMALE_SPLIT_X)) if mask_fn is not None else '') + (('fit2z' + str(sum(b.get('fit_removed_tris', 0) for b in bodies))) if fit else '')
                       + ','.join(b['name'] for b in bodies)).encode()).hexdigest()[:10]
    fn = f'{WORK}/data/sdf_{gender}_{tag}_{key}.npy'
    g = Grid(lo, hi, h)
    if os.path.exists(fn):
        return g, np.load(fn)
    t0 = time.time()
    F = body_sdf([(b['tree_fit'] if fit else b['tree']) for b in bodies], g, band=band)
    if mask_fn is not None:
        X, Y, Z = g.coords()
        m = np.broadcast_to(mask_fn(X, Y, Z), F.shape)
        F = np.where(m, np.maximum(F, 0.03), F).astype(np.float32)
    np.save(fn, F)
    print(f'  SDF {tag} cached ({time.time()-t0:.0f}s) -> {os.path.basename(fn)}')
    return g, F


def arm_axis(V, C0, d0, iters=5, r=0.075, s_range=(0.04, 0.30), step=0.02):
    """refine an arm axis (centre line) by slab centroids of the body points near the initial line."""
    C0 = np.asarray(C0, float)
    d = unit(d0)
    for _ in range(iters):
        R = V - C0
        s = R @ d
        perp = R - np.outer(s, d)
        rr = np.linalg.norm(perp, axis=1)
        pts, ss = [], []
        for s0 in np.arange(s_range[0], s_range[1], step):
            m = (rr < r) & (s >= s0) & (s < s0 + step)
            if m.sum() > 8:
                pts.append(V[m].mean(0))
                ss.append(s0 + step / 2)
        pts = np.array(pts)
        c = pts.mean(0)
        u, sv, vt = np.linalg.svd(pts - c)
        d1 = vt[0]
        if d1 @ d < 0:
            d1 = -d1
        d = unit(d1)
        C0 = c - d * ((c - C0) @ d)          # keep C0 as the point on the line nearest the old C0
        C0 = c + d * (((np.asarray(C0) - c) @ d))
    return C0, d


# ------------------------------------------------------------------------------------------------ body segmentation helpers
def arm_vertex_mask(V, axes, r_arm, s_min):
    """axes: list of (C, d) per arm.  Body vertices within r_arm of an arm axis and beyond s_min along it."""
    m = np.zeros(len(V), bool)
    for C, d in axes:
        R = V - C
        s = R @ d
        perp = np.linalg.norm(R - np.outer(s, d), axis=1)
        m |= (perp < r_arm) & (s > s_min)
    return m


def split_trees(V, F, vmask):
    """BVHs of (mask triangles = >=2 masked verts) and the rest."""
    tm = vmask[F].sum(1) >= 2
    return bvh_from(V, F[tm]), bvh_from(V, F[~tm])


def tree_dist(tree, P):
    out = np.empty(len(P))
    for i, p in enumerate(np.asarray(P, float).tolist()):
        loc, n, idx, d = tree.find_nearest(p)
        out[i] = d if idx is not None else 1e3
    return out


def mirror_axis(C, d):
    return C * np.array([-1, 1, 1]), d * np.array([-1, 1, 1])


# ------------------------------------------------------------------------------------------------ hanging-arm exclusion (bottoms)
_FEMALE_SPLIT_Z = [0.66, 0.72, 0.80, 0.84, 0.88, 0.92, 0.96, 1.00, 1.10, 1.20]
_FEMALE_SPLIT_X = [0.205, 0.205, 0.200, 0.187, 0.177, 0.165, 0.154, 0.142, 0.150, 0.500]


def female_arm_region(X, Y, Z):
    """grid mask of the space occupied by the hanging arms/hands below the armpit (beyond the torso/arm gap midline)."""
    zz = Z[0, 0, :]
    xs = np.interp(zz, _FEMALE_SPLIT_Z, _FEMALE_SPLIT_X).astype(np.float32)[None, None, :]
    return (np.abs(X) > xs) & (Z > 0.66) & (Z < 1.19)


def fit_mask_fn(gender):
    return female_arm_region if gender == 'female' else None


LIMBS_MAP = ROOT + '/work/female-parallel-limbs/data/HeroBase_Female_limbs_vertex_map.npz'


def female_arm_vertex_mask(V, new_vertex_mask=None, zmax=1.10):
    """hanging arm/forearm vertices below the armpit (table midline between torso and arm) plus, for the staged candidates, the
    SDF-built hand vertices (exactly the vertices the limbs chat created: final_to_base == -1, away from the feet)."""
    xs = np.interp(V[:, 2], _FEMALE_SPLIT_Z, _FEMALE_SPLIT_X)
    m = (np.abs(V[:, 0]) > xs) & (V[:, 2] > 0.66) & (V[:, 2] < zmax)
    if new_vertex_mask is not None:
        m |= new_vertex_mask & (np.abs(V[:, 0]) > 0.15) & (V[:, 2] > 0.5)
    return m


def add_nohand_trees(bodies, gender='female', zmax=1.10):
    """per body: tree_fit/mesh_fit = body minus the hanging arms/hands (used to build garment fields so shells are not shaped around
    hands); tree_nohand/mesh_nohand = what the FIT gate uses (authority: the FULL body, hands must clear; candidates: hands excluded)."""
    new_mask = None
    if gender == 'female':
        f2b = np.load(LIMBS_MAP)['final_to_base']
        new_mask = f2b < 0
    for b in bodies:
        if gender == 'female':
            nm = new_mask if len(b['V']) == len(new_mask) else None
            m = female_arm_vertex_mask(b['V'], nm, zmax)
            keep = ~(m[b['F']].any(1))
            b['tree_fit'] = bvh_from(b['V'], b['F'][keep])
            b['mesh_fit'] = (b['V'], b['F'][keep])
            b['fit_removed_tris'] = int((~keep).sum())
            if b['name'] == 'female_authority':
                b['tree_nohand'], b['mesh_nohand'] = b['tree'], (b['V'], b['F'])
            else:
                b['tree_nohand'], b['mesh_nohand'] = b['tree_fit'], b['mesh_fit']
        else:
            b['tree_fit'], b['mesh_fit'] = b['tree'], (b['V'], b['F'])
            b['tree_nohand'], b['mesh_nohand'] = b['tree'], (b['V'], b['F'])
    return bodies
