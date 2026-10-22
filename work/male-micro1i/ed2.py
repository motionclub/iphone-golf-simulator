"""Edit e2: ear root skirt + rim fairing.  Ear shell stays (outline, helix, concha); the head surface around it rises smoothly into the ear root."""
import sys; sys.path.insert(0, '.')
from edlib import *
import sculpt as S


def ear_dist(V):
    """signed distance (m) from the ear outline in the (y,z) side view: >0 outside, <0 inside"""
    poly = S.ear_poly()
    return S.poly_dist(V[:, 1], V[:, 2], poly)


def e2_ears(V, M, A=3.0, skirt=10.0, front_extra=0.0, taubin_iters=2, taubin_w_in=0.9, taubin_w_out=0.5, pull=0.0, top_pull=0.0, top_z=(1.576, 1.598)):
    V = V.copy()
    ax = np.abs(V[:, 0]); sgn = np.where(V[:, 0] < 0, -1.0, 1.0)
    d = ear_dist(V)                                            # m, >0 outside the outline
    side = (ax > 0.058) & (V[:, 1] > -0.075) & (V[:, 1] < 0.045) & (V[:, 2] > 1.50) & (V[:, 2] < 1.625)
    # raise: inside the outline everything is lifted by A (the ear base), outside a smooth skirt decays to 0 over `skirt` mm
    t = np.clip(d / (skirt * mm), 0.0, 1.0)
    rise = A * mm * np.where(d <= 0, 1.0, 1.0 - t * t * (3 - 2 * t))
    rise = rise * (1.0 - sstep(1.562, 1.590, V[:, 2]))            # keep the upper helix a free-standing rim: no web to the skull at the top
    # the skirt must not pull the face/jaw region: fade it out in front of the tragus root and below the lobe
    rise = rise * sstep(0.058, 0.070, ax)
    V[:, 0] += sgn * rise * side
    if pull:
        # plates disagree on ear protrusion (front: wider, 3/4: narrower): pull the crest/rear of the shell in by `pull` mm, root + rim stay attached
        w_in = np.where(d < 0, sstep(0.0, 8 * mm, -d), 0.0); w_rear = sstep(-0.014, 0.010, V[:, 1])
        V[:, 0] -= sgn * pull * mm * w_in * w_rear * side * (1.0 - sstep(1.568, 1.590, V[:, 2]))
    if top_pull:
        # the upper ear is a thin triangular fin ('webbed'): pull the top of the shell in so the helix rounds over (front hw at z~1.595 was +5 mm vs the plate)
        w_top = sstep(top_z[0], top_z[1], V[:, 2]); w_in2 = np.where(d < 0, sstep(0.0, 6 * mm, -d), 0.0)
        V[:, 0] -= sgn * top_pull * mm * w_top * w_in2 * side
    # fairing of the rim noise: weights inside the ear zone
    zone_w = np.where(d <= 0, taubin_w_in, taubin_w_out * (1.0 - sstep(0.0, 12 * mm, d))) * side * sstep(0.062, 0.072, ax)
    V = M.taubin(V, zone_w, iters=taubin_iters)
    return V


if __name__ == '__main__':
    V0, F, loops = load('e1'); M = Mesh(V0, F)
    V1 = e2_ears(V0, M)
    d = np.linalg.norm(V1 - V0, axis=1)
    print('moved verts', int((d > 1e-6).sum()), 'max mm %.2f' % (d.max() * 1000))
    np.save('data/V_e2.npy', V1)
