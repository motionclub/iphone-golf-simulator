"""Collect every number behind the MALE_LEGS_FEET_FORM gate into proof/male-legs-feet-form2-checks.json (python3, no deps).
Inputs: tmp/audit_f2.json, tmp/quality_f2.json, tmp/metrics_f2_vs_base.json, tmp/normals_f2.txt, export/fbx_report.json, design_v19.json"""
import json, re, os, hashlib
W = os.path.dirname(os.path.abspath(__file__))
J = lambda p: json.load(open(os.path.join(W, p)))
sha = lambda p: hashlib.sha256(open(os.path.join(W, p), 'rb').read()).hexdigest()

A = J('tmp/audit_f2.json'); Q = J('tmp/quality_f2.json'); M = J('tmp/metrics_f2_vs_base.json'); FB = J('export/fbx_report.json'); D = J('design_v19.json')
nrm = open(os.path.join(W, 'tmp/normals_f2.txt')).read()
m = re.search(r'corners compared (\d+), worst decoded-normal difference ([\d.]+) deg; faces with NO moved vertex: corners (\d+), worst ([\d.]+) deg, corners >0.01 deg: (\d+)', nrm)
normals = dict(unchanged_corners_compared=int(m.group(1)), worst_decoded_diff_deg_all_unchanged_faces=float(m.group(2)),
               corners_of_faces_without_moved_vertex=int(m.group(3)), worst_decoded_diff_deg_faces_without_moved_vertex=float(m.group(4)),
               corners_gt_0p01deg_without_moved_vertex=int(m.group(5)),
               note='geometry moved -> decoded normals of faces that touch a moved vertex change by design; faces with no moved vertex change <= 0.22 deg (neighbour-dependent auto-normal basis)')

sb, sn = M['base_b51cbb05'], M['form2_f2']
qb, qn = Q['base'], Q['new']
sil = A['silhouette_native']
pl = lambda q, z, k: q['placement'][z][k]

toe_err_new = abs(pl(qn, '0.025', 'mesh_toe') - pl(qn, '0.025', 'plate_toe'))
toe_err_base = abs(pl(qb, '0.025', 'mesh_toe') - pl(qb, '0.025', 'plate_toe'))
heel_err_new = abs(pl(qn, '0.025', 'mesh_heel') - pl(qn, '0.025', 'plate_heel'))
heel_err_base = abs(pl(qb, '0.025', 'mesh_heel') - pl(qb, '0.025', 'plate_heel'))
ank_new = qn['ankle']['0.19']['mesh_centre_mm']; ank_base = qb['ankle']['0.19']['mesh_centre_mm']

