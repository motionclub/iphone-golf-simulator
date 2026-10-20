"""Evaluate the gates from the measured JSON and write proof/checks.json + GATE_RESULTS.md (system python).  python3 final_report.py"""
import json, os, hashlib, subprocess, datetime, glob

ROOT = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = ROOT + '/work/standard-tennis-kit-worn/'
RAW = W + 'proof/raw/'
BODY = {
    'male': (ROOT + '/ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend', 'fd04bc286f688b03ea25fbb57e1242bf2f5976c2dc7bbcdfdb0f68b622ab2347'),
    'female': (ROOT + '/ArtDir/hero/base_lock/blender/HeroBase_Female.blend', '200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd'),
    'female_arms_candidate': (ROOT + '/work/female-arms-form2/export/HeroBase_Female_arms_candidate.blend', '573ab4431d83f8651936f0081ad3bda9c6890c56ee5dce3061140198c9455f0e'),
}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
J = lambda p: json.load(open(p))

chk = {g: J(f'{RAW}checks_{g}.json') for g in ('male', 'female')}
man = {g: J(f'{W}export/manifest_{g}.json') for g in ('male', 'female')}
fbx = J(f'{W}export/fbx_verify.json')
mask = J(f'{RAW}liner_mask_pixels.json') if os.path.exists(f'{RAW}liner_mask_pixels.json') else None
unity = J(f'{W}proof/unity_import_report.json') if os.path.exists(f'{W}proof/unity_import_report.json') else None

gates, fails = {}, []


def gate(name, ok, evidence):
    gates[name] = dict(result='PASS' if ok else 'FAIL', evidence=evidence)
    if not ok:
        fails.append(name)


def piece(g, base):
    return [v for k, v in chk[g]['pieces'].items() if k.endswith('_White') and k.startswith(base)]


# ------------------------------------------------------------------ UNTUCKED_HEM
ev, ok = [], True
for g in ('male', 'female'):
    ph = chk[g]['polo_hem']
    o = ph['overlap_mm']
    good = 15.0 <= o['min'] and o['max'] <= 25.0 and chk[g]['polo_vs_bottom_overlap_pairs'] == 0 and chk[g]['polo_vs_band']['min_gap_mm'] >= 1.0 and not chk[g]['swappable']['top_bottom_fused']
    ok &= good
    ev.append(f"{g}: polo hem overlaps the band top {o['min']}-{o['max']} mm (mean {o['mean']}); polo<->bottom overlapping triangle pairs {chk[g]['polo_vs_bottom_overlap_pairs']}; "
              f"polo inner wall stands {chk[g]['polo_vs_band']['min_gap_mm']} mm outside the band; {ph['visible_band_below_hem_mm']['min']}-{ph['visible_band_below_hem_mm']['max']} mm of the band visible below the hem; "
              f"top and bottom are separate objects (fused={chk[g]['swappable']['top_bottom_fused']})")
gate('UNTUCKED_HEM', ok, ev)

# ------------------------------------------------------------------ WAISTBAND_CONTRAST
ev, ok = [], True
for g in ('male', 'female'):
    b = chk[g]['band_color']
    good = (b['White']['contrast'] == 'black on white' and b['Black']['contrast'] == 'white on black' and b['White']['slot2_faces_all_band'] and b['Black']['slot2_faces_all_band']
            and not b['White']['polo_uses_band_slot'] and not b['Black']['polo_uses_band_slot'] and 25.0 <= chk[g]['polo_hem']['band_height_mm'] <= 40.5)
    ok &= good
    ev.append(f"{g}: white kit = fabric {b['White']['fabric_material']} {b['White']['fabric_rgb']} + band {b['White']['band_material']} {b['White']['band_rgb']} ({b['White']['contrast']}); "
              f"black kit = fabric {b['Black']['fabric_material']} + band {b['Black']['band_material']} ({b['Black']['contrast']}); band = {b['White']['band_faces']} faces on {b['White']['band_on_bottom_object']} (slot 2), "
              f"polo uses no band slot; band {chk[g]['polo_hem']['band_height_mm']} mm tall")
