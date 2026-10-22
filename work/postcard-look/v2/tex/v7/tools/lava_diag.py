import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
aa = None
for kv in sys.argv[1:]:
    if kv.startswith('--aa='):
        g.LAVA_AA = tuple(tuple(float(x) for x in lv.split(',')) for lv in kv[5:].split(';')); continue
    k, v = kv.split('=')
    g.LAVA_P[k] = tuple(int(x) for x in v.split(',')) if ',' in v else float(v)
F0 = g.lava_fields()
hh0 = F0['hh']; print('raw stage-1 heat gradient p99.9 per ss texel %.3f (per out texel %.3f)' % (np.percentile(np.maximum(np.abs(np.roll(hh0,-1,1)-hh0),np.abs(np.roll(hh0,-1,0)-hh0)),99.9), 2*np.percentile(np.maximum(np.abs(np.roll(hh0,-1,1)-hh0),np.abs(np.roll(hh0,-1,0)-hh0)),99.9)))
ss = 2
hh, crust, seam = [g.ssdown(a_, ss) for a_ in g.lava_design(F0)]
r = g.lava_encode(F0, g.LAVA_ENC['alpha'], list(g.LAVA_ENC['lut']))
C, E, N = g.enc(r['C']), g.enc(r['E']), g.enc_normal(r['N'])
sp = g.lava_spec(); h_, rgb = g.lava_shader_model(C, E, N, sp)
L = g.lum(rgb.astype(np.float32) / 255) * 255
gg = np.maximum(np.abs(np.roll(L, -1, 1) - L), np.abs(np.roll(L, -1, 0) - L))
thr = np.percentile(gg, 99.9)
top = gg >= thr
print('thr', thr, 'n', top.sum())
cedge = (crust > 0.05) & (crust < 0.95)
print('share of the top 0.1%% that is: crust edge %.2f, inside seam(>.05) %.2f, crust>0.95 %.2f, molten (crust<.05, seam<.05) %.2f' % (
    (top & cedge).sum() / top.sum(), (top & (seam > .05)).sum() / top.sum(), (top & (crust >= .95)).sum() / top.sum(), (top & (crust <= .05) & (seam <= .05)).sum() / top.sum()))
top2 = gg >= np.percentile(gg, 99)
print('top 1%%: crust edge %.2f, seam %.2f, molten %.2f' % ((top2 & cedge).sum() / top2.sum(), (top2 & (seam > .05)).sum() / top2.sum(), (top2 & (crust <= .05) & (seam <= .05)).sum() / top2.sum()))
# gradient of components: heat part vs relief part
lw = np.array([0.2126, 0.7152, 0.0722])
c = C.astype(np.float64) / 255; e = E.astype(np.float64) / 255
cg = (c @ lw) * 255; eg = (e @ lw) * 255
def gmag(x): return np.maximum(np.abs(np.roll(x, -1, 1) - x), np.abs(np.roll(x, -1, 0) - x))
print('p99.9 gradient: lum(C) %.1f, lum(E) %.1f, heat %.3f, relief term %.3f' % (np.percentile(gmag(cg), 99.9), np.percentile(gmag(eg), 99.9), np.percentile(gmag(h_), 99.9),
      np.percentile(gmag(((N[..., 0].astype(np.float64) / 255 * 2 - 1) + (N[..., 1].astype(np.float64) / 255 * 2 - 1)) * 0.5 * sp['Relief']), 99.9)))
print('design heat grad p99.9 (per out texel) %.3f, crust %.3f' % (np.percentile(gmag(hh), 99.9), np.percentile(gmag(crust), 99.9)))
# save a map of top-gradient texels over the shader image
img = rgb.astype(np.uint8).copy(); img[gg >= thr] = (255, 255, 255)
g.write_png(os.path.join(HERE, '..', 'lava_diag_top.png'), img)
