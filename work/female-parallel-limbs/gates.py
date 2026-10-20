"""python3 gates.py : evaluates the FEMALE_LIMBS gates from measured data and writes proof/GATE_RESULTS.md + data/gates.json"""
import json, hashlib, datetime
A=json.load(open('data/audit_final.json')); M=json.load(open('data/metrics_final.json')); D=json.load(open('data/measure_final.json'))
P=json.load(open('data/peaks_final.json')); X=json.load(open('export/export_report.json')); FV=json.load(open('data/fbx_verify.json'))
R=json.load(open('data/HeroBase_Female_limbs_report.json'))
BASE_HEIGHT_ZMAX=1.7038931846618652
G=[]   # (id, title, pass, detail lines)
def gate(i,title,ok,lines): G.append((i,title,bool(ok),lines))
# G1 outside-zone
gate('G1','OUTSIDE_ZONE = 0 (independent audit vs the start file)',A['OUTSIDE_ZONE_MOVED']==0 and A['removed_or_moved_outside_zone']==0 and A['new_verts_outside_zone']==0,
 [f"start SHA {A['start_sha256'][:16]}…  final SHA {A['final_sha256'][:16]}…",
  f"baseline verts outside the limb zone: {A['outside_zone_baseline_verts']}, missing or moved: {A['outside_zone_baseline_verts_missing_or_moved']}",
  f"removed/moved baseline verts outside zone: {A['removed_or_moved_outside_zone']}; new verts outside zone: {A['new_verts_outside_zone']}",
  f"untouched faces checked {A['untouched_faces_checked']}: missing {A['untouched_faces_missing']}, material diffs {A['untouched_face_material_diffs']}, corner UV diffs {A['untouched_corner_uv_diffs']}",
  f"corner normals away from the change: {A['untouched_corner_normal_diffs_away_from_change']} differ of {A['untouched_corners_checked']} ({A['corner_normal_diffs_at_change_boundary']} at the zone boundary, expected)",
  f"Hair_F vertex hash identical: {A['hair_verts_sha_same']}; all other scene objects identical: {A['other_objects_same']}",
  "zone = z < 0.58 (feet, ankle, shank, calf) OR |x| > 0.18 & 0.60 < z < 0.875 (hands, wrists); arms above the wrist rings and the torso/head are not touched"])
# G2 mesh
ok=(A['non_manifold_edges']==0 and A['non_contiguous_edges']==0 and A['degenerate_faces']==0 and A['loose_verts']==0 and A['materials_same']
    and A['final_body_plus_hair']<=50000 and abs(A['z_max']-BASE_HEIGHT_ZMAX)<1e-7 and A['z_min']>-0.0005 and A['signed_volume_m3']>0)
gate('G2','MESH integrity + budget',ok,
 [f"non-manifold edges {A['non_manifold_edges']}, non-contiguous (flipped) edges {A['non_contiguous_edges']}, degenerate faces {A['degenerate_faces']}, loose verts {A['loose_verts']}",
  f"signed volume {A['signed_volume_m3']:.5f} m³ (>0 = outward winding); materials unchanged: {A['materials_same']}",
  f"tris: body {A['final_tris']} (baseline {A['baseline_tris']}) + hair {A['hair_tris_baseline']} = {A['final_body_plus_hair']} (limit 50000, base_lock/ACCEPTANCE.md)",
  f"height z_max {A['z_max']:.7f} (baseline {BASE_HEIGHT_ZMAX:.7f}); lowest vertex z {A['z_min']*1000:+.3f} mm (soles on the ground)"])
# G3 silhouette consensus
cons={z:M['final']['consensus_'+z] for z in ('arms','hands','legs','feet')}
base_c={z:M['baseline']['consensus_'+z] for z in ('arms','hands','legs','feet')}
ok=all(c['ratio']<=1.25 for c in cons.values())
fl=M['plate_floor']
lines=["metric = soft XOR of the model silhouette vs the MEAN of the four plate silhouettes (front-L/R, back-L/R) in each limb zone, divided by how far the plate views are from that same mean (the plates disagree with each other)",
       "threshold: ratio <= 1.25 (model no further from the plate consensus than 1.25x the plates are from each other)"]
