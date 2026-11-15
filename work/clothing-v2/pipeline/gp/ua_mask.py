"""ua_mask.py <candidate Kit_Top.npz> <out.npy> [threshold]: 0..1 mask over his polo where today's OR the candidate's weights use the
shoulder / upper-arm bones (incl. the ArmBlend helpers between chest, shoulder and upper arm), smoothed (11-14 polo underarm)."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, rig, scene, graph as GR
h = rig.Hero('MatchHero_Male'); it = [i for i in scene.items_from_dump(h) if i.tag == 'Kit_Top'][0]
z = np.load(sys.argv[1]); thr = float(sys.argv[3]) if len(sys.argv) > 3 else .15
core = {7, 8, 26, 27}
arm = np.zeros(len(h.bones), bool)
for g, b in enumerate(h.bones):
    m = re.match(r'ArmBlend_(\d+)_(\d+)_', b)
    arm[g] = g in core or bool(m and ({int(m.group(1)), int(m.group(2))} & core))
def armw(bi, bw): return (bw * arm[bi]).sum(1)
gt = it.gidx[it.bi] if it.gidx is not None else it.bi
a = np.maximum(armw(gt, it.bw), armw(z['bi'], z['bw']))
m = np.clip(a / thr, 0, 1); m = m * m * (3 - 2 * m)
m = GR.Graph(it.P, it.tri).smooth(m[:, None], 8)[:, 0]
np.save(sys.argv[2], m.astype(np.float32))
print('mask: %d of %d vertices > .5, %d > .05' % ((m > .5).sum(), len(m), (m > .05).sum()))
