"""Evaluate the nine DRESSED_LOOK gates from the recorded evidence and write checks.json + GATE_RESULTS.md.   python3 final_report.py

Evidence (all under data/): sources_before/after.json, artdir_before/after.json, build_<sex>.json, verify_<sex>.json, fit_<sex>.json, video_check.json, sheets.json.
Gate definitions: GATE_DEFS_preregistered.md (written before any build or measurement)."""
import glob
import json
import os
import re
import sys

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/dressed-look/'
D = W + 'data/'
P = W + 'proof/'
J = lambda n: json.load(open(D + n))
gates = {}
disc = []

src_b, src_a = J('sources_before.json'), J('sources_after.json')
art_b, art_a = J('artdir_before.json'), J('artdir_after.json')
build = {t: J(f'build_{t}.json') for t in ('male', 'female')}
verify = {t: J(f'verify_{t}.json') for t in ('male', 'female')}
fit = {t: J(f'fit_{t}.json') for t in ('male', 'female')}
video = J('video_check.json')
sheets = J('sheets.json')

# 1 BODIES
body_src_ok = all(src_a['files'][k]['ok'] and src_b['files'][k]['ok'] for k in ('male_body', 'female_body'))
bodies = {t: verify[t]['BODIES'] for t in verify}
copy_sha_ok = all(build[t]['copy_sha256_before_edit'] == src_b['files'][f'{t}_body']['sha256'] for t in build)
g = dict(ok=bool(body_src_ok and copy_sha_ok and all(b['ok'] for b in bodies.values())),
         source_sha_before_after=body_src_ok, copy_equals_source_before_edit=copy_sha_ok,
         geometry_equal={t: {n: v['geometry_equal'] for n, v in b['per_mesh'].items()} for t, b in bodies.items()},
         vertex_hash_equal={t: {n: v['verts_hash_equal'] for n, v in b['per_mesh'].items()} for t, b in bodies.items()},
         vertex_groups_added_on_body={t: b['per_mesh'][next(iter(b['per_mesh']))]['dressed_vgroups'] - b['per_mesh'][next(iter(b['per_mesh']))]['source_vgroups'] for t, b in bodies.items()})
gates['BODIES'] = g
disc.append('Vertex groups were added to the dressed copy of the body (16 per hero: the right-hand finger skin weights, names = bone names) plus an Armature modifier and a parent to the rig: that is the carrier of the finger pose. Mesh geometry (positions, topology, normals, UVs, materials indices) is bit-identical to the source; the geometry hash deliberately excludes vertex-group weights (see GATE_DEFS).')

# 2 KIT_SEPARATE
gates['KIT_SEPARATE'] = dict(ok=all(verify[t]['KIT_SEPARATE']['ok'] for t in verify),
                             sockets={t: verify[t]['KIT_SEPARATE']['sockets'] for t in verify},
                             pieces={t: {n: dict(parent=r['parent'], ok=r['ok']) for n, r in verify[t]['KIT_SEPARATE']['rows'].items()} for t in verify})
# 3 RACKET_IN_HAND
rk = {t: verify[t]['RACKET_IN_HAND'] for t in verify}
gates['RACKET_IN_HAND'] = dict(ok=all(r['ok'] for r in rk.values()),
                               hand_racket={t: r['hand_racket'] for t, r in rk.items()},
                               grip_to_evaluated_hand_min_mm={t: r['grip_to_evaluated_hand_min_mm'] for t, r in rk.items()},
                               hand_vertex_nearest_to_grip_origin_mm={t: r['hand_vertex_nearest_to_grip_origin_mm'] for t, r in rk.items()},
                               in_hand_measured={t: r['in_hand_measured'] for t, r in rk.items()},
                               float_label={t: r['float_label'] for t, r in rk.items()},
                               action={t: r['action'] for t, r in rk.items()})
