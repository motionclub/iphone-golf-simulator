import os, sys, itertools, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, lab, smoke_model as sm
gl = lab.gl
f, fS, _ = sm.light_fit(); sky = sm.load_rgb('t4e_smoke_card_without.rgb').astype(float)
G = sm.G_for(.8, .40, f, fS)
def run(over, tag=None, out=None):
    gl.SMOKE_P.update(over)
    S = lab.gen('Smoke')['Smoke_C.png']
    m = gl.smoke_metrics(S)
    fr, al = sm.render(S, sky, (1, .95, .92, 1), 1.35, .40, .8, G=G, A=np.zeros(3)); st = sm.stats(fr, sky)
    print('%-60s aspect %.2f cover %.2f grad %.3f | eff %.3f med %5.1f p99 %5.1f g %.2f' % (json.dumps(over), m['aspect'], m['cover'], m['grad'], al.max(), st['med'], st['p99'], st['grad']))
    return S, fr
if __name__ == '__main__':
    base = dict(gl.SMOKE_P)
    for over in ({}, dict(curl=.03), dict(curl=.03, w0=.08, w1=.12), dict(curl=.03, w0=.075, w1=.11, expo=1.8), dict(curl=.03, w0=.07, w1=.10, expo=1.8, y_in=(.10, .26), y_out=(.66, .88))):
        gl.SMOKE_P.clear(); gl.SMOKE_P.update(base); run(over)
