"""smoke_iter.py -- iterate the Smoke_C design: generate, then predict GolfLookSmoke's numbers with smoke_model.py for the live LK_SMOKE row and variants.
  python3.13 smoke_iter.py [outdir]   (Blender's python)"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, lab, smoke_model as sm
gl = lab.gl
out = sys.argv[1] if len(sys.argv) > 1 else None
d = lab.gen('Smoke'); S = d['Smoke_C.png']
m = gl.smoke_metrics(S); print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()})
f, fS, res = sm.light_fit()
sky = sm.load_rgb('t4e_smoke_card_without.rgb').astype(float)
for lbl, tint, gain, e, lit in (('LIVE', (1, .95, .92, 1), 1.35, .40, .8), ('gain1.2', (1, .95, .92, 1), 1.2, .40, .8), ('gain1.45', (1, .95, .92, 1), 1.45, .40, .8),
                               ('t4e', (1, .95, .92, 1), 1.30, .30, .8), ('selflight.25', (1, .95, .92, 1), 1.35, .25, .8), ('t2-style', (.62, .56, .56, 1), 1.0, .05, .6)):
    G = sm.G_for(lit, e, f, fS)
    fr, al = sm.render(S, sky, tint, gain, e, lit, G=G, A=np.zeros(3))
    st = sm.stats(fr, sky)
    print('%-13s alpha max %.3f  N %6d  median %5.1f  p99 %5.1f  grad %4.2f' % (lbl, al.max(), st['N'], st['med'], st['p99'], st['grad']))
if out:
    os.makedirs(out, exist_ok=True)
    G = sm.G_for(.8, .40, f, fS)
    fr, al = sm.render(S, sky, (1, .95, .92, 1), 1.35, .40, .8, G=G, A=np.zeros(3))
    np.save(os.path.join(out, 'frame.npy'), fr)
    a = S[..., 3].astype(float) / 255; c = S[..., :3].astype(float) / 255
    red = np.array([180, 60, 30]) / 255; gry = np.array([90, 80, 85]) / 255
    tiles = [c * a[..., None] + bg * (1 - a[..., None]) for bg in (red, gry)]
    crop = fr[450:1000, 150:750].astype(float) / 255
    ys = (np.arange(512) * crop.shape[0] / 512).astype(int); xs = (np.arange(512) * crop.shape[1] / 512).astype(int)
    tiles.append(crop[ys][:, xs]); tiles.append(np.repeat((a / max(a.max(), 1e-6))[..., None], 3, -1))
    lab.write(os.path.join(out, 'smoke_iter.png'), np.concatenate(tiles, 1)) if hasattr(lab, 'write') else None