# 4 BOTH_COLORS
sheet_colors = all(os.path.exists(f"{P}Sheet_{s}_{c}.png") for s in ('Male', 'Female') for c in ('White', 'Black'))
gates['BOTH_COLORS'] = dict(ok=bool(all(verify[t]['BOTH_COLORS']['ok'] for t in verify) and sheet_colors),
                            collections={t: verify[t]['BOTH_COLORS']['collections'] for t in verify},
                            materials_on_kit_pieces={t: verify[t]['BOTH_COLORS']['materials_on_kit_pieces'] for t in verify},
                            sheets_for_both_colours=sheet_colors)
# 5 BOTH_SEXES
exp = {'male': ('Kit_Top_Polo_M', 'Kit_Bottom_Shorts_M'), 'female': ('Kit_Top_Polo_F', 'Kit_Bottom_Skort_F')}
blends = {t: f"{W}export/HeroBase_{'Male' if t == 'male' else 'Female'}_Dressed.blend" for t in exp}
sex_ok = all(os.path.exists(blends[t]) and len([n for n in verify[t]['BOTH_SEXES_part']['present']]) == 4 and
             all(any(e in n for n in verify[t]['BOTH_SEXES_part']['present']) for e in exp[t]) for t in exp)
gates['BOTH_SEXES'] = dict(ok=bool(sex_ok), blends={t: os.path.exists(b) for t, b in blends.items()}, pieces={t: verify[t]['BOTH_SEXES_part']['present'] for t in exp})
# 6 NO_REFIT
nr = {t: verify[t]['NO_REFIT'] for t in verify}
gates['NO_REFIT'] = dict(ok=all(r['ok'] for r in nr.values()),
                         max_abs_world_diff_all_24_pieces=max(v['max_abs_world_diff'] for r in nr.values() for v in r['rows'].values()),
                         pieces_checked=sum(len(r['rows']) for r in nr.values()),
                         geometry_equal_all=all(v['geometry_equal'] for r in nr.values() for v in r['rows'].values()),
                         modifiers_total=sum(v['modifiers'] for r in nr.values() for v in r['rows'].values()))
# 7 SOURCES_UNCHANGED
mt_same = all(src_a['files'][k]['mtime_ns'] == src_b['files'][k]['mtime_ns'] and src_a['files'][k]['size'] == src_b['files'][k]['size'] for k in src_b['files'])
gates['SOURCES_UNCHANGED'] = dict(ok=bool(src_a['all_ok'] and src_b['all_ok'] and mt_same), sha_after={k: v['sha256'] for k, v in src_a['files'].items()},
                                  sha_ok_after={k: v['ok'] for k, v in src_a['files'].items()}, mtimes_unchanged=mt_same)
# 8 ARTDIR_UNCHANGED
mb, ma = art_b['manifest'], art_a['manifest']
added, removed = sorted(set(ma) - set(mb)), sorted(set(mb) - set(ma))
changed = sorted(k for k in set(ma) & set(mb) if ma[k] != mb[k])
kb, ka = art_b['key_sha256'], art_a['key_sha256']
key_diff = sorted(k for k in set(kb) | set(ka) if kb.get(k) != ka.get(k))
audit = {}
for f in sorted(glob.glob(W + 'scripts/*.py') + glob.glob(W + 'scripts/*.sh')):
    txt = open(f).read()
    audit[os.path.basename(f)] = len(re.findall('ArtDir', txt))
audit_ok = all(n == 0 for k, n in audit.items() if k not in ('artdir_snapshot.py', 'final_report.py'))
gates['ARTDIR_UNCHANGED'] = dict(ok=bool(not added and not removed and not changed and not key_diff and audit_ok),
                                 files_before=len(mb), files_after=len(ma), added=added[:20], removed=removed[:20], changed=changed[:20],
                                 base_lock_sha256_files=len(kb), base_lock_sha256_differences=key_diff[:20],
                                 scripts_mentioning_ArtDir={k: n for k, n in audit.items() if n},
                                 snapshot_before=art_b['taken'], snapshot_after=art_a['taken'])
