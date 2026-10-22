"""lava_v3.py -- v3 (2026-10-04) lava fitting + shader-model report. Run with Blender's python3.13 (numpy).
  lava_v3.py cache                      compute the stage-1 design fields once (64 MB npz in $LAVA_CACHE, default <tmp>/golf_lava_fields.npz; ~6 s)
  lava_v3.py try ALPHA LUT              encode with albedo share ALPHA and the 11 comma-separated LUT knots (design heat at 0,.1,..1 -> tone-curved heat), print the report
  lava_v3.py fit ALPHA [ITERS]          rank-match the tone curve so the GolfLava shader heat histogram (live GolfLook.cs constants) follows crater.jpg's pool
                                        (D_RHO/D_HEAT below); prints the fitted LUT (bake it into LAVA_ENC in golf_look_textures.py)
The report is golf_look_textures.lava_report(): the shipped GolfLava shader model under the live and an earlier bias/gain, and the URP Lit fallback.
Example (the baked result): lava_v3.py try 0.25 0,0.1,0.258,0.275,0.348,0.415,0.526,0.61,0.669,0.70,0.84
"""
import importlib.util, os, sys, time, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sp_ = importlib.util.spec_from_file_location('g', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(sp_); sp_.loader.exec_module(g)
CACHE = os.environ.get('LAVA_CACHE', os.path.join(tempfile.gettempdir(), 'golf_lava_fields.npz'))   # never inside the repo


def fields():
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        return dict(hh=z['hh'], crust=z['crust'], pu=z['pu'], pv=z['pv'], N=1024, seed=1201, ss=2)
    t = time.time(); F = g.lava_fields(); np.savez(CACHE, hh=F['hh'], crust=F['crust'], pu=F['pu'], pv=F['pv']); print('stage 1 %.1fs' % (time.time() - t)); return F


# crater.jpg's pool in ramp terms (heat under the live GolfLook.cs ramp; ref_lava_crop.png projected on the ramp polyline): p50 .44, p75 .71, p90 .94, ~11 % > .9;
# ~12 % crust. Target quantile function of the heat over ALL texels (rho -> heat); the crust texels keep their own (low) heat.
D_RHO = [0.0, 0.12, 0.25, 0.50, 0.75, 0.90, 0.97, 1.0]
D_HEAT = [0.0, 0.157, 0.28, 0.44, 0.68, 0.90, 0.98, 1.0]


def fit(alpha, iters=6, lut=None):
    F0 = fields(); sp = g.lava_spec()
    hh, crust, seam = [g.ssdown(a_, 2) for a_ in g.lava_design(F0)]
    mol = (crust < 0.03) & (seam < 0.03)
    X = np.array(g.LAVA_LUT_X); lut = list(X if lut is None else lut)
    for it in range(iters):
        r = g.lava_encode(F0, alpha, lut)
        C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
        H = g.lava_shader_model(C, E, N, sp)[0]
        Hs = np.sort(H.ravel())
        newlut = list(lut)
        for k, x in enumerate(X):
            sel = mol & (np.abs(hh - x) < 0.02)
            if sel.sum() < 300:
                continue
            hk = float(np.median(H[sel])); rho = float(np.searchsorted(Hs, hk) / Hs.size)
            tk = float(np.interp(rho, D_RHO, D_HEAT))
            newlut[k] = lut[k] + (tk - hk) / 2.2 * 0.8       # assumed slope d heat / d lut ~ 2.2 (the shader's gain x the maps' response), damped
        newlut[0] = 0.0
        for k in range(1, len(newlut)):
            newlut[k] = float(np.clip(max(newlut[k], newlut[k - 1] + 0.004), 0, 1.0))
        print('it', it, 'lut', [round(v, 3) for v in newlut], flush=True)
        lut = newlut
    r = g.lava_encode(F0, alpha, lut)
    print(g.lava_report(g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N']), sp))
    return lut


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'cache':
        fields()
    elif cmd == 'try':
        F = fields(); r = g.lava_encode(F, float(sys.argv[2]), [float(x) for x in sys.argv[3].split(',')])
        print(g.lava_report(g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N']), g.lava_spec()))
    elif cmd == 'fit':
        print('FINAL', [round(v, 3) for v in fit(float(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 6)])
