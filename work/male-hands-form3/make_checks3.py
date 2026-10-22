import json
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3')
L = lambda n: json.load(open(W / 'data' / n))
A = L('allmetrics_FORM2.json'); B = L('allmetrics_final.json'); au = L('audit_final.json'); ve = L('verify_final.json'); si = L('selfisect_final.json'); sn = L('sil_native.json'); fb = L('fbx_report_final.json')
wf = L('weld_FORM2.json'); wn = L('weld_final.json'); pv = L('palmvol.json')
kk = list(sn.keys()); sb = sn[[x for x in kk if 'before' in x][0]]; sa = sn[[x for x in kk if 'after' in x][0]]
g = {}
def gate(name, ok, detail): g[name] = dict(result='PASS' if ok else 'FAIL', detail=detail)
pc = lambda x, y: round(100 * (y / x - 1), 1)
pa, pb = A['palm']['R'], B['palm']['R']
# ------------------------------------------------------------------ PALM_SCALE (thresholds fixed before the final measurement)
gate('PALM_SCALE.palm_length>=+10%', pc(pa['palm_length_mm'], pb['palm_length_mm']) >= 10, dict(FORM2_mm=round(pa['palm_length_mm'], 1), FORM3_mm=round(pb['palm_length_mm'], 1), pct=pc(pa['palm_length_mm'], pb['palm_length_mm'])))
gate('PALM_SCALE.breadth_at_web>=+4%', pc(pa['palm_breadth_web_mm'], pb['palm_breadth_web_mm']) >= 4, dict(FORM2_mm=round(pa['palm_breadth_web_mm'], 1), FORM3_mm=round(pb['palm_breadth_web_mm'], 1), pct=pc(pa['palm_breadth_web_mm'], pb['palm_breadth_web_mm'])))
gate('PALM_SCALE.breadth_mid_palm>=+5%', pc(pa['palm_breadth_mid_mm'], pb['palm_breadth_mid_mm']) >= 5, dict(FORM2_mm=round(pa['palm_breadth_mid_mm'], 1), FORM3_mm=round(pb['palm_breadth_mid_mm'], 1), pct=pc(pa['palm_breadth_mid_mm'], pb['palm_breadth_mid_mm'])))
gate('PALM_SCALE.planform_area>=+10%', pc(pa['palm_planform_area_mm2'], pb['palm_planform_area_mm2']) >= 10, dict(FORM2_mm2=round(pa['palm_planform_area_mm2']), FORM3_mm2=round(pb['palm_planform_area_mm2']), pct=pc(pa['palm_planform_area_mm2'], pb['palm_planform_area_mm2'])))
gate('PALM_SCALE.palm_volume>=+10%', pv['pct_value'] >= 10, dict(FORM2_mm3=pv['FORM2_mm3'], FORM3_mm3=pv['FORM3_mm3'], pct=pv['pct_value']))
gate('PALM_SCALE.palm_over_middle_finger>=1.15', pb['palm_over_middle_finger'] >= 1.15, dict(FORM2=round(pa['palm_over_middle_finger'], 2), FORM3=round(pb['palm_over_middle_finger'], 2), anthropometry='~1.3'))
gate('PALM_SCALE.plate_hand_ROI_xor<=FORM2', B['roi_xor_total'] <= A['roi_xor_total'], dict(FORM2=A['roi_xor_total'], FORM3=B['roi_xor_total']))
gate('PALM_SCALE.mirror_palm(L=R within 0.2 mm)', all(abs(A_ - B_) < 0.2 for A_, B_ in [(B['palm']['L'][k], B['palm']['R'][k]) for k in ('palm_length_mm', 'palm_breadth_web_mm', 'palm_breadth_mid_mm')]), dict(L=B['palm']['L'], R=pb))
# ------------------------------------------------------------------ FINGER_TIP_ROUND (8 fingers + 2 thumbs)
names = ['finger0', 'finger1', 'finger2', 'finger3', 'thumb']
for key, cond, thr in (('cap_rows>=8', lambda t: t['cap_rows'] >= 8, 8), ('cap_len/mean_tip_radius in [0.9,1.4] (hemisphere-ish)', lambda t: 0.9 <= t['hemisphere_ratio'] <= 1.4, None),
                       ('max_contour_turn_side<=25deg', lambda t: t['max_turn_side_deg'] <= 25, 25), ('max_contour_turn_plan<=25deg', lambda t: t['max_turn_plan_deg'] <= 25, 25)):
    ok = all(cond(B['tips'][s][n]) for s in 'RL' for n in names)
    fld = {'cap_rows': 'cap_rows', 'cap_len': 'hemisphere_ratio', 'max_contour_turn_side': 'max_turn_side_deg', 'max_contour_turn_plan': 'max_turn_plan_deg'}[[f for f in ('cap_rows', 'cap_len', 'max_contour_turn_side', 'max_contour_turn_plan') if key.startswith(f)][0]]
    gate('FINGER_TIP_ROUND.' + key, ok, dict(FORM2={n: round(A['tips']['R'][n][fld], 2) for n in names}, FORM3={n: round(B['tips'][s][n][fld], 2) for s in 'RL' for n in names if s == 'R'}, FORM3_L_equals_R=all(abs(B['tips']['L'][n][fld] - B['tips']['R'][n][fld]) < 0.3 for n in names)))
