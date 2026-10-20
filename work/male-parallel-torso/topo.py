import numpy as np
from collections import defaultdict
from zone import *
ec = defaultdict(int)
for f in F:
    for k in range(len(f)):
        a, b = f[k], f[(k + 1) % len(f)]; ec[(min(a, b), max(a, b))] += 1
bd = [e for e, c in ec.items() if c == 1]; nm = [e for e, c in ec.items() if c > 2]
print('boundary edges', len(bd), 'nonmanifold', len(nm))
zb = np.array([(V0[a, 2] + V0[b, 2]) / 2 for a, b in bd]); xb = np.array([(V0[a, 0] + V0[b, 0]) / 2 for a, b in bd])
import collections
print('boundary-edge z hist (cm):', collections.Counter(np.round(zb * 100).astype(int)).most_common(20))
sel = [(a, b) for a, b in bd if 0.74 < (V0[a, 2] + V0[b, 2]) / 2 < 0.90]
print('boundary edges in z .74-.90:', len(sel))
for a, b in sel[:12]: print(np.round(V0[a], 3), np.round(V0[b], 3))
# connected components of the whole mesh
nb = neighbors(); seen = np.full(N0, -1); c = 0
for i in range(N0):
    if seen[i] >= 0 or len(nb[i]) == 0: continue
    st = [i]; seen[i] = c
    while st:
        u = st.pop()
        for w in nb[u]:
            if seen[w] < 0: seen[w] = c; st.append(w)
    c += 1
sizes = np.bincount(seen[seen >= 0]); print('components', c, 'sizes', sorted(sizes)[::-1][:6])
