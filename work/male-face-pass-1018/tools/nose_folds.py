"""python3 tools/nose_folds.py <params.json> ... : folded triangles (face normal flips vs the 10-17 head) and minimum triangle area ratio in the nose zone."""
import sys, json, os; ARGS=[os.path.abspath(a) for a in sys.argv[1:]]; sys.argv=['x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, nose_off as NO
G0 = NO.head({})
def tri_n(G):
    t = NO.h.tri; return np.cross(G[t[:, 1]] - G[t[:, 0]], G[t[:, 2]] - G[t[:, 0]])
n0 = tri_n(G0); a0 = np.linalg.norm(n0, axis=1)
cen = G0[NO.h.tri].mean(1); zone = (np.abs(cen[:, 0]) < 32) & (cen[:, 1] < 12) & (cen[:, 1] > -66) & (cen[:, 2] > 15)
if os.environ.get('PHIL'): zone = (np.abs(cen[:, 0]) < 14) & (cen[:, 1] < -50) & (cen[:, 1] > float(os.environ.get('PHIL_LO', -68))) & (cen[:, 2] > 25)
if os.environ.get('SIDES'): zone = (np.abs(cen[:, 0]) > 5) & (np.abs(cen[:, 0]) < 24) & (cen[:, 1] < -8) & (cen[:, 1] > -46) & (cen[:, 2] > 25)
def report(path):
    G = NO.head(json.load(open(path))); n1 = tri_n(G); a1 = np.linalg.norm(n1, axis=1)
    cos = np.einsum('ij,ij->i', n0, n1) / np.maximum(a0 * a1, 1e-12)
    fold = zone & (cos < 0); steep = zone & (cos < .5); shrink = zone & (a1 < .15 * a0)
    # creases: dihedral angle between neighbouring triangles inside the nose zone (the game keeps creases over 45 deg sharp)
    t = NO.h.tri; e = {}
    for k in np.where(zone)[0]:
        for a_, b_ in ((t[k,0],t[k,1]),(t[k,1],t[k,2]),(t[k,2],t[k,0])):
            key = (min(a_,b_),max(a_,b_)); e.setdefault(key, []).append(k)
    un = n1 / np.maximum(a1, 1e-12)[:, None]; ang = []
    for ks in e.values():
        if len(ks) == 2: ang.append(np.degrees(np.arccos(np.clip(un[ks[0]] @ un[ks[1]], -1, 1))))
    ang = np.array(ang)
    print(os.path.basename(path), 'zone tris', zone.sum(), 'FOLDS', fold.sum(), 'turned>60deg', steep.sum(), '| dihedral >20:', (ang > 20).sum(), '>30:', (ang > 30).sum(), '>45:', (ang > 45).sum(), 'mean', round(ang.mean(), 2))
    if fold.sum(): print('   fold centres', np.round(cen[fold][:8], 1).tolist())
    return fold
for a in ARGS: report(a)
