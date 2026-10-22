"""Connected-component probe of the right arm/hand region for both bodies (numpy only)."""
import numpy as np
from collections import deque

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/'


def components(n, tris, sel):
    sel = set(sel.tolist())
    adj = {}
    for a, b, c in tris:
        for u, v in ((a, b), (b, c), (c, a)):
            if u in sel and v in sel:
                adj.setdefault(u, set()).add(v)
                adj.setdefault(v, set()).add(u)
    seen, comps = set(), []
    for s in sel:
        if s in seen:
            continue
        q = deque([s]); seen.add(s); comp = [s]
        while q:
            u = q.popleft()
            for v in adj.get(u, ()):
                if v not in seen:
                    seen.add(v); q.append(v); comp.append(v)
        comps.append(np.array(comp))
    return comps


for tag in ('male', 'female'):
    d = np.load(W + f'data/{tag}_body.npz')
    co, tris = d['co'], d['tris']
    print('=' * 10, tag)
    # hand-ish region: right side (-x), z below 1.0 (male) / 0.80 (female), outside the legs
    if tag == 'male':
        sel = np.where((co[:, 0] < -0.50) & (co[:, 2] < 1.0))[0]
    else:
        sel = np.where((co[:, 0] < -0.215) & (co[:, 2] < 0.9))[0]
    comps = components(len(co), tris, sel)
    comps.sort(key=len, reverse=True)
    print('region verts', len(sel), 'components', [len(c) for c in comps][:12])
    for c in comps[:8]:
        P = co[c]
        print('  comp n=%d bbox min %s max %s' % (len(c), P.min(0).round(4), P.max(0).round(4)))
