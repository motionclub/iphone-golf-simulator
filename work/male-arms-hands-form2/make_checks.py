import json
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-arms-hands-form2')
L = lambda n: json.load(open(W / 'data' / n))
m = L('metrics_G1.json'); au = L('audit_G1.json'); ve = L('verify_G1.json'); si = L('selfisect_G1.json'); sn = L('sil_native.json'); ex = L('extra_G1.json'); fq = L('facequal_G1.json'); am = L('arm_metrics_G1.json'); fb = L('fbx_report_G1.json')
sb = sn['proof/sil_native_before']; sa = sn['proof/sil_native_after']
F = m['fingers']; T = m['thumb']
g = {}
def gate(name, ok, detail): g[name] = dict(result='PASS' if ok else 'FAIL', detail=detail)
# ---------------- FINGER_TAPER (8 fingers)
allf = F['R'] + F['L']
gate('FINGER_TAPER.tip_over_base<=0.70', all(f['taper_tip_over_base'] <= 0.70 for f in allf), [round(f['taper_tip_over_base'], 3) for f in allf])
gate('FINGER_TAPER.mid_over_base<=0.90', all(f['taper_mid_over_base'] <= 0.90 for f in allf), [round(f['taper_mid_over_base'], 3) for f in allf])
gate('FINGER_TAPER.no_equal_width_run(<=35% of rows)', all(c['run_frac'] <= 0.35 for c in ex['finger_width_cv']), [dict(finger=c['finger'], run_frac=round(c['run_frac'], 2), cv=round(c['cv'], 3)) for c in ex['finger_width_cv']])
gate('FINGER_TAPER.knuckle_hint(PIP>=1.0mm,DIP>=0.6mm)', all(f['pip_bump_mm'] >= 1.0 and f['dip_bump_mm'] >= 0.6 for f in allf), [(round(f['pip_bump_mm'], 2), round(f['dip_bump_mm'], 2)) for f in allf])
gate('FINGER_TAPER.pad_tips(>=6 cap rows)', all(f['cap_rows'] >= 6 for f in allf), [f['cap_rows'] for f in allf])
gate('FINGER_TAPER.fingers_separate(gap>=4mm at 40%/70%)', all(abs(x) >= 4.0 for x in m['gaps_mm']['R'] + m['gaps_mm']['L']), [round(x, 1) for x in m['gaps_mm']['R']])
gate('FINGER_TAPER.depth_over_width_base<=1.4', all(f['depth_over_width_base'] <= 1.4 for f in allf), [round(f['depth_over_width_base'], 2) for f in allf])
# ---------------- THUMB_ANATOMY
for s in ('R', 'L'):
    t = T[s]
    gate(f'THUMB_ANATOMY.{s}.thenar_mound>=4mm', ex['T1_thenar_mound_mm'] >= 4.0, round(ex['T1_thenar_mound_mm'], 1))
    gate(f'THUMB_ANATOMY.{s}.two_phalanges(IP bend>=8deg, IP radius bump>=2%)', t['ip_axis_bend_deg'] >= 8.0 and len(ex['thumb_radius_increases']) >= 1, dict(ip_bend_deg=round(t['ip_axis_bend_deg'], 1), radius_bumps=ex['thumb_radius_increases']))
    gate(f'THUMB_ANATOMY.{s}.taper_not_pill(last/max<=0.65)', t['taper_last_over_max'] <= 0.65, round(t['taper_last_over_max'], 3))
    gate(f'THUMB_ANATOMY.{s}.pad_tip(>=6 cap rows, radii decreasing)', t['cap_rows'] >= 6 and all(t['radii_mm'][i] > t['radii_mm'][i + 1] for i in range(len(t['radii_mm']) - 6, len(t['radii_mm']) - 1)), t['radii_mm'][-7:])
    gate(f'THUMB_ANATOMY.{s}.not_spike(min shaft radius>=8mm, length/diameter<=5)', min(t['radii_mm'][:-6]) >= 8.0 and t['length_mm'] / (2 * min(t['radii_mm'][:-6])) <= 5.0, dict(min_r=round(min(t['radii_mm'][:-6]), 1), len_over_diam=round(t['length_mm'] / (2 * min(t['radii_mm'][:-6])), 2)))
