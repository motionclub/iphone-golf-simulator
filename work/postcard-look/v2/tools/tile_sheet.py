import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
gl = lab.gl
name = sys.argv[1]; out = sys.argv[2]
d = lab.gen(name)
C = d[name + '_C.png']; N = d.get(name + '_N.png')
t3 = lab.fit(lab.tile(lab.f01(C), 3), 960)
parts = [lab.label(t3, name + ' ALBEDO 3X3')]
if N is not None:
    lp = gl.lit_preview(C, N)
    parts.append(lab.label(lab.fit(lab.tile(lp, 3), 960), name + ' LIT 3X3'))
lab.write(out, lab.hstack(parts))
print('wrote', out)
