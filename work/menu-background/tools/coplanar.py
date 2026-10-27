#!/usr/bin/env python3
"""Z-fighting finder: faces of the plaza that share a plane (same facing, within --tol metres) and overlap by more than
--min-area m², read from MenuBackgroundCapture's meshes.bin (world-space triangles of an unbatched plaza build).
Two front faces in the same plane draw in whichever order the depth test happens to resolve that frame: the menu's camera
drift flips it pixel by pixel (the flicker). Faces pointing away from the menu cameras (normal.z > .3, i.e. facing north,
seen only from behind) are skipped unless --all.

  coplanar.py meshes.bin [--tol .0015] [--min-area .0004] [--all]
Prints one line per overlapping pair group: where, the two materials, overlap area; and a summary count."""
import struct, sys, argparse, collections
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("bin"); ap.add_argument("--tol", type=float, default=.0015)
ap.add_argument("--min-area", type=float, default=.0004); ap.add_argument("--all", action="store_true")
ap.add_argument("--skip", default="Hub player,Hub life,Rendered,Sky,Sea,Island,Collider")
a = ap.parse_args()
skip = [s for s in a.skip.split(",") if s]

f = open(a.bin, "rb").read(); o = 0
def r(fmt):
    global o; v = struct.unpack_from(fmt, f, o); o += struct.calcsize(fmt); return v
tris = []   # (p0, p1, p2, label)
n, = r("<i")
for _ in range(n):
    l, = r("<i"); name = f[o:o + l].decode(); o += l
    nv, = r("<i"); V = np.frombuffer(f, np.float32, nv * 3, o).reshape(-1, 3).astype(np.float64); o += 12 * nv
    sm, = r("<i")
    for _ in range(sm):
        l, = r("<i"); mat = f[o:o + l].decode(); o += l
        ni, = r("<i"); I = np.frombuffer(f, np.int32, ni, o).reshape(-1, 3); o += 4 * ni
        if any(s in name for s in skip): continue
        for t in I: tris.append((V[t[0]], V[t[1]], V[t[2]], name.replace("Mesh dump/", "") + " [" + mat + "]"))
print("triangles", len(tris))

P = np.array([[t[0], t[1], t[2]] for t in tris])          # (n,3,3)
N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); area = np.linalg.norm(N, axis=1) / 2
ok = area > 1e-7; N[ok] /= (2 * area[ok])[:, None]
D = np.einsum("ij,ij->i", N, P[:, 0])

def clip(poly, a_, b_):
    # keep the part of convex poly on the left of edge a->b (2D)
    out = []
    def side(p): return (b_[0] - a_[0]) * (p[1] - a_[1]) - (b_[1] - a_[1]) * (p[0] - a_[0])
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]; sp, sq = side(p), side(q)
        if sp >= 0: out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq); out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out
def area2(poly):
    s = 0
    for i in range(len(poly)): x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]; s += x0 * y1 - x1 * y0
    return abs(s) / 2
def overlap(i, j, u, v):
    A = [(np.dot(p, u), np.dot(p, v)) for p in P[i]]; B = [(np.dot(p, u), np.dot(p, v)) for p in P[j]]
    if area2(A) == 0 or area2(B) == 0: return 0
    # orient both counter-clockwise
    def ccw(T):
        (x0, y0), (x1, y1), (x2, y2) = T
        return T if (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0) > 0 else [T[0], T[2], T[1]]
    A, B = ccw(A), ccw(B); poly = A
    for k in range(3):
        poly = clip(poly, B[k], B[(k + 1) % 3])
        if not poly: return 0
    return area2(poly)

# bucket by quantised normal and plane offset (neighbouring offset cells checked too)
q = .02; dq = a.tol * 2
buckets = collections.defaultdict(list)
for i in np.nonzero(ok)[0]:
    if not a.all and N[i][2] > .3: continue
    key = (round(N[i][0] / q), round(N[i][1] / q), round(N[i][2] / q), int(np.floor(D[i] / dq)))
    buckets[key].append(i)
pairs = collections.defaultdict(float); where = {}; cl = {}
keys = list(buckets)
for key in keys:
    nx, ny, nz, dk = key
    cand = buckets[key] + buckets.get((nx, ny, nz, dk + 1), [])
    if len(cand) < 2: continue
    own = set(buckets[key])
    for ii, i in enumerate(cand):
        if i not in own: continue
        n_ = N[i]; u = np.cross(n_, [0, 1, 0] if abs(n_[1]) < .9 else [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(n_, u)
        lo_i, hi_i = P[i].min(0), P[i].max(0)
        for j in cand:
            if j <= i and j in own: continue
            if np.dot(N[i], N[j]) < .999 or abs(D[i] - D[j]) > a.tol: continue
            lo_j, hi_j = P[j].min(0), P[j].max(0)
            if (lo_i > hi_j + 1e-4).any() or (lo_j > hi_i + 1e-4).any(): continue
            ov = overlap(i, j, u, v)
            if ov > 1e-6:
                k = tuple(sorted((tris[i][3], tris[j][3])))
                pairs[k] += ov
                c = (P[i].mean(0) + P[j].mean(0)) / 2; cl.setdefault(k, collections.defaultdict(float))[tuple(np.round(c / .75).astype(int))] += ov
                lo, hi = np.minimum(P[i].min(0), P[j].min(0)), np.maximum(P[i].max(0), P[j].max(0))
                if k in where: lo, hi = np.minimum(lo, where[k][0]), np.maximum(hi, where[k][1])
                where[k] = (lo, hi, N[i])
bad = [(k, ar) for k, ar in pairs.items() if ar >= a.min_area]
bad.sort(key=lambda x: -x[1])
for (m1, m2), ar in bad:
    lo, hi, nn = where[(m1, m2)]
    for cc, car in sorted(cl[(m1, m2)].items(), key=lambda x: -x[1])[:6]:
        if car >= a.min_area: print("        %.4f m² near (%.1f, %.1f, %.1f)" % (car, cc[0] * .75, cc[1] * .75, cc[2] * .75))
    print("%7.4f m²  box (%.2f,%.2f,%.2f)-(%.2f,%.2f,%.2f) n (%.2f,%.2f,%.2f)  %s  <->  %s" % (ar, *lo, *hi, *nn, m1, m2))
print("COPLANAR_OVERLAPS %d (tol %.4f m, min area %.4f m²)" % (len(bad), a.tol, a.min_area))
