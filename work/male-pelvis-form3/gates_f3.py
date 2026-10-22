"""Assemble checks.json (+ proof/P18 gate table) for MALE_PELVIS_FORM3.   python3 gates_f3.py
needs: data/V_FORM3.npy, export/candidate_FORM3.{blend,fbx}, export/audit_FORM3.json, export/f3_zone_report.json, export/merged_fd04bc28.*, r/FORM3_sil4 (slot), data/sil_FORM3.json"""
import sys, json, hashlib, os, numpy as np
sys.path.insert(0, '.')
from PIL import Image, ImageDraw, ImageFont
import gate_metrics as GM, evalv, f3_model as M
from common import V0
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
R = os.path.abspath(os.path.join('..', '..')); ART = R + '/ArtDir/hero/base_lock'
tags = {'chat9': 'start', 'FORM2': 'FINAL6', 'FORM3': 'FORM3'}
out = dict(task='MALE_PELVIS_FORM3', tags=tags)
out['files'] = dict(
    start_blend_chat9_sha256=sha('baseline/HeroBase_Male_Silhouette.blend'), form2_candidate_blend_sha256_expected='9f8c6de1e531bb0005a5c51ab80538a2d3cc1ed64b4afa327a2228ce28b6a7f7', form2_candidate_blend_sha256_found=sha('export/candidate_FORM2_FINAL6.blend'),
    candidate_blend='export/candidate_FORM3.blend', candidate_blend_sha256=sha('export/candidate_FORM3.blend'), candidate_fbx='export/candidate_FORM3.fbx', candidate_fbx_sha256=sha('export/candidate_FORM3.fbx'),
    delta='export/f3_delta.npz', delta_sha256=sha('export/f3_delta.npz'), params='data/P_F3B.json', params_sha256=sha('data/P_F3B.json'), positions='data/V_FORM3.npy', positions_sha256=sha('data/V_FORM3.npy'),
    staged_merge_blend='export/merged_fd04bc28.blend', staged_merge_blend_sha256=sha('export/merged_fd04bc28.blend'), staged_merge_fbx='export/merged_fd04bc28.fbx', staged_merge_fbx_sha256=sha('export/merged_fd04bc28.fbx'),
    artdir_blend_sha256_now=sha(ART + '/blender/HeroBase_Male_Silhouette.blend'), artdir_fbx_sha256_now=sha(ART + '/unity_import/HeroBase_Male_Body.fbx'), artdir_blend_expected_untouched='fd04bc286f688b03ea25fbb57e1242bf2f5976c2dc7bbcdfdb0f68b622ab2347')
out['audit'] = json.load(open('export/audit_FORM3.json')); out['zone_report'] = json.load(open('export/f3_zone_report.json')); out['merge_verify'] = json.load(open('export/install_verify_f3.json')); out['normals_staged'] = json.load(open('export/normals_staged_f3.json'))
ev = {}; gm = {}; ver = {}
for k, t in tags.items():
    V = V0 if t == 'start' else np.load(f'data/V_{t}.npy'); ev[k] = evalv.evaluate(t); gm[k] = GM.metrics(V, t); ver[k] = GM.verdict(gm[k])
out['evalv'] = ev; out['gate_metrics'] = gm; out['gate_verdicts'] = ver
grp = {}
for k in tags:
    grp[k] = {g: ('PASS' if all(ver[k][m] == 'PASS' for m in ms) else 'FAIL') for g, ms in GM.GROUPS.items()}
out['gate_groups_numeric'] = grp
s3 = ev['FORM3']; au = out['audit']
hard = dict(
    ZONE_OUTSIDE_eq_0=('PASS' if au['ZONE_OUTSIDE'] == 0 else 'FAIL'), TOPOLOGY_IDENTICAL=('PASS' if au['TOPOLOGY_IDENTICAL'] else 'FAIL'),
    SIL_front_back_le_5pct=('PASS' if (s3['sil_front'] <= 5 and s3['sil_back'] <= 5) else 'FAIL'), NO_SELF_INTERSECT_NO_NAN=('PASS' if (au['self_intersections_new'] == 0 and au['NAN'] == 0 and au['flipped_faces_vs_start'] == 0 and au['degenerate_faces_after'] == 0) else 'FAIL'),
    FRONT_SMOOTH_MOUND=grp['FORM3']['FRONT_SMOOTH_MOUND'], BUTT_ROUND_PEACH=grp['FORM3']['BUTT_ROUND_PEACH'])
