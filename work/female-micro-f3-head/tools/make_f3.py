"""MicroF3 jaw build: python3 make_f3.py -> data/var_f3.npz (Body_F positions, assembled order, built on the F1 base), data/anorm_f3.npz (analytic shading normals + weights), data/f3_params.json
jaw = F2's lower-face rebuild (Head2) with the F3 smoothness fixes:
  nf_smooth   front-section exponent rows Gaussian-smoothed (sigma 10 mm): F1's piecewise-linear nf(z) had slope jumps at z 1.47 / 1.53 (= horizontal creases across the cheek)
  smin=2      jaw underside blend = exponential smooth-min (C-infinity); F1/F2's quadratic smooth-min is only C1 (curvature jumps at the blend boundary)
  s5          zone / neck / floor / chain-fade weights are quintic smootherstep (C2) so a weight times a displacement adds no curvature jump
  fit         loft half-width row a(z) (+ bowl cxb, blend k1) refitted so the front-view jaw contour follows the plate's smooth silhouette (cubic fit, rms 0.24 mm); data/fit_contour.json
  ztop 1.540  zone fades out 1.540..1.565 (F2: 1.500..1.525); eye / ear loops protected
  analytic normals: shading normals of the analytic surface blended in by the zone weight (mesh vertex normals of the 2-18 mm irregular faces gave a mottled / creased look)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np
import trial, anorm_variant, fl
KW = dict(nf_smooth=1, ztop=1.540, protect_eyes_ears=1, s5=1, smin=2, fit=1)
if __name__ == '__main__':
    Vn, ctx, H = trial.build_variant('f3', **KW)
    N, w = anorm_variant.normals_for('f3', Vn, ctx, H)
    V0 = ctx.V
    dv = np.linalg.norm(Vn.astype(np.float32).astype(np.float64) - V0, axis=1)
    print('moved vertices', int((dv > 0).sum()), 'max move mm %.2f' % (dv.max() * 1000))
    json.dump(dict(kw=KW, fit=json.load(open(fl.W / 'data/fit_contour.json')), moved=int((dv > 0).sum()), max_move_mm=float(dv.max() * 1000)), open(fl.W / 'data/f3_params.json', 'w'), indent=1)
