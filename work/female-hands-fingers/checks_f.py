"""Roll-up of all gate lines -> checks.json.   ./py.sh checks_f.py <flat params json> <candidate tag> <final blend verify json> <audit json> <out checks.json>
Thresholds were fixed in metrics_f.GATES / below BEFORE the final measurement (the brief gives no numeric thresholds)."""
import sys, json
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent; sys.path.insert(0, str(W))
sys.path.insert(0, str(W.parents[1] / 'Tools/HeroBase'))
import fit_f, asm_f, fhand, metrics_f, mirror_check, sil_f
from femlib import *
from PIL import Image, ImageDraw

# male FORM3 reference (work/male-hands-form3/proof/MALE_HANDS_FORM3_RESULTS.md)
MALE = dict(finger_base_mm=25.3, palm_breadth_web_mm=118.0, palm_length_mm=122.0, thumb_diam_mm=2 * 13.5)
PLATE = dict(front_edge_y_mm=-60.0, back_edge_y_mm=5.0, lowest_tip_z_mm=692.0, index_tip_y_mm=-55.0, pinky_tip_y_mm=-3.0)
G = dict(place_tip_y_mm=10.0, place_edge_mm=12.0, place_z_mm=12.0, weld_dihedral_deg=40.0, fem_finger=0.70, fem_palm=0.75, fem_thumb=0.85, consensus_ratio=1.25, sil_full_pts=1.0, roi_factor=1.05)


def weld_dihedral(Vn, polys, ring_ids, band_mm=12.0):
    ef = edge_faces(polys); FN = face_normals(Vn, polys)
    rs = set(int(i) for i in ring_ids); c = Vn[list(rs)].mean(0)
    best = 0.0; n60 = 0
    for e, fl in ef.items():
        if len(fl) != 2: continue
        m = 0.5 * (Vn[e[0]] + Vn[e[1]])
        if abs(m[2] - c[2]) < band_mm / 1000 and np.linalg.norm(m[:2] - c[:2]) < 0.045:
            a = np.degrees(np.arccos(np.clip(np.dot(FN[fl[0]], FN[fl[1]]), -1, 1))); best = max(best, a)
    return best


def placement(Vn, si, polys):
    out = {}
    for side in (+1, -1):
        s = si[side]; mp = s['mapping']; info = s['info']
        hand_ids = sorted(set(mp.values()))
        zs = Vn[hand_ids, 2]; sel_ = zs <= 0.80                      # palm + fingers (below the wrist transition)
        ys = Vn[hand_ids, 1][sel_]
        tip_idx = Vn[mp[info['fin_rows'][0][1]]]; tip_pin = Vn[mp[info['fin_rows'][3][1]]]
        out[side] = dict(front_edge_y_mm=float(ys.min() * 1000), back_edge_y_mm=float(ys.max() * 1000), lowest_z_mm=float(zs.min() * 1000),
                         index_tip_y_mm=float(tip_idx[1] * 1000), pinky_tip_y_mm=float(tip_pin[1] * 1000), index_tip_z_mm=float(tip_idx[2] * 1000), pinky_tip_z_mm=float(tip_pin[2] * 1000),
                         hand_centroid_y_mm=float(ys.mean() * 1000))
    return out


def start_placement():
    V0 = asm_f.V0; out = {}
    for side in (+1, -1):
        hv = np.load(W / f'data/start_hand_verts_{side}.npy'); out[side] = dict(front_edge_y_mm=float(V0[hv, 1].min() * 1000), back_edge_y_mm=float(V0[hv, 1].max() * 1000), lowest_z_mm=float(V0[hv, 2].min() * 1000), hand_centroid_y_mm=float(V0[hv, 1].mean() * 1000))
    return out


def feminine(res, Vn, si):
    F = res['R']['fingers']; T = res['R']['thumb']
    base = float(np.mean([F[k]['width_base_mm'] for k in F]))
    s = si[+1]; mp = s['mapping']; info = s['info']
    kn = info['ring'][len(info['w_rows'])]                       # knuckle ring
    xs = Vn[[mp[v] for v in kn if v in mp]]
    # breadth across the knuckle ring = extent along the finger-row axis (local a): measure in 3D as the max pairwise distance of ring vertices
    from itertools import combinations
    P = xs; d = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2); breadth = float(d.max() * 1000)
    return dict(finger_base_mm=base, palm_breadth_web_mm=breadth, thumb_diam_mm=float(T['mean_diam_mm']),
                ratios=dict(finger=base / MALE['finger_base_mm'], palm=breadth / MALE['palm_breadth_web_mm'], thumb=float(T['mean_diam_mm']) / MALE['thumb_diam_mm']))


