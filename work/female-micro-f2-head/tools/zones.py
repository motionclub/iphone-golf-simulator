"""refinement zones (world-space predicates on face centres) driven by the feature curves"""
import numpy as np
import fl, feat_f, geo

_EYE = None; _SEAM = None; _EAR = None


def _eye():
    global _EYE
    if _EYE is None: _EYE = feat_f.eye_poly(6)
    return _EYE


def make_level_fn(H):
    eye = feat_f.eye_poly(6)
    nos = feat_f.NOSTRIL; mou = feat_f.MOUTH
    ear = H.ear.poly

    def level_fn(cen):
        x = np.abs(cen[:, 0]); y = cen[:, 1]; z = cen[:, 2]
        lvl = np.zeros(len(cen), int)
        front = y < -0.03
        lvl[front & (z > 1.425) & (z < 1.625) & (x < 0.108)] = 1
        # eyes: signed distance to the aperture polygon in the front projection
        de = feat_f.poly_signed_dist(x, z, eye)
        eye2 = front & (de > -0.007)
        eye3 = front & (np.abs(de) < 0.0028)
        nose = (x < 0.034) & (z > 1.492) & (z < 1.578) & (y < -0.095)
        mouth = (x < 0.048) & (z > 1.445) & (z < 1.502) & (y < -0.105)
        zs = H.seam_z(x)
        seam3 = (x < 0.043) & (y < -0.105) & (np.abs(z - zs) < 0.0030)
        nos3 = (np.hypot(x - nos['cx'], (z - nos['cz']) * 1.6) < 0.0050) & (y < -0.10)
        brow = front & (x > 0.012) & (x < 0.100) & (z > 1.580) & (z < 1.612)
        # ears: signed distance to the footprint polygon in the (y, z) plane
        dr = feat_f.poly_signed_dist(y, z, ear) + feat_f.EAR_DELTA
        earz = (x > 0.078) & (dr > -0.004)
        ear3 = (x > 0.078) & (dr > -0.0015) & (dr < 0.0085)
        chin2 = (y < -0.073) & (x < 0.068) & (z > 1.420) & (z < 1.505)
        lvl[eye2 | nose | mouth | earz | chin2] = 2
        lvl[brow] = np.maximum(lvl[brow], 1)
        lvl[eye3 | seam3 | nos3 | ear3] = 3
        lvl[(z < 1.448) & (y > -0.072)] = 0                      # underside behind the chin + neck junction: keep the cage cells (no fans at the pinned wall rows)
        return lvl
    return level_fn