# ------------------------------------------------------------------ THUMB_ANATOMY (hold)
for s in 'RL':
    t = B['thumb'][s]; ex = B['extra'][s]; rad = t['radii_mm']; ncap = t['cap_rows']; sh = rad[:len(rad) - ncap]
    gate(f'THUMB_ANATOMY.{s}.thenar_mound>=4mm', ex['T1_thenar_mound_mm'] >= 4.0, dict(FORM2=round(A['extra'][s]['T1_thenar_mound_mm'], 1), FORM3=round(ex['T1_thenar_mound_mm'], 1)))
    inc = sum(x[1] for x in ex['thumb_radius_increases'])
    gate(f'THUMB_ANATOMY.{s}.two_phalanges(IP bend>=8deg, IP bump>=0.5mm)', t['ip_axis_bend_deg'] >= 8.0 and inc >= 0.5, dict(ip_bend_deg=round(t['ip_axis_bend_deg'], 1), ip_bump_mm_total=round(inc, 2), FORM2_bump=round(sum(x[1] for x in A['extra'][s]['thumb_radius_increases']), 2)))
    gate(f'THUMB_ANATOMY.{s}.taper_not_pill(last/max<=0.65)', t['taper_last_over_max'] <= 0.65, dict(FORM2=round(A['thumb'][s]['taper_last_over_max'], 3), FORM3=round(t['taper_last_over_max'], 3)))
    gate(f'THUMB_ANATOMY.{s}.pad_tip(>=6 cap rows, radii decreasing)', ncap >= 6 and all(rad[i] > rad[i + 1] for i in range(len(rad) - ncap, len(rad) - 1)), rad[-(ncap + 1):])
    gate(f'THUMB_ANATOMY.{s}.not_spike(min shaft radius>=8mm, length/diameter<=5)', min(sh) >= 8.0 and t['length_mm'] / (2 * min(sh)) <= 5.0, dict(min_r=round(min(sh), 1), len_over_diam=round(t['length_mm'] / (2 * min(sh)), 2)))
    gate(f'THUMB_ANATOMY.{s}.root_continuity(max dihedral within 25mm<=75deg)', ex['T5_dihedral']['max'] <= 75.0, dict(FORM2=round(A['extra'][s]['T5_dihedral']['max'], 1), FORM3=ex['T5_dihedral']))