for z,c in cons.items(): lines.append(f"{z:5s}: model {c['model_vs_consensus']:.3f} vs plate-self {c['plate_views_vs_consensus_mean']:.3f} -> ratio {c['ratio']:.2f}  (baseline {base_c[z]['ratio']:.2f})")
lines.append("per-view XOR % vs the plate polygons (baseline -> new; plate-vs-plate floor of the best symmetric mask in brackets) — informational, NOT the gate:")
for z in ('legs','feet','arms','hands'):
    lines.append(f"  {z:5s} front {M['baseline'][f'front_{z}_xor_pct']:5.1f} -> {M['final'][f'front_{z}_xor_pct']:5.1f}   back {M['baseline'][f'back_{z}_xor_pct']:5.1f} -> {M['final'][f'back_{z}_xor_pct']:5.1f}   [floor: mean {fl[z]['floor_mean_pct']:.1f}%, per view {fl[z]['per_view']}]")
gate('G3','LIMB SILHOUETTES vs plate consensus (front+back)',ok,lines)
# G4 profile
pf,pb=M['profile_final'],M['profile_baseline']
ok=pf['max_abs_edge_dev_mm']<=12.0 and pf['max_abs_edge_dev_mm']<pb['max_abs_edge_dev_mm']
gate('G4','SIDE PROFILE of the lower legs vs the plate profile (z 0.17–0.46 m)',ok,
 [f"max front/back edge deviation: baseline {pb['max_abs_edge_dev_mm']:.1f} mm -> new {pf['max_abs_edge_dev_mm']:.1f} mm (threshold 12 mm)",
  f"mean |shank depth deviation|: baseline {pb['mean_abs_depth_dev_mm']:.1f} mm -> new {pf['mean_abs_depth_dev_mm']:.1f} mm; max {pb['max_abs_depth_dev_mm']:.1f} -> {pf['max_abs_depth_dev_mm']:.1f} mm",
  "new targets = plate edges pulled in 5 mm per side (the profile plate shows both legs slightly yawed, so its union silhouette is ~10 mm deeper than one leg); the residual -8…-11 mm depth error is that allowance, not a fit error",
  "front/back (x) silhouettes are unchanged by this step (y-only remap)"])
# G5 dimensions
fl_len=[D['foot_R']['length_along_axis_m'],D['foot_L']['length_along_axis_m']]; hd=[D['hand_R']['length_from_wrist_crease_0.8456_m'],D['hand_L']['length_from_wrist_crease_0.8456_m']]
ok=all(abs(l-0.241)/0.241<=0.08 for l in fl_len) and all(abs(h-0.153)/0.153<=0.10 for h in hd)
gate('G5','DIMENSIONS vs plate',ok,
 [f"foot length heel->toe: R {fl_len[0]:.4f} m, L {fl_len[1]:.4f} m (plate profile 0.241 m, tolerance ±8%); toe-out {D['foot_R']['axis_toe_out_deg']:.1f}° / {D['foot_L']['axis_toe_out_deg']:.1f}°",
  f"hand length wrist crease (z 0.8456) -> fingertip: R {hd[0]:.4f} m, L {hd[1]:.4f} m (plate 0.153 m, tolerance ±10%)",
  f"sole height: lowest new foot vertex z {D['foot_R']['z_min']*1000:+.2f} mm / {D['foot_L']['z_min']*1000:+.2f} mm"])
# G6 structure
toe={k:[p for p in P[k]['peaks_persistence_ge_6mm'] if p['y']<-0.10 and p['persistence_mm']>=15.0] for k in ('foot_R','foot_L')}
fin={k:[p for p in P[k]['peaks_persistence_ge_6mm'] if p['persistence_mm']>=8.0] for k in ('hand_R','hand_L')}
ok=all(len(v)==5 for v in toe.values()) and all(len(v)==5 for v in fin.values())
gate('G6','STRUCTURE: 5 toes per foot, 4 fingers + thumb per hand (persistent geodesic extremities)',ok,
 ["method: geodesic distance over mesh edges from the weld seam; count extremities whose persistence (height above the saddle that joins them to a longer one) is large",
  f"feet: toes with persistence >= 15 mm: R {len(toe['foot_R'])} ({[p['persistence_mm'] for p in toe['foot_R']]} mm), L {len(toe['foot_L'])} ({[p['persistence_mm'] for p in toe['foot_L']]} mm)",
  f"hands: extremities with persistence >= 8 mm: R {len(fin['hand_R'])} ({[p['persistence_mm'] for p in fin['hand_R']]} mm), L {len(fin['hand_L'])} ({[p['persistence_mm'] for p in fin['hand_L']]} mm)"])
