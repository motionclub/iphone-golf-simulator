"""Micro1l light-stubble EXAMPLE (preview only, not part of the mesh/gate): per-vertex stubble weight following FACE_SPEC 10 (jaw, chin, upper-lip shadow; no random cheek patches / full beard).
w = 1 on chin + jaw, fading up the cheek (to 0 about 44 mm above the mandible arc), a soft dusting on the neck just under the jaw, a moustache zone under the nose, never on lips/eyes/ears/nose."""
import sys
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *
import l_jaw as J


def stubble_weight(ctx, V):
    Ng = vertex_normals(V, ctx.F); Nd = J.smooth_normals(ctx, Ng, 8)
    ax = np.abs(V[:, 0]) * 1000.0; z = V[:, 2]; y = V[:, 1]
    sm = np.full(ctx.n, 99.0)
    for side in (1, -1):
        s, t, _ = J.euclid_field(ctx, V, Nd, side, band=0.085, xmin=-0.03)
        ok = np.isfinite(s) & (V[:, 0] * side > -0.03)
        smm = np.where(ok, s * 1000.0, 99.0)
        sel = ok & ((np.abs(smm) < np.abs(sm)) | (sm == 99.0)); sm[sel] = smm[sel]
    w_face = sstep(-1.0, 5.0, sm) * (1.0 - sstep(18.0, 54.0, sm))
    w_neck = np.where(sm < 0, 0.55 * (1.0 - sstep(0.0, 16.0, -sm)), 0.0)
    w = np.maximum(w_face, w_neck)
    # moustache zone (under the nose, above the upper vermilion) and chin front
    seam = np.interp(np.abs(V[:, 0]), *(lambda S: (np.sort(np.abs(S[:, 0])), S[np.argsort(np.abs(S[:, 0])), 2]))(ctx.V0[np.array(ctx.loops['LOOP_mouth_seam'])]))
    dzs = (z - seam) * 1000.0
    w_must = 0.85 * sstep(8.5, 11.5, dzs) * (1 - sstep(24.0, 28.0, dzs)) * (1 - sstep(20.0, 30.0, ax))
    w = np.maximum(w, w_must)
    # keep clear of lips / nostrils / eyes / ears and the upper cheek
    ones = np.ones(ctx.n)
    w *= sstep(1.0 * mm, 5.0 * mm, ctx.dist['mouth']) * sstep(3.0 * mm, 8.0 * mm, ctx.dist['nose']) * sstep(12 * mm, 24 * mm, ctx.dist['eye']) * sstep(8 * mm, 16 * mm, ctx.dist['ear'])
    w *= (1.0 - sstep(1.545, 1.562, z)) * (V[:, 1] < 0.0 + 0.0) * 1.0 + 0.0 * ones
    w[~ctx.zone] = 0.0
    # mouth interior band between the lips stays clean (paint); also soften with two umbrella passes so the boundary has no vertex-scale noise
    for _ in range(2): w = 0.5 * w + 0.5 * ctx.M.nbr_mean(w[:, None])[:, 0]
    return np.clip(w, 0, 1)


if __name__ == '__main__':
    tag = sys.argv[1]
    ctx = LCtx(); V = np.load(W / f'data/V_{tag}.npy')
    w = stubble_weight(ctx, V); np.save(W / f'data/W_stubble_{tag}.npy', w)
    print('stubble weight: verts >0.05:', int((w > 0.05).sum()), ' mean over those %.2f' % w[w > 0.05].mean())