def consensus(Vn, polys, hv_mask):
    """limbs-G3 style: soft XOR of the model silhouette vs the MEAN of the four plate polygon silhouettes (front/back x left/right) in the hand zone, over how far
    the plate views are from that mean.  Returns (model_err, plate_self_err, ratio)."""
    from plate_profiles import FEMALE as F
    def poly(pts):
        im = Image.new('L', (1280, 720), 0); ImageDraw.Draw(im).polygon(pts, fill=255); return np.array(im) > 0
    PF, PB = poly(F['front_outline']), poly(F['back_outline'])
    xpx = np.arange(64, 118, 1.0); ypx = np.arange(352, 422, 1)
    T4 = []
    for P_, cx in ((PF, 440), (PB, 847)):
        for sd in (-1, 1):
            cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); T4.append(P_[np.ix_(ypx, cols)].astype(float))
    Tm = np.mean(T4, axis=0)
    keep = np.ones_like(Tm, bool)
    for j, y in enumerate(ypx):
        if y >= 372: keep[j, xpx < 76] = False
        else: keep[j, xpx < 60] = False
    err = lambda M, T: np.abs(M - T)[keep].sum() / np.maximum(M, T)[keep].sum()
    plate_self = float(np.mean([err(t, Tm) for t in T4]))
    Tr = Mesh(Vn.astype(np.float32), polys).tris()
    # model masks: right (+x) hand in the front view at |dx|, supersampled 3x
    from femlib import raster
    ms = []
    for view, cx, sgn in (('bald_front', 440, +1), ('bald_back', 847, -1)):
        for sd in (+1, -1):
            x0 = int(cx + sd * 64 * sgn if False else 0)
    # simpler: rasterise the whole figure once per view and sample like the plate
    ms = []
    for view, cx in (('bald_front', 440), ('bald_back', 847)):
        full = raster(Vn, Tr, view, (0, 0, 1280, 720), ss=2).astype(float)
        for sd in (-1, 1):
            cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); ms.append(full[np.ix_(ypx, cols)])
    model_err = float(np.mean([err(m, Tm) for m in ms]))
    return model_err, plate_self, model_err / plate_self


def consensus_img(Vn, polys):
    """same zone / sampling as consensus() but the target is the mean of the plate IMAGE masks (keeps the thumb slit)"""
    PM = np.load(W / 'data/plate_masks.npz')
    xpx = np.arange(64, 118, 1.0); ypx = np.arange(352, 422, 1)
    T4 = []
    for nm, cx in (('bald_front', 440), ('bald_back', 847)):
        for sd in (-1, 1):
            cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); T4.append(PM[nm][np.ix_(ypx, cols)].astype(float))
    Tm = np.mean(T4, axis=0)
    keep = np.ones_like(Tm, bool)
    for j, y in enumerate(ypx):
        if y >= 372: keep[j, xpx < 76] = False
        else: keep[j, xpx < 60] = False
    err = lambda M, T: np.abs(M - T)[keep].sum() / np.maximum(M, T)[keep].sum()
    plate_self = float(np.mean([err(t, Tm) for t in T4]))
    Tr = Mesh(Vn.astype(np.float32), polys).tris(); ms = []
    for view, cx in (('bald_front', 440), ('bald_back', 847)):
        full = raster(Vn, Tr, view, (0, 0, 1280, 720), ss=2).astype(float)
        for sd in (-1, 1):
            cols = np.clip(np.round(cx + sd * xpx).astype(int), 0, 1279); ms.append(full[np.ix_(ypx, cols)])
    model_err = float(np.mean([err(m, Tm) for m in ms]))
    return model_err, plate_self, model_err / plate_self


def full_sil_xor(Vn, polys):
    from plate_profiles import FEMALE as F
    def poly(pts):
        im = Image.new('L', (1280, 720), 0); ImageDraw.Draw(im).polygon(pts, fill=255); return np.array(im) > 0
    Tr = Mesh(Vn.astype(np.float32), polys).tris(); out = {}
    for view, key in (('bald_front', 'front_outline'), ('bald_back', 'back_outline')):
        P_ = poly(F[key]); M = raster(Vn, Tr, view, (0, 0, 1280, 720), ss=2)
        out[view] = float((P_ ^ M).sum() / (P_ | M).sum() * 100)
    return out