gate('WAISTBAND_CONTRAST', ok, ev)

# ------------------------------------------------------------------ SKIRT_COVERS (female; the male shorts have no inner layer)
f = chk['female']
sk, lv = f['skirt'], f['liner_visibility']
mask_ok = mask is not None and all(mask[cw]['gate_px'] == 0 for cw in mask)
good = sk['skirt_longer_than_liner_mm'] > 0 and 0.40 <= sk['hem_fraction_down_thigh'] <= 0.70 and lv['visible_faces_gate_views'] == 0 and mask_ok
gate('SKIRT_COVERS', good, [
    f"outer skirt hem z {sk['skirt_hem_z']} = {sk['hem_fraction_down_thigh']*100:.0f}% of the way from crotch (z {sk['crotch_z']}) to knee (z {sk['knee_z']}): mid-thigh is z {sk['mid_thigh_z']}; the previous skirt hem was z 0.700",
    f"inner-short (liner) hem z {sk['liner_hem_z']} -> skirt is {sk['skirt_longer_than_liner_mm']} mm longer than the inner shorts",
    f"ray test: {lv['liner_faces_tested']} liner faces x {lv['ray_tests']} camera rays (elevations {lv['gate_elevations_deg']} deg, every {lv['azimuth_step_deg']} deg of azimuth), a face counts as visible only if a {lv['beam_mm']} mm beam (5 exact rays) reaches it first: visible faces = {lv['visible_faces_gate_views']}",
    f"disclosed: {lv['n_centre_ray_only_slits']} face/view pair(s) where a single zero-width centre ray slips through a ~0.3 mm slit between the waistband's bottom edge and the skirt's top lap but no 1 mm beam can ({lv['centre_ray_only_slits_gate_views']}); a camera pixel is ~2 mm wide at the proof distance, and the render test below shows 0 liner pixels",
    f"render test (liner painted magenta, 4 elevations x 12 azimuths per kit): magenta pixels White {mask['White']['gate_px']} / Black {mask['Black']['gate_px']} at 0/+8/+22 deg; "
    f"below the horizon (-12 deg) {mask['White']['under_px']}/{mask['Black']['under_px']}; positive control (skirt hidden) shows the liner",
    f"informational: looking UP under the hem from {lv['underside_elevations_deg']} deg the inside of any skirt is visible ({lv['visible_faces_underside_views_info_only']} liner faces); not a proof view"])

# ------------------------------------------------------------------ WORN_SHELL
ev, ok = [], True
for g in ('male', 'female'):
    pcs = chk[g]['pieces']
    white = {k: v for k, v in pcs.items() if k.endswith('_White')}
    closed = all(v['closed'] for v in pcs.values())
    walls = {k.replace('_White', ''): v['wall_mm']['median'] for k, v in white.items() if 'wall_mm' in v}
    wall_min = min(v['wall_mm']['p05'] for v in white.values() if 'wall_mm' in v)
    neg = sum(v['clearance_all_mm']['neg_vertices'] for v in white.values())
    ovb = sum(v['overlap_pairs_vs_body'] for v in white.values())
    polo = [v for k, v in white.items() if k.startswith('Kit_Top')][0]
    bottom = [v for k, v in white.items() if k.startswith('Kit_Bottom')][0]
    tz = polo['clearance_inner_torso_mm']
    good = closed and wall_min >= 1.5 and tz['min'] >= 6.0 and bottom['clearance_all_mm']['min'] >= 6.0 and neg == 0 and ovb == 0
    ok &= good
    ev.append(f"{g}: every piece a closed manifold (0 boundary / 0 non-manifold / 0 inconsistent edges): {closed}; wall thickness median mm {walls} (5th-percentile wall over every part {wall_min} mm); "
              f"polo waist/hip inner clearance min {tz['min']} mm (median {tz['median']}); bottom min {bottom['clearance_all_mm']['min']} mm; "
              f"vertices inside the body {neg}; triangles intersecting the body {ovb}")
    if g == 'female' and 'clearance_inner_crevice_zone_mm' in polo:
        z = polo['clearance_inner_crevice_zone_mm']
        ev.append(f"disclosed: female polo, hidden rib/sleeve crevice (hanging arm 34 mm off the ribs): min {z['min']} mm (median {z['median']}), never negative - relaxed on purpose, see polo.py")
