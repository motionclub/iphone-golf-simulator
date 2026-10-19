"""Tennis tank: follow the torso skin underneath it (construction inputs only, no poses).

Why: the body's front chest / axilla skin carries part of the upper-arm weight
(pectoral pull). The tank was bound to a torso-only palette, so whenever an arm
rises (serve, overhead, emotes) the chest skin travels ~35 mm with the arm and
pushes through the cloth. Each tank vertex now takes the weights of the nearest
TORSO skin (never arm skin, so the hem cannot bind to a hanging arm), with the
runtime arm-volume support bones folded back into their two parent bones
exactly (HeroArmSkinning rebuilds the same dual-quaternion blend on the tank at
runtime, see MatchHeroLook). Layers share one smoothed field.

Blender -b --factory-startup --python bind_tank_follow.py
"""
from pathlib import Path
import json, re, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r = Path(__file__).resolve().parent; sys.path.insert(0, str(r.parent / 'clothing-v2/py'))
import cv2io, glib as G
cv2io.DUMP = str(r / 'dump-polo'); h = cv2io.Hero('MatchHero_Female'); body = h.body; B = body.bones
u = r / 'out/MatchHero_Female/unity'
# Source = the pattern export (torso-only binding), kept so this step is repeatable.
g = dict(np.load(r / 'cage-prototype/tennis-export-top.npz')); p = g['pos']; n = len(p); tri = g['tri']
manifest = json.loads((r / 'cage-prototype/tennis-export-manifest.json').read_text()); piece = next(x for x in manifest['pieces'] if x['name'] == 'Kit_Top')
assert np.allclose(np.load(u / 'Kit_Top_final.npz')['pos'], p), 'export changed: refresh cage-prototype/tennis-export-top.npz'
ALPHA = float(__import__('os').environ.get('TANK_FOLLOW', '1'))   # share of the skin-follow field
old_bind = np.asarray(piece['bindposes']).reshape(-1, 16)
for name, m in zip(piece['bones'], old_bind):
    assert np.allclose(body.bind[B.index(name)].T.reshape(-1), m, atol=1e-5), 'tank bindposes are not this hero dump: ' + name

# Original (pre arm-volume) body weights: support bone ArmBlend_a_b_k is the
# exact k/8 split between a and b (HeroArmSkinning.Initialize, Steps=8).
Wb = np.zeros((len(body.pos), len(B)))
for k in range(4): np.add.at(Wb, (np.arange(len(body.pos)), body.bi[:, k]), body.bw[:, k])
for j, name in enumerate(B):
    m = re.fullmatch(r'ArmBlend_(\d+)_(\d+)_(\d+)', name)
    if not m: continue
    a, b, s = (int(x) for x in m.groups())
    Wb[:, a] += Wb[:, j] * (1 - s / 8); Wb[:, b] += Wb[:, j] * (s / 8); Wb[:, j] = 0
ALLOWED = ['Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'LeftShoulder', 'RightShoulder', 'LeftUpperArm', 'RightUpperArm']
idx = [B.index(x) for x in ALLOWED]
torso_core = [B.index(x) for x in ['Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'LeftShoulder', 'RightShoulder']]
# Transfer target: torso skin only (core torso share >= 0.6).
torso_v = Wb[:, torso_core].sum(1) >= .6
faces = body.tri[torso_v[body.tri].all(1)]
tree = BVHTree.FromPolygons([tuple(x) for x in body.pos], [tuple(t) for t in faces], all_triangles=True)
T = np.zeros((n, len(ALLOWED)))
for i in range(n):
    q, _, fi, _ = tree.find_nearest(Vector(p[i]))
    a, b, c = body.pos[faces[fi]]; q = np.array(q)
    v0, v1, v2 = b - a, c - a, q - a; d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01 or 1e-20; bv = (d11 * d20 - d01 * d21) / den; bw = (d00 * d21 - d01 * d20) / den
    bc = np.clip(np.array([1 - bv - bw, bv, bw]), 0, 1); bc /= bc.sum()
    T[i] = bc @ Wb[faces[fi]][:, idx]
T /= np.maximum(T.sum(1, keepdims=True), 1e-12)
# One field for all layers: light smoothing over the welded all-layer graph (~1 cm;
# the barycentric transfer is already continuous, heavier smoothing halves the pectoral share).
uq, inv = np.unique(np.round(p, 5), axis=0, return_inverse=True); inv = inv.ravel()
E = np.sort(inv[np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])], 1); E = np.unique(E[E[:, 0] != E[:, 1]], axis=0)
s, d = np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]]; cond = 1 / np.maximum(np.linalg.norm(uq[s] - uq[d], axis=1), .002)
deg = np.bincount(s, weights=cond, minlength=len(uq))
Tu = np.zeros((len(uq), len(ALLOWED))); np.add.at(Tu, inv, T); Tu /= np.bincount(inv, minlength=len(uq))[:, None]
for _ in range(4):
    mean = np.stack([np.bincount(s, weights=cond * Tu[d, c], minlength=len(uq)) for c in range(len(ALLOWED))], 1) / np.maximum(deg, 1e-12)[:, None]
    Tu = .5 * Tu + .5 * mean
