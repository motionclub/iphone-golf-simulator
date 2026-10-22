import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
gl = lab.gl
name = sys.argv[1]
cands = [(0.37, 0.61), (0.41, 0.58), (0.29, 0.52), (0.52, 0.33), (0.18, 0.77), (0.63, 0.44), (0.07, 0.25), (0.81, 0.12)]
for ph in cands:
    gl.PHASE[name] = ph
    d = lab.gen(name)
    worst = 0; txt = []
    for k, a in d.items():
        r = [gl.seam_ratio(a, 'u'), gl.seam_ratio(a, 'v')]
        worst = max(worst, *r); txt.append('%s %.2f/%.2f' % (k[-5], *r))
    print(ph, 'worst %.3f' % worst, ' '.join(txt))
