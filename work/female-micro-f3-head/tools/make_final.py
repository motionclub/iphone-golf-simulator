"""final MicroF2 lower-face build: rebuilt analytic chin / jaw underside / loft rows (Head2) applied to the staged mesh by sliding each vertex ONLY along its own
surface normal onto the new analytic surface (exp.mesh_normal_delta).   python3 make_final.py -> data/var_final.npz  (+ data/final_params.json)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, exp, fl
PARAMS = dict(
    # jaw underside z = zb0 + slope*(y-y0) + c(y)*x^2 (c from cx at the chin to cxb at the back), smooth-min blended with the loft wall: radius k at the midline -> k1 at the sides
    under=dict(zb0=1.4265, y0=-0.103, slope=-0.0232, cx=8.2, cxb=6.0, cy0=-0.09, cy1=-0.035, k=0.025, k1=0.028, kx=0.045),
    fb_chin_col=573.0,            # loft front plane rows 244..250: vertical chin front instead of F1's plane receding 19 mm toward the chin bottom
    prof_zcut=1.452,              # F1's profile-correction table (+15 mm clamped chin-boss hack) is zero below this height
    rows_smooth=dict(sig=0.005, rows=['a', 'yf']),     # loft half-width / front-plane rows smoothed in z (sigma 5 mm), faded out above z 1.525..1.545
    bumps=[dict(xc=0.054, sx=0.016, zc=1.472, sz=0.013, A=0.0028)],   # soft lower-cheek / jaw-body fullness: +2.8 mm peak, outboard of the lips, silhouette neutral
    zone=dict(zt=(1.500, 1.525), xc=(0.020, 0.060), zc=(1.449, 1.4575), back=(0.000, 0.035), neck_blend=(-0.090, -0.046), floor=(1.4225, 1.4265), chain_fade_mm=8.0),
)
if __name__ == '__main__':
    ctx = exp.Ctx()
    H = exp.build(under=PARAMS['under'], prof=exp.prof_nochin(PARAMS['prof_zcut']))
    exp.apply_a_smooth(H, sig=PARAMS['rows_smooth']['sig'], rows=tuple(PARAMS['rows_smooth']['rows']))
    H.bumps = PARAMS['bumps']
    Vn, D, nbad = exp.mesh_normal_delta(H, ctx, 'final', nb=PARAMS['zone']['neck_blend'])
    dn = np.linalg.norm(Vn.astype(np.float32).astype(np.float64) - ctx.V, axis=1)
    print('moved vertices:', int((dn > 0).sum()), ' max move mm %.2f' % (dn.max() * 1000), ' bracket failures', nbad)
    json.dump(PARAMS, open(fl.W / 'data/final_params.json', 'w'), indent=1)