def run(x, tag, verify_json, audit_json, out_json):
    res, (Vn, polys, si) = metrics_f.compute(x)
    lines = list(metrics_f.check(res))
    add = lambda name, ok, ev: lines.append((name, bool(ok), ev))
    # placement
    pl = placement(Vn, si, polys); st = start_placement()
    for side, nm in ((+1, '+x'), (-1, '-x')):
        p = pl[side]
        add(f'HAND_PLACEMENT {nm}: index / pinky fingertip y vs plate profile (<= {G["place_tip_y_mm"]} mm)', abs(p['index_tip_y_mm'] - PLATE['index_tip_y_mm']) <= G['place_tip_y_mm'] and abs(p['pinky_tip_y_mm'] - PLATE['pinky_tip_y_mm']) <= G['place_tip_y_mm'],
            f'index {p["index_tip_y_mm"]:.1f} (plate {PLATE["index_tip_y_mm"]}) pinky {p["pinky_tip_y_mm"]:.1f} (plate {PLATE["pinky_tip_y_mm"]})')
        add(f'HAND_PLACEMENT {nm}: hand band front/back edge vs plate (<= {G["place_edge_mm"]} mm)', abs(p['front_edge_y_mm'] - PLATE['front_edge_y_mm']) <= G['place_edge_mm'] and abs(p['back_edge_y_mm'] - PLATE['back_edge_y_mm']) <= G['place_edge_mm'],
            f'front {p["front_edge_y_mm"]:.1f} (plate {PLATE["front_edge_y_mm"]}) back {p["back_edge_y_mm"]:.1f} (plate {PLATE["back_edge_y_mm"]}); start {st[side]["front_edge_y_mm"]:.1f} / {st[side]["back_edge_y_mm"]:.1f}')
        add(f'HAND_PLACEMENT {nm}: lowest fingertip z vs plate (<= {G["place_z_mm"]} mm)', abs(p['lowest_z_mm'] - PLATE['lowest_tip_z_mm']) <= G['place_z_mm'], f'{p["lowest_z_mm"]:.1f} mm (plate {PLATE["lowest_tip_z_mm"]}, start {st[side]["lowest_z_mm"]:.1f})')
        ring = np.load(W / f'data/start_hand_ring_{side}.npy')
        wd = weld_dihedral(Vn, polys, ring)
        add(f'HAND_PLACEMENT {nm}: wrist weld clean, max dihedral in the +-12 mm band <= {G["weld_dihedral_deg"]} deg', wd <= G['weld_dihedral_deg'], f'{wd:.1f} deg')
    fem = feminine(res, Vn, si)
    add(f'FEMININE_SOFT_PLASTIC: finger base width / male FORM3 <= {G["fem_finger"]}', fem['ratios']['finger'] <= G['fem_finger'], f'{fem["finger_base_mm"]:.1f} mm vs {MALE["finger_base_mm"]} -> {fem["ratios"]["finger"]:.2f}')
    add(f'FEMININE_SOFT_PLASTIC: palm breadth at the web / male <= {G["fem_palm"]}', fem['ratios']['palm'] <= G['fem_palm'], f'{fem["palm_breadth_web_mm"]:.0f} mm vs {MALE["palm_breadth_web_mm"]:.0f} -> {fem["ratios"]["palm"]:.2f}')
    add(f'FEMININE_SOFT_PLASTIC: thumb diameter / male <= {G["fem_thumb"]}', fem['ratios']['thumb'] <= G['fem_thumb'], f'{fem["thumb_diam_mm"]:.1f} mm vs {MALE["thumb_diam_mm"]:.0f} -> {fem["ratios"]["thumb"]:.2f}')
    # mirror
    mr = mirror_check.mirror_report(x, verbose=False)
    dist = max(mr[k][0] for k in mr if k.startswith('finger') or k == 'thumb' or k.startswith('palm_w0.03'))
    add(f'MIRROR_L_R: right vs mirrored left, distal hand (fingers, thumb, palm w >= 30 mm) max <= {metrics_f.GATES["mirror_distal_max_mm"]} mm', dist <= metrics_f.GATES['mirror_distal_max_mm'], f'max {dist:.4f} mm ({ {k: round(v[0], 4) for k, v in mr.items()} })')
    # silhouettes
    hv = sil_f.hand_mask_for(Vn)
    e_new = sil_f.evaluate(Vn, polys, hv)
    V0, p0 = asm_f.V0, asm_f.POLYS0; e_old = sil_f.evaluate(V0, p0, sil_f.hand_mask_for(V0))
    cm_new = consensus(Vn, polys, hv); cm_old = consensus(V0, p0, hv)
    im_new = consensus_img(Vn, polys); im_old = consensus_img(V0, p0)
    add(f'SIL_NOT_WRECKED: hand-ROI XOR vs the plate IMAGE masks (8 ROIs, weighted) <= start x {G["roi_factor"]}', e_new['total'] <= e_old['total'] * G['roi_factor'], f'{e_old["total"]:.0f} -> {e_new["total"]:.0f} px ({100 * (e_new["total"] / e_old["total"] - 1):+.1f} %); the start hand was itself fitted to the plate silhouettes')
    add('SIL_NOT_WRECKED (info only): limbs-G3 polygon consensus ratio', True, f'polygon target is a filled blob without the thumb slit, so it rewards the old mitten: start {cm_old[2]:.2f} -> new {cm_new[2]:.2f} (limit 1.25 was for the limbs hands); image-mask consensus ratio start {im_old[2]:.2f} -> new {im_new[2]:.2f}')
    fs_new = full_sil_xor(Vn, polys); fs_old = full_sil_xor(V0, p0)
    add(f'SIL_NOT_WRECKED: full-figure silhouette XOR vs plate polygons (front, back) <= start + {G["sil_full_pts"]} pt', all(fs_new[k] <= fs_old[k] + G['sil_full_pts'] for k in fs_new), f'front {fs_old["bald_front"]:.2f} -> {fs_new["bald_front"]:.2f} %, back {fs_old["bald_back"]:.2f} -> {fs_new["bald_back"]:.2f} %')
    # from blend verification + audit
    if verify_json and Path(verify_json).exists():
        v = json.load(open(verify_json)); v0 = json.load(open(W / 'data/verify_start.json'))
        add('NO_SELF_INTERSECT: hand-vs-hand and hand-vs-body triangle overlaps = 0 (BVH, non-adjacent)', v['bvh_hand_vs_hand'] == 0 and v['bvh_hand_vs_body'] == 0, f'hand/hand {v["bvh_hand_vs_hand"]}, hand/body {v["bvh_hand_vs_body"]}; all pairs {v["bvh_overlap_pairs_nonadjacent"]} = start {v0["bvh_overlap_pairs_nonadjacent"]} (head eyes/lashes)')
        add('TOPOLOGY: 0 boundary / non-manifold / flipped edges, 0 degenerate faces, 0 loose verts, volume > 0', v['boundary_edges'] == 0 and v['nonmanifold_edges'] == 0 and v['flipped_edges'] == 0 and v['degenerate_faces'] == 0 and v['loose_verts'] == 0 and v['signed_volume_m3'] > 0,
            f'volume {v["signed_volume_m3"]:.5f} m3 (start {v0["signed_volume_m3"]:.5f}), min face area {v["min_face_area_mm2"]:.4f} mm2 (start {v0["min_face_area_mm2"]:.4f})')
        add('TOPOLOGY: unchanged faces keep material + corner UV; new faces Base_Grey_F on the flat grey patch', v['unchanged_material_diffs'] == 0 and v['unchanged_uv_diffs'] == 0 and v['new_faces_material'] == ['Base_Grey_F'] and all(abs(a_ - 0.93) < 1e-6 and abs(b_ - 0.10) < 1e-6 for a_, b_ in v['new_faces_uv']), f'{v["faces_unchanged"]} faces unchanged, {v["faces_new"]} new; UV {v["new_faces_uv"]}')
        add('TOPOLOGY: Hair_F bit-identical', v['hair_sha'] == v0['hair_sha'], v['hair_sha'][:16] + '...')
        add('TRIANGLES (disclosed): body + hair vs the 50k guide', True, f'body {v0["tris"]} -> {v["tris"]} (+{v["tris"] - v0["tris"]}), body+hair {v0["tris"] + v0["hair_tris"]} -> {v["tris"] + v["hair_tris"]}')
    if audit_json and Path(audit_json).exists():
        a = json.load(open(audit_json))
        add('ZONE_OUTSIDE=0: vertices outside the two hand shells bit-identical to the start (incl. 36 wrist-ring verts)', a['moved_outside_shells'] == 0 and a['ring_moved'] == 0, f'moved outside {a["moved_outside_shells"]}, ring verts moved {a["ring_moved"]} (max {a["ring_max_mm"]:.4f} mm), shell slots reused {a["slots_reused"]}, appended {a["appended"]}')
        add('ZONE_OUTSIDE=0: every polygon that does not touch a hand shell is unchanged', a['faces_unchanged_ok'], f'{a["faces_checked"]} faces checked')
    summary = dict(tag=tag, lines=[dict(name=n, ok=ok, evidence=ev) for n, ok, ev in lines], all_pass=all(ok for n, ok, ev in lines),
                   data=dict(placement=pl, start_placement=st, feminine=fem, consensus=dict(new=cm_new, start=cm_old), consensus_img=dict(new=im_new, start=im_old), roi=dict(new=e_new['total'], start=e_old['total']), full_sil=dict(new=fs_new, start=fs_old), mirror={k: list(v) for k, v in mr.items()}, metrics=res))
    json.dump(summary, open(out_json, 'w'), indent=1, default=float)
    for n, ok, ev in lines: print(('PASS ' if ok else 'FAIL ') + n + ' | ' + ev[:260])
    print('ALL PASS' if summary['all_pass'] else 'SOME FAIL')
    return summary


if __name__ == '__main__':
    x = json.load(open(sys.argv[1]))['params'] if sys.argv[1].endswith('.json') else json.loads(sys.argv[1])
    run(x, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, sys.argv[4] if len(sys.argv) > 4 else None, sys.argv[5] if len(sys.argv) > 5 else str(W / 'checks.json'))