# G7 export
ok=(FV['verts']==A['final_verts'] and FV['tris']==A['final_tris'] and abs(FV['height']-1.70395)<2e-4 and FV['materials']==A['material_names'] and FV['scale']==[1.0,1.0,1.0])
gate('G7','FBX export re-imports identically (export/ only; NOT installed in ArtDir)',ok,
 [f"export/HeroBase_Female_Body_limbs.fbx sha {X['fbx_sha256'][:16]}…; re-import verts {FV['verts']} tris {FV['tris']} (blend {A['final_verts']}/{A['final_tris']}), height {FV['height']:.5f} m, scale 1, same 10 materials, custom normals {FV['custom_normals']}",
  "exporter settings copied from Tools/HeroBase/export_male_form.py (scale 1, -Z forward, Y up, no leaf bones, no animation)"])
allok=all(g[2] for g in G)
now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
L=[f"# GATE_RESULTS — FEMALE LIMBS (chat 8/8) — {now}",'',f"## GATE: FEMALE_LIMBS {'PASS' if allok else 'FAIL'}",'']
L+=['| gate | result |','|---|---|']+[f"| {i} {t} | {'PASS' if ok else 'FAIL'} |" for i,t,ok,_ in G]
L+=['']
for i,t,ok,lines in G:
    L+=[f"### {i} {t} — {'PASS' if ok else 'FAIL'}"]+[f"- {x}" for x in lines]+['']
L+=['## What changed (limb zone only)',
 f"- Lower legs (z 0.14–0.58): y-only remap of each z-slice to the plate side profile ({R['leg_verts_moved']} vertices moved; x untouched, so front/back silhouettes are unchanged).",
 f"- Feet: the old skin foot below the ankle ring (z=0.15728) replaced by a new foot (heel, arch/instep wedge, 5 toes, flat sole), welded vertex-to-vertex onto the existing 24-vertex ankle ring; hands: old hand below the wrist ring replaced by a new hand (palm, 4 fingers, thumb), welded onto the existing 18-vertex wrist ring (right ring z=0.8456, left ring z=0.8726 — the only planar rings in the start mesh).",
 f"- {R['deleted_old_tris']} old triangles removed, {R['new_verts']} new vertices; body tris {A['baseline_tris']} -> {A['final_tris']}.",
 '- New faces: feet = Skin_F, hands = Base_Grey_F, UVs on flat patches of the existing albedo atlas (skin / grey), smooth normals.',
 '','## Not done / limits (honest list)',
 '- Not installed into ArtDir (install rule: only after the torso chat is idle or via a documented vertex mask). Merge map: data/HeroBase_Female_limbs_vertex_map.npz (baseline index -> final index, new vertices = -1, zone mask).',
 '- No Unity import/render was run in this chat; the proof is Blender Workbench renders + the FBX re-import check.',
 '- Plate disagreement: the four plate silhouettes disagree 20–35 % with each other in the hands/feet, and the back plate\'s soles sit ~8 px higher than the front plate\'s, so per-view XOR cannot reach 5 % in these zones (floors listed in G3); the feet consensus ratio is 1.07 vs 0.88 for the crude baseline foot — within the gate, but not better than the baseline on that metric (the 3D form, profile, toes and length are much better).',
 '- The hand palm is turned ~55° (from a fit to the plate silhouettes); the profile targets carry a 5 mm-per-side allowance for the plate\'s yawed legs. Both are judgement calls from noisy plates — Adnan\'s eye check is final.',
 '- Arms above the wrist were left untouched (already at the plate floor in the front/back silhouettes).',
 '- Toes are stylised soft-plastic lobes (no nails); fingers are capsule-like.',
 '','## Files',
 '- work/female-parallel-limbs/HeroBase_Female_limbs.blend (deliverable), export/HeroBase_Female_Body_limbs.fbx, baseline/HeroBase_Female.blend (start copy, SHA 200dc3b9…)',
 '- proof/01_limbs_vs_plate_front_back.png, 02_silhouette_overlay_before_after.png, 03_profile_vs_plate.png, 04_hands_vs_plate.png, 05_feet_vs_plate.png, 06_before_after_limbs.png',
 '- data/audit_final.json (outside-zone), metrics_final.json, measure_final.json, peaks_final.json, silhouette_floor.json, HeroBase_Female_limbs_report.json, HeroBase_Female_limbs_vertex_map.npz',
 '- Reproduce: `blender -b baseline/HeroBase_Female.blend --python make_limbs.py -- HeroBase_Female_limbs.blend 1800 1500 5` (needs data/foot_R_raw.npz, hand_R_raw.npz from shapes.py, data/leg_targets.json from legtargets.py)']
open('proof/GATE_RESULTS.md','w').write('\n'.join(L)+'\n')
json.dump({'gate':'FEMALE_LIMBS','result':'PASS' if allok else 'FAIL','gates':{i:ok for i,t,ok,_ in G}},open('data/gates.json','w'),indent=1)
print('\n'.join(L[:12]))