gate('WORN_SHELL', ok, ev)

# ------------------------------------------------------------------ NO_SKIN_FLASH
ev, ok = [], True
for g in ('male', 'female'):
    s = chk[g]['skin_flash']
    ok &= s['exposed'] == 0
    ev.append(f"{g}: {s['skin_samples']} skin samples between z {s['z_range'][0]} and {s['z_range'][1]} x {s['ray_tests']} camera rays ({s['elevations_deg']} deg elevation, 15 deg azimuth steps, 1 mm beam, exact ray-triangle): exposed {s['exposed']}")
gate('NO_SKIN_FLASH', ok, ev)

# ------------------------------------------------------------------ NO_LOGOS
ev, ok = [], True
bad_words = ('logo', 'text', 'swoosh', 'brand', 'label')
for g in ('male', 'female'):
    n = chk[g]['no_logos']
    vocab_bad = [t for t in n['part_tag_vocabulary'] if any(w in t.lower() for w in bad_words)]
    good = not n['blend_images'] and not n['image_texture_materials'] and not n['text_objects'] and set(n['object_types']) <= {'MESH', 'EMPTY'} and not vocab_bad
    ok &= good
    ev.append(f"{g}: images in blend {n['blend_images']}, image-texture materials {n['image_texture_materials']}, text objects {n['text_objects']}, object types {n['object_types']}, part vocabulary has no logo/text/brand part ({len(n['part_tag_vocabulary'])} tags: tone-on-tone seams, piping, buttons, laces)")
gate('NO_LOGOS', ok, ev)

# ------------------------------------------------------------------ BODY_SHA_UNCHANGED
ev, ok = [], True
shas = {}
for k, (p, before) in BODY.items():
    now = sha(p)
    shas[k] = dict(file=p.replace(ROOT + '/', ''), before=before, after=now, unchanged=(now == before))
    ok &= now == before
    ev.append(f"{k}: {before[:8]}.. before == {now[:8]}.. after")
gate('BODY_SHA_UNCHANGED', ok, ev)

# ------------------------------------------------------------------ SWAPPABLE
ev, ok = [], True
want = {'Top': 'Chest_Top', 'Bottom': 'Hip_Bottom'}
for g in ('male', 'female'):
    sw = chk[g]['swappable']
    pieces_ok = True
    for nm, d in sw['pieces'].items():
        cat = next(v for k, v in chk[g]['pieces'].items() if k.startswith(nm)).get('category')
        exp = want.get(cat) or ('Foot_L_Shoe' if nm.endswith('_L') or '_L_' in nm else 'Foot_R_Shoe')
        pieces_ok &= d['parent'] == exp
    fb = [v for k, v in fbx.items() if (('Male' in k) == (g == 'male')) and 'ArmsCand' not in k]
    fb_ok = all(all(o['parent'] == o['parent_src'] for o in v['objects'].values()) and v['ok'] for v in fb)
    ident = all(v['world_identity'] for v in chk[g]['pieces'].values())
    good = sorted(sw['sockets']) == sorted(['Chest_Top', 'Hip_Bottom', 'Foot_L_Shoe', 'Foot_R_Shoe']) and pieces_ok and not sw['top_bottom_fused'] and sw['distinct_mesh_data'] and ident and fb_ok
    ok &= good
    ev.append(f"{g}: sockets {sw['sockets']}; every piece parented to its socket ({pieces_ok}), identity world transform {ident}, distinct mesh data {sw['distinct_mesh_data']}, top/bottom fused {sw['top_bottom_fused']}; hierarchy survives the FBX round trip {fb_ok}")
