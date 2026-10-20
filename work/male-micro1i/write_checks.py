import sys, json, pickle, hashlib; sys.path.insert(0, '.')
import numpy as np
from m1i_lib import *
import ed2v
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
BL = R / 'ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend'; FB = R / 'ArtDir/hero/base_lock/unity_import/HeroBase_Male_Body.fbx'
audit = json.load(open('final/audit_j5g.json')); exp = json.load(open('final/export_j5.json')); cn = json.load(open('final/contour_numbers_h0_j5.json'))
fo = json.load(open('final/facem_offsets_j5.json')); fit = json.load(open(str(R / 'ArtDir/hero/base_lock/proof/_gate/02b_multiangle_fit.json')))
V0, F, loops = load('h0'); V1, _, _ = load('j5')
ordered = pickle.load(open(str(W.parent / 'male-micro1h/data/loops_f18.pkl'), 'rb'))          # ordered chains of the Micro1h build (the blend's vertex groups lose the order)
assert all(sorted(ordered[k[5:]]) == sorted(loops[k]) for k in loops), 'ordered chains do not match the vertex groups'
E = set()
for f in F:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]; E.add((min(a, b), max(a, b)))
chain_ok = lambda idx: all((min(a, b), max(a, b)) in E for a, b in zip(idx[:-1], idx[1:]))
loop_info = {}
for k, idx_ in loops.items():
    idx = list(ordered[k[5:]])
    d = np.linalg.norm(V1[idx] - V0[idx], axis=1) * 1000; dyz = np.linalg.norm((V1[idx] - V0[idx])[:, 1:], axis=1) * 1000
    loop_info[k] = dict(verts=len(idx), ordered_chain_consecutive_vertices_share_an_edge=bool(chain_ok(idx)), max_move_mm=round(float(d.max()), 2), max_move_in_yz_mm=round(float(dyz.max()), 2))
jawj = pickle.load(open('data/jaw_loops_j5.pkl', 'rb'))
jaw_new = {k: dict(verts=len(v), continuous_edge_path=bool(chain_ok(v)), path_length_mm=round(float(sum(np.linalg.norm(V1[a] - V1[b]) for a, b in zip(v[:-1], v[1:])) * 1000), 1)) for k, v in jawj.items()}
jumps = json.load(open('final/loop_chain_jumps.json'))
def alar(Vv, zs=(1.560, 1.552, 1.544, 1.540, 1.536)):
    p = Vv[loops['LOOP_ala_R']]; p = p[np.argsort(-p[:, 2])]
    return {f'{z:.3f}': round(float(np.interp(z, p[::-1, 2], p[::-1, 0]) * 1000), 1) for z in zs}
