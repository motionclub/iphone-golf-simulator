import sys, numpy as np
sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0]); from meshbin import load
d, h = sys.argv[1], sys.argv[2]
src = load(f'{d}/mesh_{h}_src.bin'); lod = load(f'{d}/mesh_{h}_lod2.bin')
n = src['n']
# exact source index of every LOD vertex: all attributes equal
def key(m, i): return (m['pos'][i].tobytes(), m['nrm'][i].tobytes(), m['col'][i].tobytes(), *(m['uv%d' % c][i].tobytes() for c in range(5)))
idx = {}
for i in range(n): idx.setdefault(key(src, i), i)
lmap = np.array([idx[key(lod, j)] for j in range(lod['n'])])
print(h, 'src v', n, 'tris', sum(len(t) for t in src['tris']), 'lod v', lod['n'])
# duplicates by position in source: which attributes differ between copies
P = np.round(src['pos'] * 1e5).astype(np.int64)
_, pid, cnt = np.unique(P, axis=0, return_inverse=True, return_counts=True); pid = pid.ravel()
used = np.zeros(n, bool)
for t in src['tris']: used[t.ravel()] = True
print(' positions', pid.max() + 1, 'with copies', (cnt > 1).sum(), 'unused verts', (~used).sum())
first = {}
diff = {k: 0 for k in ['nrm', 'col', 'uv0', 'uv1', 'uv2', 'uv3', 'uv4']}
for i in np.where(used)[0]:
    p = pid[i]
    if p in first:
        j = first[p]
        for k in diff:
            if not np.array_equal(src[k][i], src[k][j]): diff[k] += 1
    else: first[p] = i
print(' used copies differing from first copy:', diff)
# triangles: corner copy consistency. For each LOD triangle corner (source index v at position p), the source triangles around p that
# use copy v: does the LOD triangle lie in that copy's region? Proxy: the corner copies of one LOD triangle should all co-occur in
# some source triangle fan, i.e. each LOD edge (va, vb) should exist as copy pair among source edges sharing those positions' copies.
srcEdgeCopies = set()
for t in src['tris']:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        x, y = t[:, a], t[:, b]; srcEdgeCopies.update(zip(np.minimum(x, y).tolist(), np.maximum(x, y).tolist()))
# copy-island id: connected components of source vertices via triangles (copies of one position in different islands)
parent = np.arange(n)
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for t in src['tris']:
    for a, b in ((0, 1), (1, 2)):
        for x, y in zip(t[:, a], t[:, b]):
            rx, ry = find(x), find(y)
            if rx != ry: parent[rx] = ry
comp = np.array([find(i) for i in range(n)])
for name, m in (('lod2', lod),):
    bad = 0; badT = []; total = 0
    for s, t in enumerate(m['tris']):
        T = lmap[t]
        total += len(T)
        cross = (comp[T[:, 0]] != comp[T[:, 1]]) | (comp[T[:, 1]] != comp[T[:, 2]])
        bad += cross.sum()
    print(f' {name}: triangles whose corners come from different source islands: {bad} / {total}; islands in src: {len(set(comp[used]))}')