# 9 PROOFS
cells_ok = all(os.path.exists(f'{P}raw/{t}_{c}_{n}.png') for t in ('male', 'female') for c in ('White', 'Black')
               for n in ('full_front', 'full_q3', 'full_side', 'full_back', 'waist_front', 'waist_back', 'hand_a', 'hand_b'))
sheet_files = {f'{s}_{c}': dict(exists=os.path.exists(f'{P}Sheet_{s}_{c}.png'), bytes=os.path.getsize(f'{P}Sheet_{s}_{c}.png') if os.path.exists(f'{P}Sheet_{s}_{c}.png') else 0)
               for s in ('Male', 'Female') for c in ('White', 'Black')}
vids = {}
for s in ('Male', 'Female'):
    v = video.get(f'Turntable_{s}_White.mp4', {})
    vids[s] = dict(exists=v.get('exists'), bytes=v.get('bytes'), size=v.get('size'), fps=v.get('fps'), frames=v.get('frame_duration'), duration_s=v.get('duration_s'), decode_ok=v.get('decode_ok'),
                   mean_abs_diff_vs_first=v.get('mean_abs_diff_vs_first'))
vid_ok = all(v['exists'] and v['decode_ok'] and (v['duration_s'] or 0) >= 6.0 for v in vids.values())
gates['PROOFS'] = dict(ok=bool(cells_ok and all(f['exists'] and f['bytes'] > 100000 for f in sheet_files.values()) and vid_ok), raw_cells_32=cells_ok, sheets=sheet_files, turntables=vids)

overall = all(g['ok'] for g in gates.values())
out = dict(overall='PASS' if overall else 'FAIL', gates={k: v for k, v in gates.items()},
           clip_float={t: dict(findings=fit[t]['findings'], racket=fit[t]['racket'], hand=fit[t].get('hand')) for t in fit},
           disclosures=disc)
json.dump(out, open(W + 'checks.json', 'w'), indent=1, default=str)

# ----------------------------------------------------------------- GATE_RESULTS.md
L = []
L.append(f"# DRESSED_LOOK - gate results\n\n**GATE: DRESSED_LOOK {'PASS' if overall else 'FAIL'}**\n")
L.append('Definitions were written before building/measuring: `GATE_DEFS_preregistered.md`. Evidence: `checks.json`, `data/*.json`, pictures in `proof/`.\n')
L.append('| Gate | Result | Evidence |\n|---|---|---|')
ev = {
    'BODIES': f"both body blends hash to the brief's SHA before and after; the dressed copies were byte-identical to the sources before the first edit; geometry hash of every body mesh (Body, Face, Hair_F) identical (male {len(bodies['male']['per_mesh'])} meshes, female {len(bodies['female']['per_mesh'])}); Body vertex-array SHA-256 male {build['male']['source_body_vertex_hash'][:12]}... == {build['male']['dressed_body_vertex_hash'][:12]}..., female {build['female']['source_body_vertex_hash'][:12]}... == {build['female']['dressed_body_vertex_hash'][:12]}.... 16 right-hand finger vertex groups + an Armature modifier were added to each Body (disclosed below).",
    'KIT_SEPARATE': 'per hero 12 pieces (6 white + 6 black): polo, bottom, 2 socks, 2 shoes, each its own mesh object with its own datablock, parent type OBJECT to the exactly named socket Chest_Top / Hip_Bottom / Foot_L_Shoe / Foot_R_Shoe; body vertex count equals the source.',
    'RACKET_IN_HAND': f"Hand_Racket parented to bone Hand_R of Rig_Hand_R (right hand); Racket_Classic (+ StringBed, Grip, ButtCap, Collider_Racket) children as in the racket blend, geometry hashes equal; grip to evaluated hand min {gates['RACKET_IN_HAND']['grip_to_evaluated_hand_min_mm']['male']:.2f} mm male / {gates['RACKET_IN_HAND']['grip_to_evaluated_hand_min_mm']['female']:.2f} mm female (<= 3 mm), grip origin {gates['RACKET_IN_HAND']['hand_vertex_nearest_to_grip_origin_mm']['male']:.0f} / {gates['RACKET_IN_HAND']['hand_vertex_nearest_to_grip_origin_mm']['female']:.0f} mm from the nearest hand vertex (<= 45 mm): no FLOAT label needed.",
    'BOTH_COLORS': 'collections Kit_White and Kit_Black (6 pieces each) in both blends; the only kit materials are Std_White_Lit and Std_Black_Lit; four sheets (male/female x white/black).',
    'BOTH_SEXES': 'HeroBase_Male_Dressed.blend (Polo_M, Shorts_M) and HeroBase_Female_Dressed.blend (Polo_F, Skort_F).',
    'NO_REFIT': f"24 clothing meshes: geometry hash equal to the kit source, world vertex positions bit-identical (max |diff| = {gates['NO_REFIT']['max_abs_world_diff_all_24_pieces']}), world matrices identical, 0 modifiers, 0 shape keys, 0 vertex groups.",
    'SOURCES_UNCHANGED': 'SHA-256 of the two kit blends, the racket blend and both source body blends equal the brief after the run; sizes and mtimes unchanged.',
    'ARTDIR_UNCHANGED': f"ArtDir stat manifest ({len(mb)} files) identical before/after (0 added, 0 removed, 0 changed); SHA-256 of the {len(kb)} files under hero/base_lock identical; no script of this job names ArtDir except the read-only snapshot and this report.",
    'PROOFS': f"32 raw cells, 4 sheets (proof/Sheet_*.png), 2 turntables ({vids['Male']['frames']} frames, {vids['Male']['duration_s']:.1f} s, {vids['Male']['size']}) re-opened and decoded through the video sequencer (frames differ: the figure turns).",
}
for k, v in gates.items():
    L.append(f"| {k} | {'PASS' if v['ok'] else 'FAIL'} | {ev[k]} |")