n0 = V0[loops['LOOP_nostril_R']]; n1 = V1[loops['LOOP_nostril_R']]
poly, c = ed2v.outline_geometry()
h = V1[loops['LOOP_helix_R']]; phi = np.degrees(ed2v.ellipse_angle(h[:, 1], h[:, 2], c)); o = np.argsort(phi)
crest = {int(round(phi[i])): round(float(h[i, 0] * 1000), 1) for i in o[::6]}
res = dict(
    micro='1i', date='2026-10-01', gate_line='GATE: MALE_HEAD FAIL', failed_lines=['OVERALL_LIKENESS', 'FAIL_WRONG_LIKENESS'],
    start=dict(blend_sha256='349d790e28147aedaf7aa6aa1b0879dc2856bf0d6ba7bb054552d1177bccfc12', fbx_sha256=sha(str(W / 'baseline/HeroBase_Male_Body.fbx'))),
    final=dict(blend=str(BL), blend_sha256=sha(BL), fbx=str(FB), fbx_sha256=sha(FB), note='blend = j5 coordinates + continuous jaw groups (j5g); FBX exported from the j5 blend (identical geometry; FBX embeds a timestamp so a re-export hashes differently)'),
    tris=dict(body_m=audit['tris'], face_m=exp['face_tris'], face_m_verts=audit['face_m']['verts'], body_verts=audit['verts'], budget='~60k approved by Adnan for Micro1i'),
    topology=dict(head_edge_mm=audit['head_edge_mm'], face_zone_edge_mm=audit['face_zone_edge_mm'], quad_faces=audit['quad_faces'], tri_faces=audit['tri_faces'], boundary_edges=audit['boundary_edges'], nonmanifold_edges=audit['nonmanifold_edges'], new_vertices=audit['new_vertices'], note='same vertices and faces as Micro1h, only positions changed; 92 boundary + 2 non-manifold edges are pre-existing (eye openings)'),
    regression=dict(moved_outside_head_zone=audit['moved_outside_head_zone'], moved_in_hands=audit['moved_in_hands'], weld_ring_verts=audit['weld_ring_verts'], weld_ring_moved=audit['weld_ring_moved'], verts_below_z1436_moved=audit['verts_below_z1436_moved'], head_zone_verts_moved=audit['head_zone_verts_moved'], head_zone_max_move_mm=round(audit['head_zone_max_move_mm'], 2), body_below_neck_bit_identical=audit['body_below_neck_bit_identical'], height_m=audit['height_m']),
    silhouette_pct=dict(bald_front=round(audit['silhouette']['body_bald_front']['pct'], 4), bald_back=round(audit['silhouette']['body_bald_back']['pct'], 4), with_face_front=round(audit['silhouette']['withface_bald_front']['pct'], 4), with_face_back=round(audit['silhouette']['withface_bald_back']['pct'], 4), limit_pct=5.0, micro1h=dict(front=4.3121, back=4.6175)),
    plate_fit_mm=dict(chin_3q=dict(micro1h=cn['h0']['chin_3q_far_contour_mm'], micro1i=cn['j5']['chin_3q_far_contour_mm'], gate='+-3 mm'),
                      profile_front_y_chin_mouth_rows=cn['j5']['profile_front_y_err_mm'], front_halfwidth_jaw_rows=cn['j5']['front_halfwidth_err_mm_jaw'],
                      ear_front_halfwidth=dict(micro1h=cn['h0']['front_halfwidth_err_mm_ear'], micro1i=cn['j5']['front_halfwidth_err_mm_ear']),
                      ear_3q_rear_contour=dict(micro1h=cn['h0']['q3_ear_rear_contour_err_mm'], micro1i=cn['j5']['q3_ear_rear_contour_err_mm'], note='the plates disagree about ear standoff: the front plate has the ear ~19 mm proud of the head, the 3/4 and back plates imply ~8-12 mm less. Micro1i FAVOURS THE FRONT PLATE: front-view ear width is within -4..+1 mm, but the 3/4 rear contour is +7..+15 mm outside plates 04/05 (Micro1h +6.6..+12.4). Open decision for Adnan.'),
                      multiangle_dome_contour_rms_px=fit),
    nose=dict(alar_crease_halfwidth_mm=dict(micro1h=alar(V0), micro1i=alar(V1), note='Micro1h foot was widest at the TOP (23.0 at z1.560) and narrower at the base (~21); Micro1i 19.2 -> 25.5 (plate wings ~25-26)'),
              nostril_ring_R_x_mm=dict(micro1h=[round(float(n0[:, 0].min() * 1000), 1), round(float(n0[:, 0].max() * 1000), 1)], micro1i=[round(float(n1[:, 0].min() * 1000), 1), round(float(n1[:, 0].max() * 1000), 1)])),
    ear=dict(method='rebuilt from scratch: thin-plate skull base from a collar outside the ear + rolled helix rim (quarter-ellipse wall, crest on the carved helix loop) + scapha level + antihelix/concha/tragus/antitragus/lobe relief; crest set by ABSOLUTE x targets vs ellipse angle',
             crest_x_mm_vs_angle_deg_R=crest, params=ed2v.PRM_V, xc_knots=ed2v.XC_KNOTS, hc_front_knots=ed2v.HC_FRONT),
    loops=loop_info, loop_chain_jumps_micro1h_stored_order=jumps,
    jaw_ear_loop=dict(micro1h='stored as fragments: L 71 / R 70 vertices, 10 / 9 jumps of ~52 mm (pre-existing, built with snap=False and a normal mask that blocked front-facing facets)', micro1i=jaw_new, change='LOOP_jaw_ear_L/R vertex-group membership replaced by a continuous edge path along the same jaw curve (30 vertices per side, max 3.95 mm from the curve); geometry untouched'),
    face_m=dict(slots=exp['face_slots'], offsets_from_skin_mm=fo, note='paint layers only: brow ribbons <=1.5 mm (hair), lash/crease/lip/nostril 0.12-0.74 mm, seam ribbon <=1.07 mm at the lip corners; eyeballs sit behind the lid margin; all face forms are Body_M geometry'),
    unity=dict(verify='MALE_FORM_SAVED_UNITY_VERIFY_PASS', fbx_matches_source=True, triangles=60358, hair_root_socket_in_prefab=True, hair_mesh=False, import_settings='globalScale 1, fileScale 1, mesh compression off, normals imported', captures='ArtDir/hero/base_lock/proof/male_form_d/unity/*.png', audit='ArtDir/hero/base_lock/proof/male-form-unity-audit.txt'),
    edit_chain=['e1 chin: far-side 3/4 tangent shave (plates 04 yaw 41, 05 yaw 36), softplus margin 1 mm',
                'e2n nose: bridge narrowed up to 7 mm/side, wings pushed out up to 5.4 mm/side (nostril openings kept), x-only warp',
                'PMO photometric mesh optimisation: Lambert vs plate luminance in 4 views (light az 4/el 40 fitted on the dome), RBF basis 10 mm sigma / 8 mm centres, contour hinge constraints, stubble albedo field',
                'e3/e3b lower-face + chin-band fairing, centre-line profile restored', 'e4 interior relief (infraorbital, malar, buccal, temple, mentolabial, jaw groove, alar groove + lobe bump)', 'e5 cheek apple / smile bunching / lid puff',
                'e8 mouth on the carved loops (seam groove along LOOP_mouth_seam, lip volume, corner pockets)', 'e7 alar fairing', 'e2v ear rebuilt from scratch'],
    gate_lines={'OVERALL_LIKENESS': 'FAIL', 'FAIL_WRONG_LIKENESS': 'FAIL', 'CHIN_WIDTH_3Q': 'PASS (measured +-2.5 mm vs both 3/4 plates; Adnan in-session: jaw almost there)', 'CHIN_FRONT_PROFILE': 'PASS',
                'EAR_ATTACH': 'PASS', 'EAR_ANATOMY': 'PASS', 'CHEEK_ATHLETIC': 'PASS', 'CHEEKBONE_3Q': 'PASS', 'CHEEK_WIDTH': 'PASS', 'MOUTH_SMILE': 'PASS', 'LIP_VOLUME': 'PASS',
                'NO_STICKER_VOLUME': 'PASS', 'TOPO_DENSITY': 'PASS', 'MANDATORY_LOOPS': 'PASS', 'HANDS': 'PASS', 'BODY_BELOW_NECK': 'PASS', 'SIL_%': 'PASS', 'CUSTOMIZE_SOCKETS': 'PASS', 'TRI_BUDGET': 'PASS (60,358 within the ~60k approval)'})
res.update(sil_front=res['silhouette_pct']['bald_front'], sil_back=res['silhouette_pct']['bald_back'], sil_front_face=res['silhouette_pct']['with_face_front'], sil_back_face=res['silhouette_pct']['with_face_back'],
           body_tris=audit['tris'], face_tris=exp['face_tris'], face_edge_mean_mm=audit['face_zone_edge_mm']['mean'], fbx_sha256=res['final']['fbx_sha256'])
json.dump(res, open(str(R / 'ArtDir/hero/base_lock/proof/male-micro1i-checks.json'), 'w'), indent=1)
print('checks json written; final blend', res['final']['blend_sha256'][:12], 'fbx', res['final']['fbx_sha256'][:12], 'start fbx', res['start']['fbx_sha256'][:12])
print('chains whose consecutive vertices do NOT share an edge:', [k for k, v in loop_info.items() if not v['ordered_chain_consecutive_vertices_share_an_edge']])
print('loop max move mm (total, in-yz):', {k: (v['max_move_mm'], v['max_move_in_yz_mm']) for k, v in loop_info.items()})
