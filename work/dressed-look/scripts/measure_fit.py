"""CLIP / FLOAT measurement of the kit and racket on the new bodies (labels for the sheets; nothing is edited).

  blender -b --factory-startup --python measure_fit.py -- <male|female> [dressed.blend] [out.json]

Definitions (GATE_DEFS_preregistered.md): kit vertices are tested against the EVALUATED new body (pose applied) with a ray-parity inside test
(3 directions, majority vote).  Wall classification: a vertex whose normal points towards the nearest body point is on the INNER wall, otherwise OUTER.
  CLIP skin-through : outer-wall vertices inside the body by > 0.5 mm  (>= 10 vertices)
  CLIP squeezed     : inner-wall vertices inside the body by > 0.5 mm  (>= 50 vertices)
  FLOAT             : inner-wall distance to the new body exceeds its distance to the body the kit was fitted to (FitRef in the kit blend) by > 6 mm (>= 100 vertices)
  racket            : triangle overlaps racket vs body (not the hand) and racket vs kit pieces -> CLIP;  Grip-hand distance > 3 mm -> FLOAT."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dl_common import *
from handlib import edges_of, adjacency, hand_region
from mathutils.bvhtree import BVHTree

a_ = args_after_dashes()
tag = a_[0]
H = HERO[tag]
DRESSED = a_[1] if len(a_) > 1 else f"{EXPORT}/HeroBase_{H['label']}_Dressed.blend"
OUTJSON = a_[2] if len(a_) > 2 else f'{DATA}/fit_{tag}.json'
COLOR = 'White'

# ----------------------------------------------------------- FitRef (the body each kit was fitted to), read from the kit blend
with bpy.data.libraries.load(SRC[H['kit_src']], link=False) as (s, d):
    d.objects = [H['fitref']]
fr = d.objects[0]
fr_co = mesh_co(fr).astype(float)
fr_tris = mesh_tris(fr)
fr_tree = BVHTree.FromPolygons([tuple(x) for x in fr_co], [tuple(int(i) for i in t) for t in fr_tris], epsilon=0.0)

bpy.ops.wm.open_mainfile(filepath=DRESSED)
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[H['body']]
dg = bpy.context.evaluated_depsgraph_get()
body_tree = BVHTree.FromObject(body, dg)          # evaluated (armature applied); the body object transform is identity
ev = body.evaluated_get(dg)
em = ev.to_mesh()
Xb = np.empty(len(em.vertices) * 3, np.float32)
em.vertices.foreach_get('co', Xb)
em.calc_loop_triangles()
Tb = np.empty(len(em.loop_triangles) * 3, np.int64)
em.loop_triangles.foreach_get('vertices', Tb)
ev.to_mesh_clear()
Xb = Xb.reshape(-1, 3).astype(float)
Tb = Tb.reshape(-1, 3)
co_rest = mesh_co(body).astype(float)
hand_idx = hand_region(co_rest, adjacency(len(co_rest), edges_of(body.data)), tag)
is_hand = np.zeros(len(co_rest), bool)
is_hand[hand_idx] = True

DIRS = [np.array(v) / np.linalg.norm(v) for v in ((0.5773, 0.5789, 0.5741), (-0.3127, 0.8123, -0.4931), (0.7311, -0.2417, -0.6397))]


def inside(tree, p):
    votes = 0
    for dvec in DIRS:
        o = Vector(p)
        dv = Vector(dvec)
        n = 0
        for _ in range(12):
            hit = tree.ray_cast(o, dv)
            if hit[0] is None:
                break
            n += 1
            o = hit[0] + dv * 1e-5
        votes += n % 2
    return votes >= 2


def vertex_normals(V, T):
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, T[:, k], fn)
    n = np.linalg.norm(vn, axis=1, keepdims=True)
    return vn / np.maximum(n, 1e-12)


def region_name(P):
    """plain-words region of a point set (character right = world -X)."""
    c = P.mean(0)
    z0, z1 = P[:, 2].min(), P[:, 2].max()
    side = 'right' if c[0] < -0.01 else ('left' if c[0] > 0.01 else 'centre')
    zc = c[2]
    if tag == 'male':
        zones = [(0.12, 'foot / ankle'), (0.40, 'lower leg'), (0.62, 'knee / thigh'), (0.88, 'upper thigh / hip'), (1.02, 'waist / hip'), (1.35, 'chest'), (2.0, 'shoulder / neck')]
    else:
        zones = [(0.12, 'foot / ankle'), (0.38, 'lower leg'), (0.60, 'knee / thigh'), (0.85, 'upper thigh / hip'), (1.00, 'waist / hip'), (1.32, 'chest'), (2.0, 'shoulder / neck')]
    nm = next(n for z, n in zones if zc <= z)
    fb = 'front' if c[1] < -0.02 else ('back' if c[1] > 0.02 else 'side')
    return f'{side} {nm} ({fb}), z {z0:.2f}-{z1:.2f} m'


out = dict(tag=tag, dressed=DRESSED, color_measured=COLOR, pieces={}, findings=[])
flags = {}
for n, sock in piece_names(tag, COLOR):
    o = bpy.data.objects[n]
    V = mesh_co(o, world=True)
    T = mesh_tris(o)
    N = vertex_normals(V, T)
    nv = len(V)
    d_new = np.empty(nv)
    q_new = np.empty((nv, 3))
    d_ref = np.empty(nv)
    for i in range(nv):
        loc, nrm, idx, dist = body_tree.find_nearest(Vector(V[i]))
        d_new[i] = dist
        q_new[i] = loc
        d_ref[i] = fr_tree.find_nearest(Vector(V[i]))[3]
    s = np.einsum('ij,ij->i', q_new - V, N)
    inner = s > 1e-4
    outer = s < -1e-4
    # inside test only for vertices close to the body (others cannot be inside)
    ins = np.zeros(nv, bool)
    cand = np.where(d_new < 0.03)[0]
    for i in cand:
        ins[i] = inside(body_tree, V[i])
    depth = np.where(ins, d_new, 0.0)
    skin_through = outer & ins & (depth > 0.0005)
    squeezed = inner & ins & (depth > 0.0005)
    delta = d_new - d_ref
    floatv = inner & (delta > 0.006)
    out['pieces'][n] = dict(n_verts=int(nv), inner=int(inner.sum()), outer=int(outer.sum()),
                            skin_through=int(skin_through.sum()), skin_through_max_mm=float(depth[skin_through].max() * 1000) if skin_through.any() else 0.0,
                            squeezed=int(squeezed.sum()), squeezed_max_mm=float(depth[squeezed].max() * 1000) if squeezed.any() else 0.0,
                            float_verts=int(floatv.sum()), float_max_mm=float(delta[floatv].max() * 1000) if floatv.any() else 0.0,
                            inner_clearance_mm=dict(median=float(np.median(d_new[inner]) * 1000) if inner.any() else None,
                                                    p95=float(np.percentile(d_new[inner], 95) * 1000) if inner.any() else None),
                            clip_region=region_name(V[skin_through]) if skin_through.sum() >= 10 else None,
                            squeeze_region=region_name(V[squeezed]) if squeezed.sum() >= 50 else None,
                            float_region=region_name(V[floatv]) if floatv.sum() >= 100 else None)
    flags[n] = dict(V=V, skin_through=skin_through, squeezed=squeezed, floatv=floatv, depth=depth, delta=delta)
    p = out['pieces'][n]
    if p['skin_through'] >= 10:
        out['findings'].append(dict(kind='CLIP', piece=n, text=f"{n.replace('Kit_', '').replace('_White', '')}: body surface pokes through the cloth at the {p['clip_region']} ({p['skin_through']} verts, up to {p['skin_through_max_mm']:.1f} mm)"))
    if p['squeezed'] >= 50:
        out['findings'].append(dict(kind='SQUEEZE', piece=n, text=f"{n.replace('Kit_', '').replace('_White', '')}: cloth squeezed into the body at the {p['squeeze_region']} ({p['squeezed']} verts, up to {p['squeezed_max_mm']:.1f} mm)"))
    if p['float_verts'] >= 100:
        out['findings'].append(dict(kind='FLOAT', piece=n, text=f"{n.replace('Kit_', '').replace('_White', '')}: stands off the new body at the {p['float_region']} ({p['float_verts']} verts, up to {p['float_max_mm']:.1f} mm more than on the body it was fitted to)"))

# ----------------------------------------------------------- racket
rk_parts = ['Grip', 'ButtCap', 'Racket_Classic', 'StringBed']
Vr, Tr, off = [], [], 0
for nme in rk_parts:
    o = bpy.data.objects[nme]
    v_ = mesh_co(o, world=True)
    Vr.append(v_)
    Tr.append(mesh_tris(o) + off)
    off += len(v_)
Vr, Tr = np.concatenate(Vr), np.concatenate(Tr)
rtree = BVHTree.FromPolygons([tuple(map(float, x)) for x in Vr], [tuple(int(i) for i in t) for t in Tr], epsilon=0.0)
nh = ~np.any(is_hand[Tb], axis=1)
body_nohand = BVHTree.FromPolygons([tuple(x) for x in Xb], [tuple(int(i) for i in t) for t in Tb[nh]], epsilon=0.0)
body_hand = BVHTree.FromPolygons([tuple(x) for x in Xb], [tuple(int(i) for i in t) for t in Tb[~nh]], epsilon=0.0)
ov_body = rtree.overlap(body_nohand)
ov_hand = rtree.overlap(body_hand)
ov_kit = {}
for n, sock in piece_names(tag, COLOR):
    o = bpy.data.objects[n]
    V = mesh_co(o, world=True)
    T = mesh_tris(o)
    t_ = BVHTree.FromPolygons([tuple(map(float, x)) for x in V], [tuple(int(i) for i in t) for t in T], epsilon=0.0)
    ov_kit[n] = len(rtree.overlap(t_))
# which part of the racket / which body region
body_tri_ids = sorted(set(j for i, j in ov_body))
Tb_nh = Tb[nh]
reg = None
if body_tri_ids:
    P = Xb[Tb_nh[body_tri_ids]].reshape(-1, 3)
    reg = region_name(P)
# deepest racket vertex inside the body (ray parity on racket sample points that lie near the body)
dgrip = min(body_hand.find_nearest(Vector(q))[3] for q in mesh_co(bpy.data.objects['Grip'], world=True)[::2])
inside_pts = 0
max_depth = 0.0
for q in Vr[::3]:
    d = body_nohand.find_nearest(Vector(q))[3]
    if d < 0.06 and inside(body_tree, q):
        inside_pts += 1
        max_depth = max(max_depth, d)
# posed hand (evaluated) against the rest of the body and the worn kit
hand_strict = BVHTree.FromPolygons([tuple(x) for x in Xb], [tuple(int(i) for i in t) for t in Tb[np.all(is_hand[Tb], axis=1)]], epsilon=0.0)   # all 3 vertices in the hand: shares no vertex with body_nohand
hand_vs_body = len(hand_strict.overlap(body_nohand))
hand_vs_kit = {}
for n, sock in piece_names(tag, COLOR):
    o = bpy.data.objects[n]
    V = mesh_co(o, world=True)
    T = mesh_tris(o)
    t_ = BVHTree.FromPolygons([tuple(map(float, x)) for x in V], [tuple(int(i) for i in t) for t in T], epsilon=0.0)
    hand_vs_kit[n] = len(body_hand.overlap(t_))
out['hand'] = dict(posed_hand_vs_body_not_hand_tri_pairs=hand_vs_body, posed_hand_vs_kit_tri_pairs=hand_vs_kit)
for n, c in hand_vs_kit.items():
    if c > 0:
        out['findings'].append(dict(kind='CLIP', piece='Hand', text=f"Right hand passes into {n.replace('Kit_', '').replace('_White', '')} ({c} triangle pairs)"))
if hand_vs_body > 0:
    out['findings'].append(dict(kind='CLIP', piece='Hand', text=f"Right hand passes into the body ({hand_vs_body} triangle pairs)"))
out['racket'] = dict(overlap_tri_pairs_vs_body_not_hand=len(ov_body), overlap_tri_pairs_vs_hand=len(ov_hand), overlap_vs_kit=ov_kit,
                     body_region=reg, racket_samples_inside_body=inside_pts, max_depth_inside_body_mm=max_depth * 1000, grip_to_hand_min_mm=dgrip * 1000)
if len(ov_body) > 0 or inside_pts > 0:
    out['findings'].append(dict(kind='CLIP', piece='Racket', text=f"Racket passes through the {reg or 'body'} (static A-pose arm hangs flush; {len(ov_body)} triangle pairs, deepest {max_depth * 1000:.0f} mm)"))
for n, c in ov_kit.items():
    if c > 0:
        out['findings'].append(dict(kind='CLIP', piece='Racket', text=f"Racket crosses {n.replace('Kit_', '').replace('_White', '')} ({c} triangle pairs)"))
if dgrip > 0.003:
    out['findings'].append(dict(kind='FLOAT', piece='Racket', text=f"Racket grip floats {dgrip * 1000:.1f} mm off the palm"))
json.dump(out, open(OUTJSON, 'w'), indent=1, default=float)
np.savez_compressed(OUTJSON.replace('.json', '_flags.npz'), **{f'{n}__{k}': v for n, d in flags.items() for k, v in d.items()})
print('MEASURE_DONE', tag)
for f in out['findings']:
    print(' ', f['kind'], f['text'])
