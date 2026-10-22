import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
import numpy as np
import female_hand as FH
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'
d = np.load(W + 'data/female_body.npz')
co, tris = d['co'], d['tris']
parts = FH.hand_parts(co, tris)
print({k: ([len(x) for x in v] if isinstance(v, list) else len(v)) for k, v in parts.items()})
idx, c, u, v, p = FH.frame_from_parts(co, parts)
print('c', c.round(4), 'u', u.round(3), 'v', v.round(3), 'p', p.round(3))
for name in ('ball', 'thumb'):
    Q = FH.to_hand(co[parts[name]], c, u, v, p)
    print(name, 'U', Q[:, 0].min().round(3), Q[:, 0].max().round(3), 'V', Q[:, 1].min().round(3), Q[:, 1].max().round(3), 'W', Q[:, 2].min().round(3), Q[:, 2].max().round(3))
for i, m in enumerate(FH.finger_models(co, parts, c, u, v, p)):
    Q = FH.to_hand(co[m['idx']], c, u, v, p)
    print('finger', i, 'M', m['M'].round(3), 'd', m['d'].round(3), 'len', round(m['length'], 3), 'U', Q[:, 0].min().round(3), Q[:, 0].max().round(3), 'V', Q[:, 1].min().round(3), Q[:, 1].max().round(3), 'W', Q[:, 2].min().round(3), Q[:, 2].max().round(3))
fa = FH.to_hand(co[parts['forearm']], c, u, v, p)
print('forearm shell U', fa[:, 0].min().round(3), fa[:, 0].max().round(3))