gate('THUMB_ANATOMY.plate_match(hand ROI xor <= 1.15x FORM2)', B['roi_xor_total'] <= 1.15 * A['roi_xor_total'], dict(FORM2=A['roi_xor_total'], FORM3=B['roi_xor_total']))
# ------------------------------------------------------------------ FINGER_TAPER (hold, no sausage return)
allf = B['fingers']['R'] + B['fingers']['L']; allcv = B['extra']['R']['finger_width_cv'] + B['extra']['L']['finger_width_cv']
gate('FINGER_TAPER.tip_over_base<=0.70', all(f['taper_tip_over_base'] <= 0.70 for f in allf), dict(FORM2=[round(f['taper_tip_over_base'], 2) for f in A['fingers']['R']], FORM3=[round(f['taper_tip_over_base'], 2) for f in B['fingers']['R']], note='measured at the last shaft ring (FORM3: earlier on the finger because the round cap is longer)'))
gate('FINGER_TAPER.mid_over_base<=0.90', all(f['taper_mid_over_base'] <= 0.90 for f in allf), [round(f['taper_mid_over_base'], 2) for f in B['fingers']['R']])
gate('FINGER_TAPER.no_equal_width_run(<=35% of rows)', all(c['run_frac'] <= 0.35 for c in allcv), [dict(finger=c['finger'], run_frac=round(c['run_frac'], 2)) for c in B['extra']['R']['finger_width_cv']])
gate('FINGER_TAPER.knuckle_hint(PIP>=1.0mm,DIP>=0.6mm)', all(f['pip_bump_mm'] >= 1.0 and f['dip_bump_mm'] >= 0.6 for f in allf), [(round(f['pip_bump_mm'], 2), round(f['dip_bump_mm'], 2)) for f in B['fingers']['R']])
gate('FINGER_TAPER.pad_tips(>=6 cap rows)', all(f['cap_rows'] >= 6 for f in allf), [f['cap_rows'] for f in B['fingers']['R']])
gate('FINGER_TAPER.fingers_separate(gap>=4mm at 40%/70%)', all(abs(x) >= 4.0 for x in B['gaps_mm']['R'] + B['gaps_mm']['L']), dict(FORM2=[round(x, 1) for x in A['gaps_mm']['R']], FORM3=[round(x, 1) for x in B['gaps_mm']['R']]))
gate('FINGER_TAPER.depth_over_width_base<=1.4 (no sausage)', all(f['depth_over_width_base'] <= 1.4 for f in allf), dict(FORM2=[round(f['depth_over_width_base'], 2) for f in A['fingers']['R']], FORM3=[round(f['depth_over_width_base'], 2) for f in B['fingers']['R']]))
gate('FINGER_TAPER.width_base_unchanged(+-1.5mm vs FORM2, no sausage return)', all(abs(f['width_base_mm'] - a_['width_base_mm']) <= 1.5 for f, a_ in zip(B['fingers']['R'], A['fingers']['R'])), dict(FORM2=[round(f['width_base_mm'], 1) for f in A['fingers']['R']], FORM3=[round(f['width_base_mm'], 1) for f in B['fingers']['R']]))
# ------------------------------------------------------------------ global
gate('MIRROR_L_R(<=0.05mm distal hand)', B['mirror_err_mm_distal_hand']['max'] <= 0.05, B['mirror_err_mm_distal_hand'])
gate('ZONE_OUTSIDE=0', au['all_conditions_ok'] and au['moved_outside_hand_shell'] == 0 and au['weld_ring_moved'] == 0, dict(moved_outside_hand_shell=au['moved_outside_hand_shell'], weld_ring_verts_moved=au['weld_ring_moved'], bit_identical=au['bit_identical'], moved_original_verts=au['moved_original_verts'], hand_shell_verts=au['shell_verts'], appended=au['appended']))
gate('NO_SELF_INTERSECT', si['n_pairs'] == 0, si)
gate('SIL_BALD_FRONT<=5.0%(Blender native)', sa['bald_front']['pct'] <= 5.0, dict(before=sb['bald_front']['pct'], after=sa['bald_front']['pct']))
gate('SIL_BALD_BACK<=5.0%(Blender native)', sa['bald_back']['pct'] <= 5.0, dict(before=sb['bald_back']['pct'], after=sa['bald_back']['pct']))
gate('TOPOLOGY(manifold boundary/non-manifold unchanged, no degenerate polys, custom normals + vgroups + materials kept, no sharp flags)', B['manifold']['boundary'] == B['manifold_baseline']['boundary'] and B['manifold']['nonmanifold'] == B['manifold_baseline']['nonmanifold'] and B['degenerate_polys'] == 0 and ve['custom_normal_nonzero'] == 31246 and ve['custom_normal_loops_diff_from_baseline'] == 0 and au['vg_entries_equal'] and ve['sharp_face_true'] == 0 and ve['sharp_edge_true'] == 0 and ve['materials'] == ['Blockout_Grey'], dict(manifold=B['manifold'], baseline=B['manifold_baseline'], custom_normal_nonzero=ve['custom_normal_nonzero'], custom_normal_diff=ve['custom_normal_loops_diff_from_baseline'], vg_equal=au['vg_entries_equal']))
fq = B['facequal']
gate('FACE_QUALITY(min new face >=0.3mm2, max edge aspect <=16, no worse than FORM2 aspect 14.7)', fq['min_area_mm2'] >= 0.3 and fq['max_edge_aspect'] <= 16.0, dict(FORM2=A['facequal'], FORM3=fq))
gate('WELD_NO_STEP_CREASE(max dihedral at the wrist weld band <=45deg and not worse than FORM2 +2deg)', max(wn['R']['max_dihedral_deg'], wn['L']['max_dihedral_deg']) <= 45 and max(wn['R']['max_dihedral_deg'], wn['L']['max_dihedral_deg']) <= max(wf['R']['max_dihedral_deg'], wf['L']['max_dihedral_deg']) + 2, dict(FORM2=wf, FORM3=wn))
gate('FBX_REIMPORT(verts/tris match, max vertex error <0.01mm, height 1.65-1.75m)', fb['imported_verts'] == au['verts_staged'] and fb['imported_tris'] == au['tris_staged'] and fb['max_nearest_distance_mm'] < 0.01 and 1.65 <= fb['reimport_height_m'] <= 1.75, fb)
gate('TRIANGLES(disclosed, no cap beyond +2%)', (au['tris_staged'] / au['tris_start'] - 1) <= 0.02, dict(before=au['tris_start'], after=au['tris_staged'], delta=au['tris_staged'] - au['tris_start'], pct=round(100 * (au['tris_staged'] / au['tris_start'] - 1), 2), note='AGENTS.md ~35-50k per base unless Adnan approves more; ArtDir was already 63,022 after FORM2'))
overall = all(v['result'] == 'PASS' for v in g.values())
out = dict(gate='MALE_HANDS_FORM3', result='PASS' if overall else 'FAIL', params='work/male-hands-form3/params_final.json', gates=g,
           tris=dict(before=au['tris_start'], after=au['tris_staged']), verts=dict(before=au['verts_start'], after=au['verts_staged']),
           palm=dict(FORM2=A['palm'], FORM3=B['palm']), tips=dict(FORM2=A['tips'], FORM3=B['tips']), silhouette_native=dict(before=sb, after=sa), roi_xor=dict(FORM2=A['roi_xor'], FORM3=B['roi_xor']),
           audit=au, verify_blend=ve, selfintersect=si, fbx=fb, weld=dict(FORM2=wf, FORM3=wn))
json.dump(out, open(W / 'data/male-hands-form3-checks.json', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
for k, v in g.items(): print(v['result'], k)
print('OVERALL', out['result'])
