import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lab
gl = lab.gl
out = sys.argv[1]
if len(sys.argv) > 2:
    gl.BASALT_P.update(json.loads(sys.argv[2]))
d = lab.gen('Basalt')
C, N, E = d['Basalt_C.png'], d['Basalt_N.png'], d['Basalt_E.png']
lp = gl.lit_preview(C, N, E)
one = lab.fit(lp, 1024)
tile3 = lab.fit(lab.tile(lp, 3), 1024)
alb3 = lab.fit(lab.tile(lab.f01(C), 3), 640)
nrm = lab.fit(lab.f01(N), 640)
em = lab.fit(lab.f01(E), 640)
top = lab.hstack([lab.label(one, 'BASALT LIT 1X (WARM KEY, ABOVE-LEFT)'), lab.label(tile3, 'BASALT LIT 3X3')])
bot = lab.hstack([lab.label(alb3, 'ALBEDO 3X3'), lab.label(nrm, 'NORMAL'), lab.label(em, 'EMISSION')])
lab.write(out, lab.vstack([top, bot]))
print('wrote', out)
nl = N.astype(np.float32) / 255 * 2 - 1
el = gl.lum(E.astype(np.float32) / 255)
print('glow frac (lum>.05) %.3f ; (lum>.15) %.3f ; E max' % ((el > .05).mean(), (el > .15).mean()), E.reshape(-1,3).max(0), ' |nx| bevel share %.3f' % (((np.abs(nl[...,0]) > .3) & (np.abs(nl[...,0]) < .55)).mean()))