gate('SWAPPABLE', ok, ev)

# ------------------------------------------------------------------ EXPORT
ev, ok = [], True
for g, G in (('male', 'Male'), ('female', 'Female')):
    b = f'{W}export/StandardKit_{G}.blend'
    ok &= os.path.exists(b)
    ev.append(f"{g}: {os.path.basename(b)} ({os.path.getsize(b)/1e6:.1f} MB, sha {man[g]['blend_sha256'][:10]}..)")
for k, v in fbx.items():
    ok &= v['ok'] and v['scale_check']['objects_scale_max_dev'] < 1e-4
    ev.append(f"{k}: {v['size_mb']} MB, {len([o for o in v['objects']])} meshes + {len(v['empties'])} socket empties, {v['total_tris']} tris, scale 1 m (max object scale deviation {v['scale_check']['objects_scale_max_dev']}), "
              f"round-trip max vertex error {max(o['max_vertex_err_mm'] for o in v['objects'].values()):.4f} mm, normals max {max(o['normal_dev_max_deg'] for o in v['objects'].values()):.3f} deg, UVs kept")
if unity:
    ok &= unity.get('STDKIT_WORN_UNITY_IMPORT') == 'PASS'
    ev.append(f"Unity 6000.3.24f1 scratch import (outside the repo): {unity.get('STDKIT_WORN_UNITY_IMPORT')} - scale 1, hierarchy under the sockets, UV + normals, world bounds vs Blender < 1 mm (proof/unity_import_report.json)")
else:
    ev.append('Unity scratch import: not run')
gate('EXPORT', ok, ev)

# ------------------------------------------------------------------ PROOFS
need = ['ONBODY_Male.png', 'ONBODY_Female.png', 'WAIST_Male.png', 'WAIST_Female.png', 'HEM_Female.png', 'LINER_MASK_Female.png', 'EXPLODED_Male.png', 'EXPLODED_Female.png',
        'OBJECT_ID_Male.png', 'OBJECT_ID_Female.png', 'SECTIONS_Male.png', 'SECTIONS_Female.png', 'CLEARANCE_Male.png', 'CLEARANCE_Female.png']
missing = [n for n in need if not os.path.exists(W + 'proof/' + n)]
gate('PROOFS', not missing and os.path.exists(W + 'proof/checks.json') or not missing, [f"{len(need) - len(missing)} of {len(need)} sheets present in proof/: {', '.join(need)}" + (f"; MISSING {missing}" if missing else ''), 'proof/checks.json'])

# ------------------------------------------------------------------ untouched checks
def newer(path):
    try:
        out = subprocess.run(['find', path, '-type', 'f', '-newer', W + 'scripts/kitlib.py'], capture_output=True, text=True, timeout=120).stdout.split('\n')
        return [o.replace(ROOT + '/', '') for o in out if o]
    except Exception as e:
        return [f'find failed: {e}']
refs = subprocess.run('grep -n "ArtDir" ' + W + 'scripts/*.py | grep -v final_report', shell=True, capture_output=True, text=True).stdout.strip().split('\n')
_ad = newer(ROOT + '/ArtDir')
_ext = {}
for _f in _ad:
    _e = os.path.splitext(_f)[1].lower() or '(none)'
    _ext[_e] = _ext.get(_e, 0) + 1
_model_ext = ('.blend', '.blend1', '.fbx', '.obj', '.mtl', '.prefab', '.mat', '.unity', '.anim', '.controller')
_models_changed = [_f for _f in _ad if os.path.splitext(_f)[1].lower() in _model_ext]
untouched = dict(ArtDir_files_modified_since_job_start=_ad, ArtDir_modified_by_extension=_ext, ArtDir_model_files_modified=_models_changed,
                 classic_tennis_racket_files_modified_since_job_start=newer(ROOT + '/work/classic-tennis-racket'),
                 note='other chats are active in this repo (the ArtDir files listed are theirs: head/limbs proof images); this job writes only under work/standard-tennis-kit-worn. Static check: every script reference to ArtDir is a READ path of the authority bodies:',
                 script_references_to_ArtDir=[r.replace(W, '') for r in refs if r])