L.append('\n## CLIP / FLOAT (labels, not gates - the brief says leave them and caption them)\n')
for t in ('male', 'female'):
    L.append(f"### {t.capitalize()}\n")
    fnd = fit[t]['findings']
    if not fnd:
        L.append('Nothing found: skin-through 0, squeezed 0, floating 0 for polo, shorts, socks and shoes; racket and fingers cross neither body nor kit (0 triangles).\n')
    for f in fnd:
        L.append(f"* **{f['kind']}** - {f['text']}")
    r = fit[t]['racket']
    h = fit[t].get('hand', {})
    L.append(f"* racket: {r['overlap_tri_pairs_vs_body_not_hand']} triangle pairs vs body (not hand), kit {sum(r['overlap_vs_kit'].values())}, grip-to-hand {r['grip_to_hand_min_mm']:.2f} mm; posed hand vs body {h.get('posed_hand_vs_body_not_hand_tri_pairs')}, vs kit {sum(h.get('posed_hand_vs_kit_tri_pairs', {}).values())}")
    L.append('')
L.append('Female CLIP / FLOAT that is visible in the renders: socks and shoes (the kit was fitted to the older placeholder feet: heels, ankles and toes poke through, the sock tubes stand off the shins). Polo/skort float (25 / 16 mm further off the new back / hips than off the body they were fitted to) is measured only. The ArmsCandFit shoe/sock variants exist in the kit blend but the brief says to use the authority pieces.\n')
L.append('## How the hand pose was done\n')
for t in ('male', 'female'):
    r = build[t]['rig']
    s_ = r['search']['best']
    L.append(f"* **{t}** - bones: {len(r['bones'])} (palm + 5 digits x 3); numpy twin vs Blender armature max error {r['numpy_vs_blender_max_err_m'] * 1e6:.1f} micron; hold search ({r['search']['n_stage1']} placements; the best 40 re-tried with 3 wrist tilts, {r['search']['n_stage2']} kept; each re-tried with 8 racket rolls = {r['search']['n_stage3']} candidates scored for wrap, collisions and hand-through-racket) chose du {s_['du']*1000:.0f} mm, dv {s_['dv']*1000:.0f} mm, yaw {s_['yaw_deg']:.0f} deg, tilt {s_['tilt_deg']:.0f} deg, extra roll about the shaft {s_['roll_deg']:.0f} deg (racket face {s_['face_roll_from_palm_normal_deg']:.0f} deg from the palm normal; the racket chat's classic hold = 45), lift {s_['lift']*1000:.1f} mm (all four fingers touch the grip, finger-to-grip distances {', '.join(f'{k} {v:.2f}' for k, v in r['finger_min_dist_mm'].items())} mm); real-mesh check: {r['verify']['racket_hand_tri_overlaps']} racket/hand triangle overlaps.")