gate('THUMB_ANATOMY.root_continuity(max dihedral near root<=75deg)', ex['T5_dihedral']['max'] <= 75.0, ex['T5_dihedral'])
gate('THUMB_ANATOMY.plate_match(hand ROI xor <= 1.15x ArtDir)', m['roi_xor_total'] <= 1.15 * 2218, dict(after=m['roi_xor_total'], before=2218))
gate('MIRROR_L_R(<=0.05mm distal hand)', m['mirror_err_mm_distal_hand']['max'] <= 0.05, m['mirror_err_mm_distal_hand'])
# ---------------- global
gate('ZONE_OUTSIDE=0', au['moved_outside_arm_zone'] == 0 and all(au['bit_identical'].values()), dict(moved_outside_arm_zone=au['moved_outside_arm_zone'], bit_identical=au['bit_identical'], moved_original_verts=au['moved_original_verts'], appended=au['appended']))
gate('NO_SELF_INTERSECT', si['n_pairs'] == 0, si)
gate('SIL_BALD_FRONT<=5.0%(Blender native)', sa['bald_front']['pct'] <= 5.0, dict(before=sb['bald_front']['pct'], after=sa['bald_front']['pct']))
gate('SIL_BALD_BACK<=5.0%(Blender native)', sa['bald_back']['pct'] <= 5.0, dict(before=sb['bald_back']['pct'], after=sa['bald_back']['pct']))
gate('TOPOLOGY(manifold boundary/nonmanifold unchanged, no degenerate polys, custom normals+vgroups kept)', m['manifold']['boundary'] == m['manifold_baseline']['boundary'] and m['manifold']['nonmanifold'] == m['manifold_baseline']['nonmanifold'] and m['degenerate_polys'] == 0 and ve['custom_normal_nonzero'] == 31246 and au['vg_entries_equal'] and ve['sharp_face_true'] == 0 and ve['sharp_edge_true'] == 0, dict(manifold=m['manifold'], baseline=m['manifold_baseline'], custom_normal_nonzero=ve['custom_normal_nonzero'], vg_equal=au['vg_entries_equal']))
gate('ARMS_SECONDARY(no worse: seam step 0, noise down, silhouette within gate)', am['hf_rms_mm']['after'] < am['hf_rms_mm']['before'] and am['max_mm'] <= 3.0, dict(hf_rms_mm=am['hf_rms_mm'], max_move_mm=round(am['max_mm'], 2)))
overall = all(v['result'] == 'PASS' for v in g.values())
out = dict(gate='MALE_ARMS_HANDS_FORM', result='PASS' if overall else 'FAIL', start_blend_sha256='1fe4d53b3bcb9cfaef885d64350150e323a1d726cc4d54cc305ea71e323119bb', start_fbx_sha256='73582af619f63ba34db74a390eccfcca2f321b123761d4f3d971278a1aaa3f90',
           installed_blend_sha256='4287ba523218e89ae5a822483c322dc4cfa163c7af143ebcac11abbacea2db21', installed_fbx_sha256='2d052746eb2ff26403080df24131abecd83564cf04528e77c46a9c2af245c483',
           gates=g, tris=dict(before=au['tris_current'], after=au['tris_staged']), verts=dict(before=au['verts_current'], after=au['verts_staged']), silhouette_native=dict(before=sb, after=sa), fbx=fb, face_quality=fq, arms=am, hand_metrics=m, audit=au, verify_blend=ve)
json.dump(out, open(W / 'data/male-arms-hands-form-checks.json', 'w'), indent=1)
for k, v in g.items(): print(v['result'], k)
print('OVERALL', out['result'])
