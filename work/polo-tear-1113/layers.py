"""layers.py <base.bin> <export.json> [part]: how a garment of the exported hero is built.
Connected pieces, open (boundary) edges, and the share of vertices that have another layer of the same garment just behind them
(2-15 mm along their own normal, within 4 mm sideways): an inner layer that can cross the outer one when the garment is squeezed."""
import sys, json, numpy as np
from collections import defaultdict
blob = np.fromfile(sys.argv[1], dtype=np.uint8)
m = json.load(open(sys.argv[2])); name = sys.argv[3] if len(sys.argv) > 3 else "Kit_Top"
p = [q for q in m["parts"] if q["name"] == name][0]; n = p["vertexCount"]
def f32(off, cnt): return np.frombuffer(blob[off:off + cnt * 4].tobytes(), dtype=np.float32)
P = f32(p["positionOffset"], n * 3).reshape(n, 3); N = f32(p["normalOffset"], n * 3).reshape(n, 3)
tris = np.concatenate([np.frombuffer(blob[s["indexOffset"]:s["indexOffset"] + s["indexCount"] * 4].tobytes(), dtype=np.uint32) for s in p["submeshes"]]).reshape(-1, 3)
print(name, "verts", n, "tris", len(tris))
# weld by position (split normals/uvs duplicate vertices)
key = np.round(P / 1e-5).astype(np.int64); _, weld, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.ravel()
T = inv[tris]
parent = list(range(inv.max() + 1))
def find(a):
    while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
for a, b, c in T:
    for x, y in ((a, b), (b, c)):
        rx, ry = find(x), find(y)
        if rx != ry: parent[rx] = ry
roots = defaultdict(int)
for v in range(len(parent)): roots[find(v)] += 1
print("pieces (welded):", len(roots), "sizes", sorted(roots.values(), reverse=True)[:12])
edges = defaultdict(int)
for a, b, c in T:
    for x, y in ((a, b), (b, c), (c, a)): edges[(min(x, y), max(x, y))] += 1
open_e = [e for e, k in edges.items() if k == 1]; nonman = sum(1 for k in edges.values() if k > 2)
print("open edges", len(open_e), "non-manifold edges", nonman)
# layer test on welded vertices
W = P[weld]; WN = np.zeros_like(W)
for i in range(len(tris)):
    pass
# vertex normals of welded verts from exported normals (average)
acc = np.zeros((len(weld), 3)); np.add.at(acc, inv, N); WN = acc / np.maximum(1e-9, np.linalg.norm(acc, axis=1, keepdims=True))
cell = .015; grid = defaultdict(list); K = np.floor(W / cell).astype(int)
for i, k in enumerate(map(tuple, K)): grid[k].append(i)
behind = np.zeros(len(W), bool)
for i in range(len(W)):
    k = K[i]; cand = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1): cand += grid.get((k[0] + dx, k[1] + dy, k[2] + dz), [])
    c = np.array(cand); d = W[c] - W[i]; along = d @ WN[i]; side = np.linalg.norm(d - np.outer(along, WN[i]), axis=1)
    if np.any((along < -.002) & (along > -.015) & (side < .004)): behind[i] = True
print(f"vertices with a layer behind them: {behind.mean() * 100:.1f}% ({behind.sum()} of {len(W)})")
np.save(sys.argv[1] + f".{name}.outer.npy", behind)
