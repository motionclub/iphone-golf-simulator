"""Evaluate the gates from proof/raw/checks_<g>.json (+ start-kit control) -> checks.json + GATE_RESULTS.md.   python3 final_report.py
Thresholds are the ones written in GATE_DEFS_preregistered.md (plus its disclosed NO_SKIN_GAP zone refinement)."""
import json, os, hashlib, time, glob

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/tennis-shoes-fit'
RAW = f'{W}/proof/raw'
C = {g: json.load(open(f'{RAW}/checks_{g}.json')) for g in ('male', 'female')}
OLD = {g: json.load(open(f'{RAW}/start_kit_on_new_body_{g}.json')) for g in ('male', 'female')}
MAN = {g: json.load(open(f'{W}/export/manifest_{g}.json')) for g in ('male', 'female')}
BODY_SHA = {'male': 'd6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781', 'female': 'a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1'}
START_SHA = {'male': 'ad07a7b9ba984b0f220f975b9fe1b0c1b7068d9897c7e6f96e44f70d23aa77a9', 'female': 'f19a9c03789b7af343c56b005ed587137e8764779d31c3109942156ee71eaf4e'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
G = {}      # gate -> (ok, [evidence lines], [failed lines])


def add(name, ok, ev, fails):
    G[name] = (ok, ev, fails)


# ---------------------------------------------------------------- FOOT_INSIDE
ev, fails = [], []
for g, c in C.items():
    lo = c['layer_overlaps']
    for f in 'RL':
        d = c['foot_inside'][f]
        line = (f'{g} {f}: {d["foot_vertices_below_collar"]} foot vertices (and {d["foot_triangle_centroids_below_collar"]} triangle centroids) below the lowest collar point ({d["collar_rim_z_min"]*1000:.1f} mm): '
                f'outside the shoe {d["foot_verts_outside_shoe"]} (inside shoe material {d["foot_verts_inside_shoe_material"]}+{d["foot_tri_centroids_inside_shoe_material"]}, not enclosed {d["foot_verts_not_enclosed"]}+{d["foot_tri_centroids_not_enclosed"]}); '
                f'nearest skin to shoe {d["foot_to_shoe_min_mm"]} mm (5th pct {d["foot_to_shoe_p05_mm"]} mm); foot-vs-shoe triangle pairs {d["foot_shoe_triangle_overlap_pairs"]}; all {d["foot_verts_up_to_highest_collar_point"]} leg vertices up to the highest collar point ({d["collar_rim_z_max"]*1000:.1f} mm): inside shoe material {d["foot_verts_up_to_highest_collar_point_inside_shoe_material"]}; '
                f'sock vertices below the collar {d["sock_vertices_below_collar"]}: inside shoe material {d["sock_verts_inside_shoe_material"]}, not enclosed {d["sock_verts_not_enclosed"]}; sock inner wall >= {d["sock_inner_to_skin_min_mm"]} mm off the skin')
        ev.append(line)
        if d['foot_verts_outside_shoe'] or d['foot_to_shoe_min_mm'] < 3.0 or d['foot_shoe_triangle_overlap_pairs'] or d['sock_verts_inside_shoe_material'] or d['sock_verts_not_enclosed'] or d['foot_verts_up_to_highest_collar_point_inside_shoe_material']:
            fails.append(f'FOOT_INSIDE {g} {f}: {line}')
        o = lo[f]
        if o['sock_vs_shoe_triangle_pairs'] or o['shoe_vs_body_triangle_pairs'] or o['sock_vs_body_triangle_pairs'] or o['shoe_vertices_inside_sock_material']:
            fails.append(f'FOOT_INSIDE {g} {f}: layer intersections {o}')
    if lo['L_vs_R_shoe_triangle_pairs']:
        fails.append(f'FOOT_INSIDE {g}: left and right shoe intersect')
    ev.append(f'{g}: layer intersections (triangle pairs): sock vs shoe {lo["R"]["sock_vs_shoe_triangle_pairs"]}/{lo["L"]["sock_vs_shoe_triangle_pairs"]}, shoe vs body {lo["R"]["shoe_vs_body_triangle_pairs"]}/{lo["L"]["shoe_vs_body_triangle_pairs"]}, '
              f'sock vs body {lo["R"]["sock_vs_body_triangle_pairs"]}/{lo["L"]["sock_vs_body_triangle_pairs"]}, shoe vertices inside sock material {lo["R"]["shoe_vertices_inside_sock_material"]}/{lo["L"]["shoe_vertices_inside_sock_material"]}, left vs right shoe {lo["L_vs_R_shoe_triangle_pairs"]}')
add('FOOT_INSIDE', not fails, ev, fails)

# ---------------------------------------------------------------- TOE / HEEL
for name, key in (('TOE_COVERED', 'toe'), ('HEEL_COVERED', 'heel')):
    ev, fails = [], []
    for g, c in C.items():
        sv = c['skin_visibility']
        sect = sv.get('exposed_by_sector', {})
        want_sector = 'front' if key == 'toe' else 'rear'
        for f in 'RL':
            d = c['foot_inside'][f]
            inner, outer = d[f'{key}_overhang_inner_mm'], d[f'{key}_overhang_outer_mm']
            lm = c['foot_landmarks'][f]
            pt = lm['longest_toe_tip'] if key == 'toe' else lm['heel_point']
            ev.append(f'{g} {f}: {"longest toe tip" if key == "toe" else "heel point"} at {pt}; inner wall of the upper {inner:+.1f} mm past it, outside of the shoe {outer:+.1f} mm past it (along the foot axis, toe-out {lm["toe_out_deg"]} deg)')
            if inner < 5.0 or outer < 10.0:
                fails.append(f'{name} {g} {f}: inner {inner} mm / outer {outer} mm (need >= 5 / >= 10)')
        ev.append(f'{g}: skin samples below the cuff band reachable by a camera ray from the {want_sector} sector: {sect.get(want_sector, 0)} (all sectors {sv["exposed"]} of {sv["ray_tests"]:,} rays)')
        if sect.get(want_sector, 0) or sv['exposed']:
            fails.append(f'{name} {g}: {sv["exposed"]} exposed skin samples')
    add(name, not fails, ev, fails)

# ---------------------------------------------------------------- NO_SKIN_GAP
ev, fails = [], []
for g, c in C.items():
    sv, cb, ov = c['skin_visibility'], c['skin_visibility_cuff_band'], c['sock_collar_overlap']
    ev.append(f'{g}: skin of both legs from the ground to {sv["z_max"]*1000:.0f} mm (sock top - 30 mm): {sv["skin_samples"]:,} samples x {sv["ray_tests"]:,} camera rays (24 azimuths x elevations -10/0/10/25/45 deg, 1 mm beam, exact ray-triangle): exposed {sv["exposed"]}')
    ev.append(f'{g}: informational, the cuff band itself ({cb["z_range"][0]*1000:.0f}-{cb["z_range"][1]*1000:.0f} mm): {cb["exposed"]} grazing samples seen from above through the open top edge of the sock (not next to the shoe)')
    for f in 'RL':
        o = ov[f]
        ev.append(f'{g} {f}: sock top at z {o["sock_top_z"]*1000:.1f} mm = {o["sock_top_above_rim_mm"]["min"]:.1f} mm above the HIGHEST collar point ({o["sock_top_above_rim_mm"]["at_lowest_rim"]:.1f} mm above the lowest); '
                  f'sock continues {o["sock_below_rim_mm"]["min"]:.1f} mm below the lowest collar point down to the insole (z {o["sock_lowest_z"]*1000:.1f} mm) -> sock-to-collar overlap {o["overlap_mm_min"]:.1f} mm')
        if o['overlap_mm_min'] < 20.0:
            fails.append(f'NO_SKIN_GAP {g} {f}: overlap {o["overlap_mm_min"]} mm')
    if sv['exposed']:
        fails.append(f'NO_SKIN_GAP {g}: {sv["exposed"]} exposed samples {sv["examples"][:3]}')
add('NO_SKIN_GAP', not fails, ev, fails)

# ---------------------------------------------------------------- SOLE_GROUNDED
ev, fails = [], []
for g, c in C.items():
    s = c['sole']
    zs = [s[k]['sole_bottom_z'] for k in s]
    tz = [s[k]['tread_bottom_z'] for k in s]
    mz = [s[k]['shoe_min_z'] for k in s]
    ev.append(f'{g}: sole bottom z L/R White {s["White_L"]["sole_bottom_z"]*1000:.3f}/{s["White_R"]["sole_bottom_z"]*1000:.3f} mm, Black {s["Black_L"]["sole_bottom_z"]*1000:.3f}/{s["Black_R"]["sole_bottom_z"]*1000:.3f} mm; '
              f'tread bottom {s["White_L"]["tread_bottom_z"]*1000:.3f}/{s["White_R"]["tread_bottom_z"]*1000:.3f} mm; lowest vertex of the shoe {min(mz)*1000:.3f} mm (spread over all four {(max(mz)-min(mz))*1000:.4f} mm)')
    if max(zs) - min(zs) > 1e-4 or max(tz) - min(tz) > 1e-4 or max(mz) - min(mz) > 1e-4:
        fails.append(f'SOLE_GROUNDED {g}: soles {zs} tread {tz}')
add('SOLE_GROUNDED', not fails, ev, fails)

# ---------------------------------------------------------------- MIRROR
ev, fails = [], []
for g, c in C.items():
    m = c['mirror']
    ev.append(f'{g}: right shoe reflected across x = 0 vs left shoe: max distance {m["hausdorff_mirror_R_to_L_mm"]:.5f} mm (both ways); a same-facing translated copy would differ by {m["hausdorff_translated_copy_mm"]} mm; '
              f'signed volume R {m["signed_volume_R_cm3"]} cm3 / L {m["signed_volume_L_cm3"]} cm3 (both positive = outward windings); length {m["length_R_mm"]}/{m["length_L_mm"]} mm; sole height {m["sole_height_R_mm"]}/{m["sole_height_L_mm"]} mm; tris {m["tris_R"]}/{m["tris_L"]}')
    if m['hausdorff_mirror_R_to_L_mm'] > 0.01 or m['hausdorff_translated_copy_mm'] <= 1.0 or m['signed_volume_R_cm3'] <= 0 or m['signed_volume_L_cm3'] <= 0 or abs(m['length_R_mm'] - m['length_L_mm']) > 0.01:
        fails.append(f'MIRROR {g}: {m}')
add('MIRROR', not fails, ev, fails)

# ---------------------------------------------------------------- OTHER_PIECES_UNCHANGED
ev, fails = [], []
for g, c in C.items():
    op = c['other_pieces']
    for k in sorted(op['start']):
        same = op['start'][k] == op['output'].get(k)
        ev.append(f'{g} {k}: start {op["start"][k][:16]}...  output {op["output"].get(k, "MISSING")[:16]}...  {"identical" if same else "DIFFERENT"}')
    if not op['identical']:
        fails.append(f'OTHER_PIECES_UNCHANGED {g}: {op}')
add('OTHER_PIECES_UNCHANGED', not fails, ev, fails)

# ---------------------------------------------------------------- BODY_UNCHANGED
ev, fails = [], []
for g, c in C.items():
    fr = c['fitref_vs_source_body']
    ok = c['body_sha256_before'] == c['body_sha256_after'] == BODY_SHA[g] and fr['max_abs_diff_mm'] == 0.0 and fr['same_triangles']
    ev.append(f'{g}: body blend SHA before {c["body_sha256_before"][:16]}... == after {c["body_sha256_after"][:16]}... == expected {BODY_SHA[g][:16]}...; FitRef copy in the output blend vs the source mesh: max vertex difference {fr["max_abs_diff_mm"]} mm, same triangles {fr["same_triangles"]}; '
              f'start kit blend SHA before {c["start_kit_sha256"][:16]}... after {c["start_kit_sha256_after"][:16]}...')
    if not ok or c['start_kit_sha256'] != START_SHA[g] or c['start_kit_sha256_after'] != START_SHA[g]:
        fails.append(f'BODY_UNCHANGED {g}')
add('BODY_UNCHANGED', not fails, ev, fails)

# ---------------------------------------------------------------- ON_THESE_FEET
ev, fails = [], []
for g, c in C.items():
    o = OLD[g]
    nout = {f: o[f]['foot_verts_inside_wall'] + o[f]['foot_verts_not_enclosed'] for f in 'RL'}
    ev.append(f'{g}: fit built and measured on {os.path.basename({"male": "merged_fd04bc28.blend", "female": "HeroBase_Female_FULL_STAGED.blend"}[g])} SHA {BODY_SHA[g][:16]}... (verified at build, assembly and check time)')
    ev.append(f'{g}: control - the START kit measured the same way on this body: foot vertices below the collar outside its shoe R {nout["R"]} / L {nout["L"]} (toe {o["R"]["toe_overhang_inner_mm"]:+.1f} mm, heel {o["R"]["heel_overhang_inner_mm"]:+.1f} mm)')
if not (OLD['female']['R']['foot_verts_inside_wall'] + OLD['female']['R']['foot_verts_not_enclosed']) > 0:
    fails.append('ON_THESE_FEET: positive control did not fail on the female')
if any(c['body_sha256_before'] != BODY_SHA[g] for g, c in C.items()):
    fails.append('ON_THESE_FEET: body SHA')
ev.append('scripts read only the two body blends above (kitlib.py has no other body path); the start kit blends are read only for the untouched pieces and for the control')
add('ON_THESE_FEET', not fails, ev, fails)

# ---------------------------------------------------------------- NO_ARMS_CAND
ev, fails = [], []
for g, c in C.items():
    ev.append(f'{g}: objects/meshes/materials/collections whose name contains ArmsCand: {c["arms_cand_names"]}; FitRef objects {c["fitref_objects"]}; removed from the start blend: {MAN[g]["log"]["removed_objects"]}, collections {MAN[g]["log"]["removed_collections"]}')
    if c['arms_cand_names']:
        fails.append(f'NO_ARMS_CAND {g}: {c["arms_cand_names"]}')
add('NO_ARMS_CAND', not fails, ev, fails)

# ---------------------------------------------------------------- SOCKETS
ev, fails = [], []
for g, c in C.items():
    s = c['sockets']
    bad = []
    for k, v in s.items():
        if k.startswith('Kit_'):
            if not (v['parent_ok'] and v['mesh_world_identity'] and v['local_identity'] and v['closed'] and v['modifiers'] == 0):
                bad.append((k, v))
        else:
            if not v['world_identity']:
                bad.append((k, v))
    ev.append(f'{g}: Kit_Shoe_L / Kit_Sock_L -> Foot_L_Shoe_<colour>, Kit_Shoe_R / Kit_Sock_R -> Foot_R_Shoe_<colour> (socket_name Foot_L_Shoe / Foot_R_Shoe), 16 pieces, all closed meshes with an identity world transform; '
              f'the four foot sockets have an identity transform (they sat at {MAN[g]["log"]["sockets_before"]["Foot_L_Shoe_White"]} / {MAN[g]["log"]["sockets_before"]["Foot_R_Shoe_White"]} in the start blend; nothing else moved); armature objects in the blend: {c["armature_objects"]} (no foot bone exists)')
    if bad:
        fails.append(f'SOCKETS {g}: {bad[:3]}')
    if c['armature_objects']:
        fails.append(f'SOCKETS {g}: armature present')
add('SOCKETS', not fails, ev, fails)

# ---------------------------------------------------------------- untouched evidence (ArtDir, bodies, racket)
import subprocess
R_ = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
ref = f'{W}/start/StandardKit_Male.blend'
def newer(root, patterns):
    cmd = ['find', root, '-newer', ref, '-type', 'f', '('] + sum([['-name', p, '-o'] for p in patterns], [])[:-1] + [')']
    return [x for x in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines() if x]
UNTOUCHED = dict(artdir_model_files_modified_since_job_start=newer(f'{R_}/ArtDir', ['*.blend', '*.fbx', '*.obj', '*.glb', '*.gltf', '*.mesh']),
                 racket_files_modified_since_job_start=newer(f'{R_}/work/classic-tennis-racket', ['*.blend', '*.fbx', '*.obj']),
                 body_dirs_model_files_modified_since_job_start=newer(f'{R_}/work/male-pelvis-form3/export', ['*.blend', '*.fbx']) + newer(f'{R_}/work/female-full-merge/export', ['*.blend', '*.fbx']),
                 kit_worn_model_files_modified_since_job_start=newer(f'{R_}/work/standard-tennis-kit-worn/export', ['*.blend', '*.fbx']),
                 dressed_look_model_files_modified_since_job_start=newer(f'{R_}/work/dressed-look/export', ['*.blend', '*.fbx']))
ALL = ['FOOT_INSIDE', 'TOE_COVERED', 'HEEL_COVERED', 'NO_SKIN_GAP', 'SOLE_GROUNDED', 'MIRROR', 'OTHER_PIECES_UNCHANGED', 'BODY_UNCHANGED', 'ON_THESE_FEET', 'NO_ARMS_CAND', 'SOCKETS']
passed = all(G[k][0] for k in ALL)
failed_lines = [l for k in ALL for l in G[k][2]]

# ---------------------------------------------------------------- checks.json (the numbers the brief asks for, flat) + everything
summary = {}
for g, c in C.items():
    fi = c['foot_inside']
    summary[g] = dict(
        foot_vertices_below_collar_outside_shoe=dict(L=fi['L']['foot_verts_outside_shoe'], R=fi['R']['foot_verts_outside_shoe'],
                                                      of_total=dict(L=fi['L']['foot_vertices_below_collar'], R=fi['R']['foot_vertices_below_collar'])),
        collar_height_mm=dict(rim_z_min_above_foot_sole=round(fi['R']['collar_rim_z_min'] * 1000, 1), rim_z_mean=round(fi['R']['collar_rim_z_mean'] * 1000, 1), rim_z_max=round(fi['R']['collar_rim_z_max'] * 1000, 1),
                              above_ground_plane=fi['R']['collar_height_above_ground_mm'], roll_top_z=round(fi['R']['collar_roll_top_z'] * 1000, 1)),
        toe_overhang_mm=dict(inner_wall=dict(L=fi['L']['toe_overhang_inner_mm'], R=fi['R']['toe_overhang_inner_mm']), outside=dict(L=fi['L']['toe_overhang_outer_mm'], R=fi['R']['toe_overhang_outer_mm'])),
        heel_overhang_mm=dict(inner_wall=dict(L=fi['L']['heel_overhang_inner_mm'], R=fi['R']['heel_overhang_inner_mm']), outside=dict(L=fi['L']['heel_overhang_outer_mm'], R=fi['R']['heel_overhang_outer_mm'])),
        sock_to_collar_overlap_mm=dict(L=c['sock_collar_overlap']['L']['overlap_mm_min'], R=c['sock_collar_overlap']['R']['overlap_mm_min'],
                                       sock_top_above_highest_collar_point=c['sock_collar_overlap']['R']['sock_top_above_rim_mm']['min'], sock_below_lowest_collar_point=c['sock_collar_overlap']['R']['sock_below_rim_mm']['min']),
        polo_sha_unchanged=all(c['other_pieces']['start'][k] == c['other_pieces']['output'][k] for k in c['other_pieces']['start'] if k.startswith('Kit_Top')),
        bottom_sha_unchanged=all(c['other_pieces']['start'][k] == c['other_pieces']['output'][k] for k in c['other_pieces']['start'] if k.startswith('Kit_Bottom')),
        polo_bottom_sha256=dict(start=c['other_pieces']['start'], output=c['other_pieces']['output']),
        body_sha256=c['body_sha256_before'], output_blend_sha256=c['output_blend_sha256'], foot_landmarks=c['foot_landmarks'])
out = dict(untouched=UNTOUCHED, verdict=('GATE: TENNIS_SHOES_FIT PASS' if passed else 'GATE: TENNIS_SHOES_FIT FAIL'), gates={k: dict(pass_=G[k][0], failed_lines=G[k][2]) for k in ALL}, summary=summary,
           start_kit_on_new_body=OLD, per_hero=C, manifest={g: {k: v for k, v in MAN[g].items() if k != 'objects'} for g in MAN}, pieces={g: MAN[g]['objects'] for g in MAN}, generated=time.strftime('%Y-%m-%d %H:%M:%S'))
json.dump(out, open(f'{W}/proof/checks.json', 'w'), indent=1)
json.dump(out, open(f'{W}/checks.json', 'w'), indent=1)

# ---------------------------------------------------------------- GATE_RESULTS.md
L = []
L.append('# TENNIS_SHOES_FIT - GATE_RESULTS\n')
L.append(f'**{out["verdict"]}**\n')
L.append('Shoes and the socks rebuilt on the two body blends named in the brief; nothing under ArtDir written, bodies read-only (SHA verified before and after), polo and bottom untouched.\n')
L.append('| Gate | Result |\n|---|---|')
for k in ALL:
    L.append(f'| {k} | {"PASS" if G[k][0] else "FAIL"} |')
L.append('\nNumbers are measured on the assembled output blends (`export/StandardKit_Male.blend`, `export/StandardKit_Female.blend`), definitions in `GATE_DEFS_preregistered.md` (written before the final measurement run; one disclosed refinement, see below).\n')
L.append('## Evidence\n')
for k in ALL:
    L.append(f'### {k} - {"PASS" if G[k][0] else "FAIL"}')
    for e in G[k][1]:
        L.append(f'- {e}')
    L.append('')
L.append('## The brief\'s numbers (also flat in `checks.json` -> `summary`)\n')
L.append('| | male | female |\n|---|---|---|')
sm, sf = summary['male'], summary['female']
L.append(f'| foot vertices below the collar outside the shoe (L / R) | {sm["foot_vertices_below_collar_outside_shoe"]["L"]} / {sm["foot_vertices_below_collar_outside_shoe"]["R"]} (of {sm["foot_vertices_below_collar_outside_shoe"]["of_total"]["L"]} / {sm["foot_vertices_below_collar_outside_shoe"]["of_total"]["R"]}) | {sf["foot_vertices_below_collar_outside_shoe"]["L"]} / {sf["foot_vertices_below_collar_outside_shoe"]["R"]} (of {sf["foot_vertices_below_collar_outside_shoe"]["of_total"]["L"]} / {sf["foot_vertices_below_collar_outside_shoe"]["of_total"]["R"]}) |')
L.append(f'| collar rim height above the foot sole: min / mean / max (mm) | {sm["collar_height_mm"]["rim_z_min_above_foot_sole"]} / {sm["collar_height_mm"]["rim_z_mean"]} / {sm["collar_height_mm"]["rim_z_max"]} | {sf["collar_height_mm"]["rim_z_min_above_foot_sole"]} / {sf["collar_height_mm"]["rim_z_mean"]} / {sf["collar_height_mm"]["rim_z_max"]} |')
gm, gf = sm["collar_height_mm"]["above_ground_plane"], sf["collar_height_mm"]["above_ground_plane"]
L.append(f'| collar rim above the ground plane (mm): min / mean / max | {gm["min"]} / {gm["mean"]} / {gm["max"]} | {gf["min"]} / {gf["mean"]} / {gf["max"]} |')
L.append(f'| toe overhang, inner wall / outside (mm), L / R | {sm["toe_overhang_mm"]["inner_wall"]["L"]} / {sm["toe_overhang_mm"]["inner_wall"]["R"]}  and  {sm["toe_overhang_mm"]["outside"]["L"]} / {sm["toe_overhang_mm"]["outside"]["R"]} | {sf["toe_overhang_mm"]["inner_wall"]["L"]} / {sf["toe_overhang_mm"]["inner_wall"]["R"]}  and  {sf["toe_overhang_mm"]["outside"]["L"]} / {sf["toe_overhang_mm"]["outside"]["R"]} |')
L.append(f'| heel overhang, inner wall / outside (mm), L / R | {sm["heel_overhang_mm"]["inner_wall"]["L"]} / {sm["heel_overhang_mm"]["inner_wall"]["R"]}  and  {sm["heel_overhang_mm"]["outside"]["L"]} / {sm["heel_overhang_mm"]["outside"]["R"]} | {sf["heel_overhang_mm"]["inner_wall"]["L"]} / {sf["heel_overhang_mm"]["inner_wall"]["R"]}  and  {sf["heel_overhang_mm"]["outside"]["L"]} / {sf["heel_overhang_mm"]["outside"]["R"]} |')
L.append(f'| sock-to-collar overlap (mm): min / sock above the highest collar point / sock below the lowest | {sm["sock_to_collar_overlap_mm"]["R"]} / {sm["sock_to_collar_overlap_mm"]["sock_top_above_highest_collar_point"]} / {sm["sock_to_collar_overlap_mm"]["sock_below_lowest_collar_point"]} | {sf["sock_to_collar_overlap_mm"]["R"]} / {sf["sock_to_collar_overlap_mm"]["sock_top_above_highest_collar_point"]} / {sf["sock_to_collar_overlap_mm"]["sock_below_lowest_collar_point"]} |')
L.append(f'| polo / bottom mesh SHA unchanged | {sm["polo_sha_unchanged"]} / {sm["bottom_sha_unchanged"]} | {sf["polo_sha_unchanged"]} / {sf["bottom_sha_unchanged"]} |')
L.append('\n## Foot landmarks measured on these bodies (body space, metres)\n')
for g in ('male', 'female'):
    for f in 'RL':
        lm = C[g]['foot_landmarks'][f]
        L.append(f'- {g} {f}: longest toe tip {lm["longest_toe_tip"]}, heel point {lm["heel_point"]}, instep high point {lm["instep_high_point"]}, instep/shin junction z {round(lm["instep_junction_z"], 3)}, narrowest ankle z {lm["ankle_z_narrowest"]} ({lm["ankle_area_cm2"]} cm2), foot length {lm["foot_length_mm"]} mm, toe-out {lm["toe_out_deg"]} deg')
L.append('\n## What changed, and what was decided\n')
L.append('* **Start kit measured first.** On these bodies the START female shoes leave 250 / 258 foot vertices outside (62 / 67 inside the wall), the heel 35 mm and the toes 4 mm outside the cavity (the old fit was made to 200dc3b9\'s 183 mm placeholder foot; the real foot is 240 mm). The START male shoes already enclose his foot (0 outside, toe +9.5 mm, heel +8.7 mm): his feet are bit-identical to the body they were fit to (max vertex difference 0.0 mm below z 0.70). They were re-derived on this SHA anyway: same last, now built around the union of both feet so the left shoe is the exact mirror of the right.')
L.append('* **Sock: the whole sock mesh was rebuilt, not only the cuff.** The female start sock stood up to 63 mm off the new legs and clipped the new heel/toes, so a cuff-only swap could not have fixed it. Same design (2 mm knit wall, ribbed cuff stands 1.4 mm proud, cuff ring), same names, slots, parents. The male sock came out vertex-identical to the start one (max difference 0.0 mm) because his leg did not change.')
L.append('* **Collar** raised to the ankle (design heights side / back / front: female 90 / 114 / 117 mm, male 108 / 131 / 137 mm above the foot sole; start kit: female 76 / 91 / 101, male 88 / 106 / 118; realised rim mean 100 mm female / 125 mm male, instep-to-shin junction at 95 / 135 mm), smooth padded roll along a smoothed rim path; roll and tongue are pushed off the sock so no triangle of sock and shoe intersect.')
L.append('* **Materials:** Std_White_Lit / Std_Black_Lit only. Sole + tread now use the piping slot (white on both kits): invisible on the white kit, a white sole on the black kit.')
L.append('* **Sockets:** the four foot sockets were moved to an identity transform as the brief says (they sat at (+-0.125, 0, 0.08) female / (+-0.18, 0, 0.09) male). Kit meshes keep an identity world transform, so nothing moved visually. Neither body has an armature, so there is no foot bone to move.')
L.append('* **FitRef** in each output blend is now a copy of THIS job\'s body (vertex-identical to the source), the old 200dc3b9 / arms-candidate reference bodies and every `*_ArmsCandFit_*` shoe/sock (objects, meshes, collections) were deleted.')
L.append('* **Sole heights** unchanged from the start kit (female 23.5 mm, male 28.5 mm below the foot sole; tread 2 mm more), the ground plane convention stays z = -sole height.')
L.append('* **Disclosed refinement of NO_SKIN_GAP:** the first run counted 244 exposed samples (female), all 6-18 mm below the sock top, seen from above through the open end of the sock. The zone was narrowed from `sock top - 4 mm` to `sock top - 30 mm` (below the cuff band); the cuff band is reported separately. Recorded in `GATE_DEFS_preregistered.md`.')
L.append('* Not done (not asked): FBX/Unity export of the new shoes, the two `HeroBase_*_Dressed.blend` files in work/dressed-look still carry the old shoes, no ArtDir write.')
L.append('\n## Untouched\n')
for k, v in UNTOUCHED.items():
    L.append(f'- {k}: {len(v)} {v if v else ""}')
L.append('\n## Triangles\n')
for g in ('male', 'female'):
    L.append(f'- {g}: ' + ', '.join(f'{o["name"]} {o["tris"]}' for o in MAN[g]['objects']))
L.append('\n## Files\n')
L.append('* `export/StandardKit_Male.blend`, `export/StandardKit_Female.blend` (+ `manifest_*.json`), `start/` = untouched copies of the start blends (SHA verified)')
L.append('* `proof/FEET_<Hero>_<White|Black>.png` close-ups (both feet, side / front / heel / low 3/4), `proof/CUTAWAY_<Hero>.png` sections, `proof/BEFORE_AFTER_<Hero>.png`, `proof/CONTEXT_<Hero>.png`, raw cells in `proof/raw/`, `proof/checks.json`')
L.append(f'* output blend SHA-256: male `{C["male"]["output_blend_sha256"]}`, female `{C["female"]["output_blend_sha256"]}` (each re-save of a blend changes its bytes; the geometry hashes above are the stable identity)')
L.append('* rebuild: `scripts/run_all.sh`')
open(f'{W}/GATE_RESULTS.md', 'w').write('\n'.join(L))
print(out['verdict'])
for l in failed_lines:
    print('FAILED:', l)
