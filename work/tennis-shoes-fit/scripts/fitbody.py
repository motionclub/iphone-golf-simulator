"""Fit-body registry for the TENNIS_SHOES_FIT job: ONLY the two body blends named in the brief (SHA-verified on every load, never edited)."""
import hashlib, os, time
import numpy as np
import bpy
from kitlib import *
from sdf import Grid, body_sdf

CAND = {
    'male': [('male_form3', MALE_BODY_BLEND, 'Body_M')],
    'female': [('female_full', FEMALE_BODY_BLEND, 'Body_F')],
}
SHA = {'male_form3': MALE_BODY_SHA, 'female_full': FEMALE_BODY_SHA}


def sha256(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load_set(gender, which=None):
    """list of dict(name, V, F, tree).  Verifies the SHA of the body blend before reading it (the blend itself is only read)."""
    out = []
    for name, path, obj in CAND[gender]:
        if which is not None and name not in which:
            continue
        s = sha256(path)
        assert s == SHA[name], f'{name}: SHA mismatch {s}'
        bpy.ops.wm.open_mainfile(filepath=path)
        V, F = mesh_arrays(bpy.data.objects[obj])
        out.append(dict(name=name, V=V, F=F, tree=bvh_from(V, F), path=path))
    return out


def cached_sdf(gender, bodies, lo, hi, h, tag, band=0.09, fit=False, mask_fn=None):
    """body SDF over a box (union of the given bodies), cached on disk keyed by the box + body names + their vertex hash."""
    vh = hashlib.md5(b''.join(np.ascontiguousarray(np.round(b['V'], 6)).tobytes() for b in bodies)).hexdigest()[:8]
    key = hashlib.md5((gender + tag + str(np.round(lo, 4)) + str(np.round(hi, 4)) + str(h) + str(band) + vh + ','.join(b['name'] for b in bodies)).encode()).hexdigest()[:10]
    fn = f'{WORK}/data/sdf_{gender}_{tag}_{key}.npy'
    g = Grid(lo, hi, h)
    if os.path.exists(fn):
        return g, np.load(fn)
    t0 = time.time()
    F = body_sdf([b['tree'] for b in bodies], g, band=band)
    np.save(fn, F)
    print(f'  SDF {tag} cached ({time.time()-t0:.0f}s) -> {os.path.basename(fn)}')
    return g, F