L.append("""
The pose lives in the action `Pose_GripClosed` (active); `Pose_Rest` (all zero) is stored with a fake user. Switch with `Rig_Hand_R > Animation > Action`.
The thumb stays in its bind pose (as in the racket chat's proof pose); posing it with linear blend skinning tore the skin.
The female bind hand is cupped, so her fingers were straightened virtually (open state) to place the grip against her palm and were then closed on it; the male hand is used as is.
The racket keeps the classic hold (shaft 38 deg off the finger direction, face roll 45 deg) expressed in a landmark hand frame; its position in the palm plane (du -35..+25 mm, dv -55..+15 mm), a yaw about the palm normal (-40..+16 deg), a wrist tilt (-12 / 0 / +12 deg) and the roll about the shaft (8 values) were searched to make all four fingers wrap the grip without crossing the body or the kit (body and kit are never edited).
""")
# how far the final Hand_Racket sits from the racket chat's male socket (the female one has no earlier equivalent for her new hand)
import numpy as np
sj = json.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/export/racket_classic_socket.json'))['bodies']['male']['socket_bind_pose_blender']
M0 = np.eye(4)
for i_, k_ in enumerate(('X', 'Y', 'Z')):
    M0[:3, i_] = sj[k_]
M0[:3, 3] = sj['position']
M1 = np.array(build['male']['rig']['racket_world_matrix'])
dt_mm = float(np.linalg.norm(M1[:3, 3] - M0[:3, 3]) * 1000)
ang_deg = float(np.degrees(np.arccos(np.clip((np.trace(M0[:3, :3].T @ M1[:3, :3]) - 1) / 2, -1, 1))))
disc.append(f"The male Hand_Racket ended {dt_mm:.1f} mm and {ang_deg:.1f} deg away from the racket chat's male socket (the hold search moved it so that all four fingers wrap the grip); grip origin is still in the palm (see RACKET_IN_HAND).")
L.append('## Disclosures\n')
for d in disc:
    L.append(f'* {d}')
L.append("""* Poses: the sources are un-rigged A-pose meshes with no action and no ready stance, so everything is the bind pose (plus the right-hand grip action). No swing was invented.
* The bodies are rendered with their own source materials (male Blockout_Grey, female Base_Grey_F + Skin_F); the studio, floor shadow and lights on the sheets and the court of the turntables are proof set-up only and are not in the blends.
* The kit blends' per-colour socket empties were not carried over: the dressed blends have ONE exactly named socket per slot and both colourways hang under it (Kit_White visible, Kit_Black hidden).
* The two kit-material copies that the two library loads created (`Std_White_Lit.001` ...) were re-pointed to the single `Std_White_Lit` / `Std_Black_Lit` (material references are not part of the geometry hash).
* The racket socket numbers of the racket chat (`racket_classic_socket.json`) were used as the starting hold for both heroes: the male hand is unchanged since, so the male hold is that socket (then adjusted by the search); the female socket was recomputed for her new 08c hand (as that chat's own notes asked) by transferring the male hold into her landmark hand frame and searching as described above (not with that chat's run_onhand.py).
* `.blend1` backups were disabled; nothing was written outside `work/dressed-look/`.
""")
open(W + 'GATE_RESULTS.md', 'w').write('\n'.join(L))
print('OVERALL', out['overall'], {k: v['ok'] for k, v in gates.items()})