T = Tu[inv]; T /= T.sum(1, keepdims=True)
W = np.zeros((n, len(B))); W[:, idx] = T
W0 = np.zeros((n, len(B)))
for k in range(4): np.add.at(W0, (np.arange(n), g['bi'][:, k]), g['bw'][:, k])
# Armhole edges keep the torso binding: an edge that follows the arm swings
# open over the back / side skin (overhead, run arm-swing). Blend 1 -> 4 cm.
uw, iw = np.unique(np.round(p, 5), axis=0, return_inverse=True); iw = iw.ravel()   # sewn (welded) outer shell
wt = iw[tri[g['part'] == 0]]; wt = wt[(wt[:, 0] != wt[:, 1]) & (wt[:, 1] != wt[:, 2]) & (wt[:, 0] != wt[:, 2])]
loops = [l for l in G.boundary_loops(wt) if len(l) > 20]
# Armhole rims: every open edge of the sewn shell lateral of |x| .08 (neck/hem are central).
ring = np.concatenate([uw[l] for l in loops]); ring = ring[np.abs(ring[:, 0]) > .08]
assert len(ring) > 100 and (ring[:, 0] > 0).any() and (ring[:, 0] < 0).any(), 'armhole rims not found'
from mathutils.kdtree import KDTree
kd = KDTree(len(ring))
for i, q in enumerate(ring): kd.insert(Vector(q), i)
kd.balance()
dist = np.array([kd.find(Vector(q))[2] for q in p])
t = np.clip((dist - .01) / .03, 0, 1); fade = t * t * (3 - 2 * t)
A = ALPHA * fade[:, None]
W = A * W + (1 - A) * W0
bi, bw = G.prune(W, 4); g['bi'] = bi; g['bw'] = bw
used = sorted(set(np.unique(bi[bw > 0]).tolist()) | set(B.index(x) for x in piece['bones']), key=lambda i: idx.index(i))
piece['bones'] = [B[i] for i in used]; piece['bindposes'] = [float(v) for i in used for v in body.bind[i].T.reshape(-1)]
remap = np.zeros(len(B), int)
for k, i in enumerate(used): remap[i] = k
np.savez(u / 'Kit_Top_final.npz', **g); (u / 'manifest.json').write_text(json.dumps(manifest))
with (u / 'Kit_Top.bin').open('wb') as f:
    for arr in [p.astype(np.float32), g['nrm'].astype(np.float32), g['uv'].astype(np.float32), remap[bi].astype(np.int32), bw.astype(np.float32), tri.astype(np.int32)]: f.write(arr.tobytes())
arm = W[:, [B.index('LeftUpperArm'), B.index('RightUpperArm')]].sum(1)
print('tank follow binding (alpha %.2f): palette' % ALPHA, piece['bones'], '; upper-arm share max %.2f, verts >0.05: %d, below z1.10 max %.3f; zero animation inputs'
      % (arm.max(), (arm > .05).sum(), arm[p[:, 2] < 1.10].max()))