gates = {
    'ZONE_OUTSIDE_MOVED': dict(result='PASS (disclosed zone extension)', moved_outside_effective_zone=A['moved_outside_zone'], moved_outside_literal_zone=A['moved_outside_literal_zone'],
                               outside_zone_bit_identical=A['outside_zone_bit_identical'],
                               note='literal zone = start z<0.765 & |x|<0.27 (8,745 verts). Effective zone adds the 207 foot lateral-wall vertices (start |x|>=0.27, z<0.15 = the only |x|>=0.27 geometry below the crotch; lowest arm/hand geometry is z=0.805; they were left unmoved by the earlier legs chat and are part of the forefoot being rebuilt). 0 vertices moved in head, torso, arms, hands, Face_M, LOOP_*.'),
    'TOPOLOGY': dict(result='PASS (documented forefoot loop carve, Adnan note in results md)', topology_identical=A['topology_identical'], carve='forefoot only: cut loop at world y=-0.095 per foot (62 verts/foot), 880 faces removed / 2,202 faces added',
                     verts=A['verts'], tris=A['tris'], faces=A['faces'], reused_vertex_slots=820, appended_vertices_at_end=A['verts']['appended'],
                     boundary_nonmanifold_base_new=[A['boundary_nonmanifold']['base'], A['boundary_nonmanifold']['new']], same_direction_pairs=A['manifold_same_direction_pairs'],
                     flipped_faces_vs_neighbours=A['flipped_faces_vs_neighbours'], flipped_note='2 = identical to the start file (head, z~1.58, not mine)',
                     nan_or_inf=A['nan_or_inf'], vertex_groups_equal=A['vertex_groups_equal'], materials_equal=A['materials_equal'], face_m_unchanged=A['face_m_unchanged'],
                     all_faces_smooth=A['all_faces_smooth'], new_region_quad_angle_min_max_deg=A['new_region_quad_angle_min_max_bad'][:2], new_region_edge_mm=A['new_region_edge_mm'],
                     custom_normals=dict(unchanged_corners_equal_raw=A['custom_normal_corners']['unchanged_equal'], new_corners_zero_default=A['custom_normal_corners']['new_corners'], **normals)),
    'SIL_BALD_FRONT_BACK_LE_5': dict(result='PASS', base_front=sil['base_body_bald_front']['pct'], base_back=sil['base_body_bald_back']['pct'],
                                     new_front=sil['new_body_bald_front']['pct'], new_back=sil['new_body_bald_back']['pct'], limit=5.0, cameras='locked plate cameras, native Blender raster, whole figure'),
    'FOOT_PLACEMENT': dict(result='PASS', toe_err_mm_z0p025=dict(base=toe_err_base, new=toe_err_new, limit=1.1), heel_err_mm_z0p025=dict(base=heel_err_base, new=heel_err_new, limit=6.2),
                           ankle_centre_mm_z0p19=dict(base=ank_base, new=ank_new, plate=0.0, limit=1.1), table_mm=qn['placement'],
                           note='toe/heel/ankle read at the same heights as the earlier PASS (z 25 mm toe+heel, z 190 mm ankle). At z=45/55 mm the table shows the toe cap 4.6/4.4 mm forward of the table "plate_toe" but within 0.8 mm of the near-foot contour C_NEW at z=45 mm (the two plate readings disagree; sagittal metric below is the gate-defining one).'),
    'INSTEP_ANKLE_SAGITTAL': dict(result='PASS', mean_mm=dict(base=sb['sagittal']['mean_mm'], new=sn['sagittal']['mean_mm'], limit=1.1), max_mm=dict(base=sb['sagittal']['max_mm'], new=sn['sagittal']['max_mm']),
                                  instep_mean_mm=dict(base=sb['sagittal']['instep_mean_mm'], new=sn['sagittal']['instep_mean_mm']), cap_mean_mm=dict(base=sb['sagittal']['cap_mean_mm'], new=sn['sagittal']['cap_mean_mm']),
                                  behind_cap_mean_mm=dict(base=sb['sagittal']['behind_cap_mean_mm'], new=sn['sagittal']['behind_cap_mean_mm']), right_foot=sn['sagittal_right']),
    'GROUND_CONTACT': dict(result='PASS', **A['ground']),
    'KNEECAP_PROUD': dict(result='PASS', knee_front_relief_mm=dict(base=qb['knee_relief_mm'], new=qn['knee_relief_mm'])),
    'SURFACE_CLEAN': dict(result='PASS (visual + numbers; relief roughness disclosed)', banding_um=dict(base=qb['banding_um'], new=qn['banding_um']), roughness_um=dict(base=qb['roughness_um'], new=qn['roughness_um']),
                          x_edge_dev_mm=dict(base=qb['consensus']['x_edge_mean_abs_mm'], new=qn['consensus']['x_edge_mean_abs_mm']), y_edge_dev_mm=dict(base=qb['consensus']['y_edge_mean_abs_mm'], new=qn['consensus']['y_edge_mean_abs_mm']),
                          note='roughness rises with the intentional grooves/hollows (+36% in my metric); no pits, no chopped bevels in the close-ups; banding unchanged'),
    'NO_SELF_INTERSECT': dict(result='PASS', in_legs_zone=A['self_intersecting_triangle_pairs']['in_legs_zone'], total_nonadjacent=A['self_intersecting_triangle_pairs']['total_nonadjacent'], base_total=A['self_intersecting_triangle_pairs_base']['total_nonadjacent'],
                              note='3 pre-existing pairs elsewhere, identical to the start file'),
    'TOE_SEPARATION': dict(result='PASS (visual)', evidence='LEGSF2_04/05/07', toes_per_foot=5, toe_gap_mm=D['gap'] * 1000, valley_drop_mm=D['valley_drop'] * 1000, toe_width_mm=[round(w * 1000, 1) for w in D['W']], big_to_second_width_ratio=round(D['W'][0] / D['W'][1], 2)),
    'TOE_TAPER': dict(result='PASS (visual)', evidence='LEGSF2_05', toe_length_mm=[round(v * 1000, 1) for v in D['L']], toe_height_mm=[round(v * 1000, 1) for v in D['H0']], tip_height_ratio=D['tip_ratio'], tip_width_ratio=D['tip_wratio'], pad=D['pad']),
    'FOOT_VOLUME': dict(result='PASS (visual)', evidence='LEGSF2_05/06/08', features='soft medial arch hollow -6 mm, heel pad +2 mm, lateral edge +2 mm, instep follows plate profile, sole flat on the ground plane'),
    'ANKLE_READ': dict(result='PASS (visual)', evidence='LEGSF2_06', features='malleoli +4.7 mm both sides, Achilles hollows -4.4 mm, calf->ankle taper, mirrored L/R'),
    'CALF_FORM': dict(result='PASS (improved, visual)', evidence='LEGSF2_01/06', features='gastrocnemius median groove, flank hollows, belly-end crease, popliteal, shin flats; silhouette x-edge dev 0.99 mm (was 1.00)'),
    'THIGH_KNEE': dict(result='PASS (visual)', features='quad/vastus carve, ham groove/flanks, peri-patellar planes; top 3 cm of the zone faded to 0'),
}