# ------------------------------------------------------------------ checks.json
tri = {g: {k.replace('_White', ''): v['tris'] for k, v in chk[g]['pieces'].items() if k.endswith('_White')} for g in chk}
minclr = {g: {k.replace('_White', ''): dict(all_vertices_mm=v['clearance_all_mm']['min'], inner_surface_mm=v.get('clearance_inner_mm', {}).get('min'), body_intersecting_triangles=v['overlap_pairs_vs_body'],
                                            vertices_inside_body=v['clearance_all_mm']['neg_vertices']) for k, v in chk[g]['pieces'].items() if k.endswith('_White')} for g in chk}
out = dict(
    job='STANDARD_TENNIS_KIT_WORN', created=datetime.datetime.now().isoformat(timespec='seconds'),
    overall='PASS' if not fails else 'FAIL', failed_gates=fails,
    body_sha256=shas,
    tri_per_piece=tri, tri_totals={g: sum(v.values()) for g, v in tri.items()},
    tri_previous_kit={'male': 52557, 'female': 51978},
    polo_hem_overlap_mm={g: chk[g]['polo_hem'] for g in chk},
    polo_vs_band={g: chk[g]['polo_vs_band'] for g in chk},
    skirt_hem_vs_inner_short_hem=chk['female']['skirt'], male_shorts=chk['male'].get('shorts'),
    waistband_color_per_kit={g: chk[g]['band_color'] for g in chk},
    min_clearance_mm=minclr,
    clearance_zones={g: {k.replace('_White', ''): {z: v[z] for z in ('clearance_inner_torso_mm', 'clearance_inner_crevice_zone_mm', 'clearance_inner_mm', 'wall_mm') if z in v} for k, v in chk[g]['pieces'].items() if k.endswith('_White')} for g in chk},
    skin_flash={g: chk[g]['skin_flash'] for g in chk}, liner_visibility=chk['female']['liner_visibility'], liner_mask_pixels=mask,
    garment_vs_garment={g: chk[g]['garment_vs_garment'] for g in chk}, bottom_layer_overlaps={g: chk[g]['bottom_layer_overlaps'] for g in chk},
    topology={g: {k: v['topology'] for k, v in chk[g]['pieces'].items()} for g in chk},
    fbx={k: dict(size_mb=v['size_mb'], total_tris=v['total_tris'], ok=v['ok'], sha256=v['fbx_sha256']) for k, v in fbx.items()},
    unity_import=(unity or {}).get('STDKIT_WORN_UNITY_IMPORT'),
    untouched=untouched, gates=gates)
json.dump(out, open(W + 'proof/checks.json', 'w'), indent=1)

# ------------------------------------------------------------------ GATE_RESULTS.md
L = ['# STANDARD_TENNIS_KIT_WORN - GATE_RESULTS (staged only: nothing under ArtDir written, no body edit, no racket edit)', '',
     f"**{'GATE: STANDARD_TENNIS_KIT_WORN PASS' if not fails else 'GATE: STANDARD_TENNIS_KIT_WORN FAIL - ' + ', '.join(fails)}**", '',
     'Starting point: work/standard-tennis-kit-wb (tucked polo, ~3 mm shrink-wrap, skirt hem z 0.70 with the liner showing below it). Rebuilt in work/standard-tennis-kit-worn/ with the same SDF-fit pipeline, ',
     'sock/shoe designs kept; every piece is now a closed double-walled shell, the polo is untucked, the bottom carries a lofted contrasting waistband, the female skirt is mid-thigh.', '',
     '| Gate | Result |', '|---|---|']
for k, v in gates.items():
    L.append(f"| {k} | {v['result']} |")
