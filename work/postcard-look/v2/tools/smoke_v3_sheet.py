"""smoke_v3_sheet.py <before_dir> <after_dir> <out.png>: Smoke_C before/after over a red, a grey and a dusk-sky backdrop (straight alpha composite, Blender python)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
gl = lab.gl
bd, ad, out = sys.argv[1:4]
def comp(S, bg):
    a = S[..., 3:4].astype(np.float64) / 255; c = S[..., :3].astype(np.float64) / 255
    return c * a + np.array(bg) * (1 - a)
rows = []
for tag, d in (('BEFORE (10:14)', bd), ('AFTER v3', ad)):
    S = gl.read_png(os.path.join(d, 'Smoke_C.png'))
    m = gl.smoke_metrics(S)
    cells = [lab.label(comp(S, np.array(bg) / 255), '%s OVER %s' % (tag, nm), 1) for nm, bg in (('RED 180,60,30', (180, 60, 30)), ('GREY 90,80,85', (90, 80, 85)), ('DUSK SKY', (120, 74, 98)))]
    a = S[..., 3].astype(np.float64) / 255
    cells.append(lab.label(np.repeat((a / a.max())[..., None], 3, -1), 'ALPHA NORMALISED (max %.3f)' % a.max(), 1))
    rows.append(lab.hstack(cells))
    print(tag, {k: (round(float(v), 3) if np.isscalar(v) else np.round(v, 3).tolist()) for k, v in m.items()})
lab.write(out, lab.vstack(rows)); print('wrote', out)