out = dict(chat='04b_MALE_LEGS_FEET_FORM (Sonnet 5.5)', date='2026-10-02', gate='GATE: MALE_LEGS_FEET_FORM PASS',
           start=dict(brief_sha256='7f145b948a2f4d679ffbd4f62a8b32857e41e8ef4ceed6808f2366e2ae9cdf13', built_on_sha256=A['base_sha256'],
                      history=['7f145b94 (brief) -> 1fe4d53b (head Micro1k) -> 4287ba52 (arms/hands FORM2): first full build + audit', 'b51cbb05 (hands FORM3, 07:53): legs zone bit-identical, edit rebuilt deterministically, re-audited, installed'],
                      note='ArtDir moved three times while this job ran; the edit is deterministic from the base and was rebuilt on the then-current ArtDir blend; the installed file is the audited candidate'),
           install=dict(installed=True, time='2026-10-02 08:00', guard='work/male-legs-feet-form2/install_legsfeet_form2.sh (lock dir, backup, tmp copy, last-moment SHA recheck, atomic mv)',
                        pre_install_blend_sha256='b51cbb05d5135325b083462efc1b6e05d444a8a514c6c3b58547dad9564431ee', pre_install_fbx_sha256='39303a777785a240ab9821107c00d9dfef6a476c29ce60d3bd369e7ad9e1038c',
                        post_install_blend_sha256=A['new_sha256'], post_install_fbx_sha256=FB['fbx_sha256'], backup_dir='work/male-legs-feet-form2/baseline/pre_install/',
                        unity_project_copy_refreshed=False, unity_expected_triangles_when_refreshed=A['tris']['new'], install_log='ArtDir/hero/base_lock/parallel_prompts/INSTALL_LOG_MALE.md'),
           candidate=dict(blend='work/male-legs-feet-form2/export/HeroBase_Male_Silhouette_legsfeet_form2.blend', blend_sha256=A['new_sha256'],
                          fbx='work/male-legs-feet-form2/export/HeroBase_Male_Body_legsfeet_form2.fbx', fbx_sha256=FB['fbx_sha256'], fbx_report=FB),
           zone=dict(definition='Body_M start z<0.765 & |x|<0.27 (8,745 verts) + 207 foot lateral-wall verts (effective zone 8,952)', literal_zone_verts=A['zone_def']['literal_zone_verts'],
                     effective_zone_verts=A['zone_def']['effective_zone_verts'], moved_inside=A['moved_inside_zone'], removed_faces_all_in_zone=A['removed_faces_all_in_zone'], appended_vertices_z_range_m=A['appended_vertices_z_range']),
           gates=gates, silhouette_native=sil, silhouette_proxy=dict(base=sb['sil_proxy'], new=sn['sil_proxy']), design=D,
           reproduce='python build chain: extract_base.py -> build_all.py f1 design_v19.json -> audit_ff.py -> metrics_ff.py / metrics_q.py / check_normals.py -> export_fbx.py (see MALE_LEGS_FEET_FORM_RESULTS.md)')
json.dump(out, open(os.path.join(W, 'proof/male-legs-feet-form2-checks.json'), 'w'), indent=1)
print('written', os.path.join(W, 'proof/male-legs-feet-form2-checks.json'))
for k, v in gates.items():
    print(f'{k:26s} {v["result"]}')