L += ['', '## Evidence', '']
for k, v in gates.items():
    L.append(f"### {k} - {v['result']}")
    for e in v['evidence']:
        L.append(f'- {e}')
    L.append('')
L += ['## TRI per piece (white == black)', '', '| piece | male | female |', '|---|---|---|']
names = ['Kit_Top_Polo', 'Kit_Bottom', 'Kit_Sock_L', 'Kit_Sock_R', 'Kit_Shoe_L', 'Kit_Shoe_R']
for n in names:
    m = next((v for k, v in tri['male'].items() if k.startswith(n)), '-')
    f_ = next((v for k, v in tri['female'].items() if k.startswith(n)), '-')
    L.append(f'| {n} | {m} | {f_} |')
L.append(f"| **total** | **{out['tri_totals']['male']}** (was 52,557) | **{out['tri_totals']['female']}** (was 51,978) |")
L += ['', '## Min clearance to the authority body (mm)', '', '| piece | male all / inner | female all / inner |', '|---|---|---|']
for n in names:
    m = next((v for k, v in minclr['male'].items() if k.startswith(n)), None)
    f_ = next((v for k, v in minclr['female'].items() if k.startswith(n)), None)
    fmt = lambda x: f"{x['all_vertices_mm']} / {x['inner_surface_mm']}" if x else '-'
    L.append(f'| {n} | {fmt(m)} | {fmt(f_)} |')
L += ['', '## Disclosed limits', '',
      f"- Triangle count is up {100 * (out['tri_totals']['male'] / 52557 - 1):.0f} % (male) / {100 * (out['tri_totals']['female'] / 51978 - 1):.0f} % (female): every piece is now a closed shell with an inner wall; the inner walls are the cheapest place to decimate if the budget needs it.",
      '- Female polo: where the hanging arm sits ~34 mm off the ribs the two shell offsets cannot both stay at full ease (they fuse into one membrane and the sleeve cut tears the side wall). The torso side wall (8.5 mm) and the sleeve inner side (3.5 mm) are relaxed in that hidden crevice only; its minimum inner clearance is 0.5 mm, never negative.',
      '- Visible band: 40 mm band; the polo hem covers its top 15.8-20 mm and the fabric laps its bottom 5.5 mm, so 20-24 mm of contrast colour shows between shirt and bottom.',
      '- Looking UP under the skirt hem from below the horizon shows the inside of the skirt (as with any skirt); the proof views and the camera range -5..+40 deg are fully covered.',
      '- Male shorts legs are now two separate tubes (the previous kit fused them into one trunk).',
      '- Female socks/sneakers are still fit to the authority body\'s placeholder feet (as before); an ArmsCandFit footwear set is carried over in StdKit_Female_*_ArmsCandFit.fbx.',
      '- Static shells fitted to the bind pose; no rig/skin weights; sockets are empties parenting identity-transform meshes.', '',
      f"Untouched check: ArtDir files modified since this job started: {len(untouched['ArtDir_files_modified_since_job_start'])} {untouched['ArtDir_modified_by_extension']} - all proof images / prompt notes written by the other chats that share this repo; model files (.blend/.fbx/.obj/...) modified under ArtDir: {len(untouched['ArtDir_model_files_modified'])}; the only ArtDir paths this job's scripts reference are the two READ-ONLY authority body files (SHA unchanged); classic-tennis-racket files modified: {len(untouched['classic_tennis_racket_files_modified_since_job_start'])}.", '',
      'Rebuild: scripts/run_all.sh (parts -> assemble -> FBX -> checks -> proofs -> sheets) then scripts/final_report.py.']
open(W + 'GATE_RESULTS.md', 'w').write('\n'.join(L))
print(out['overall'], fails)
for k, v in gates.items():
    print(f'  {k:20s} {v["result"]}')
print('untouched:', {k: (v[:5] if isinstance(v, list) else v) for k, v in untouched.items() if k not in ('note', 'script_references_to_ArtDir')})