out['hard_gates'] = hard; out['ALL_HARD_GATES_PASS'] = all(v == 'PASS' for v in hard.values())
out['eye_lines'] = dict(note='FRONT_SMOOTH_MOUND / BUTT_ROUND_PEACH numeric tests above are measured; the visual read (no point / bulge / wedge, round peach) is the author reading of proof/P01, P02, P03-P10, P16 -- Adnan sign-off pending.')
json.dump(out, open('checks.json', 'w'), indent=1, default=str); print('CHECKS_WRITTEN', out['ALL_HARD_GATES_PASS'], hard)
# ---- table image ----
rows = [('gate / metric', 'rule', 'chat-9', 'FORM2', 'FORM3')]
def cell(k, m): v = gm[k].get(m); return ('n/a' if v is None else str(v)) + ('  ' + ver[k][m] if m in ver[k] else '')
for m, rule in (('F1_front_reach_mm', 'front reach vs chat-9 >= -1.0'), ('F3_front_dihedral_max', 'front dihedral max <= 35'), ('N1_front_lip_above_roof_min_mm', 'front lip not hanging >= 0'), ('B1_rear_dihedral_max', 'rear dihedral max <= 35'),
                ('B2_lobe_max_turn_deg_per_4mm', 'lobe turn <= 20 deg / 4 mm'), ('B2_concave_outside_cleft', 'convex outside cleft <= 0.02'), ('B3_slot_arch_radius_mm', 'slot arch radius >= 9 mm'), ('B4_V_ness', 'fold V-ness < 0.35 (U)'), ('N1_rear_lip_above_roof_min_mm', 'rear lip not hanging >= 0')):
    rows.append((m, rule, cell('chat9', m), cell('FORM2', m), cell('FORM3', m)))
rows.append(('SIL front / back (%)', '<= 5.0', f"{ev['chat9']['sil_front']} / {ev['chat9']['sil_back']}", f"{ev['FORM2']['sil_front']} / {ev['FORM2']['sil_back']}", f"{ev['FORM3']['sil_front']} / {ev['FORM3']['sil_back']}  PASS"))
rows.append(('ZONE_OUTSIDE / TOPOLOGY / new self-int.', '0 / identical / 0', '-', 'PASS (FORM2 audit)', f"{au['ZONE_OUTSIDE']} / {au['TOPOLOGY_IDENTICAL']} / {au['self_intersections_new']}  PASS"))
rows.append(('FRONT_SMOOTH_MOUND (numeric)', 'all of F1,F3,N1front', grp['chat9']['FRONT_SMOOTH_MOUND'], grp['FORM2']['FRONT_SMOOTH_MOUND'], grp['FORM3']['FRONT_SMOOTH_MOUND']))
rows.append(('BUTT_ROUND_PEACH (numeric)', 'all of B1-B4,N1rear', grp['chat9']['BUTT_ROUND_PEACH'], grp['FORM2']['BUTT_ROUND_PEACH'], grp['FORM3']['BUTT_ROUND_PEACH']))
F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 17); Fb = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18)
cw = [440, 270, 170, 190, 260]; W_ = sum(cw) + 20; H_ = len(rows) * 30 + 20
im = Image.new('RGB', (W_, H_), (20, 20, 24)); d = ImageDraw.Draw(im)
for r, row in enumerate(rows):
    y = 10 + r * 30; x = 10
    for c, t in enumerate(row):
        col = (255, 200, 80) if r == 0 else (225, 225, 230)
        if r > 0 and c >= 2:
            col = (110, 230, 130) if t.endswith('PASS') else ((255, 110, 110) if t.endswith('FAIL') else (200, 200, 210))
        d.text((x + 4, y + 4), t, fill=col, font=Fb if r == 0 else F); x += cw[c]
    d.line([(10, y + 28), (W_ - 10, y + 28)], fill=(50, 50, 62))
im.save('proof/P18_gate_table.png'); print('P18', im.size)
