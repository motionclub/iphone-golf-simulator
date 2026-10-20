"""Roll the measurements up into checks.json and GATE_RESULTS.md against GATE_DEFS_preregistered.md.   python3 scripts/final_report.py
Inputs (all written by the stage scripts): data/gate1_*.json gate3_*.json sweep_*.json sole_*.json verify_kitfbx_*.json verify_repo.json gate2_prefab.json unity_gates.json build_*.json,
proof/unity/dressed_proof.json, logs/xcode_*.log, logs/locker_export (hero-mainstay/logs/locker_export.txt).  Thresholds are the pre-registered ones; nothing here is tuned."""
import glob
import json
import os
import re

W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/hero-dressed'
REPO = W.rsplit('/work/', 1)[0]
D = W + '/data'


def jl(p, default=None):
    try:
        return json.load(open(p))
    except Exception:
        return default


def read(p):
    try:
        return open(p, errors='ignore').read()
    except Exception:
        return ''


HEROES = ('male', 'female')
PIECES = ['Top', 'Bottom', 'Sock_L', 'Sock_R', 'Shoe_L', 'Shoe_R']
gates = {}
lines = []          # failed lines (only these go into the final reply)


def gate(name, ok, detail, failed_lines=()):
    gates[name] = dict(pass_=bool(ok), detail=detail, failed=list(failed_lines))
    if not ok:
        lines.extend(failed_lines or [name])


# ------------------------------------------------------------------------------------------------------------------------------ 1
g1 = {}
fl = []
unity = jl(D + '/unity_gates.json')
for h in HEROES:
    b = jl(f'{D}/gate1_{h}.json')
    v = jl(f'{D}/verify_kitfbx_{h}.json')
    u = next((s for s in (unity or {}).get('sexes', []) if s['sex'].lower() == h), None)
    g1[h] = dict(blender_pass=bool(b and b['pass_']), fbx_roundtrip_pass=bool(v and v['pass']),
                 unity_max_influences=max((p['maxInfluences'] for p in u['pieces']), default=None) if u else None, unity_weight_sum_err=max((p['weightSumErr'] for p in u['pieces']), default=None) if u else None,
                 blender_max_influences=max((p['max_influences'] for p in b['pieces'].values()), default=None) if b else None, blender_sum_err=max((p['sum_err_max'] for p in b['pieces'].values()), default=None) if b else None)
    if not g1[h]['blender_pass']:
        fl.append(f'1 KIT_SKINNED {h}: Blender source check failed')
    if not g1[h]['fbx_roundtrip_pass']:
        fl.append(f'1 KIT_SKINNED {h}: kit FBX round trip failed')
    if not u or g1[h]['unity_max_influences'] is None or g1[h]['unity_max_influences'] > 4 or g1[h]['unity_weight_sum_err'] > 1e-3:
        fl.append(f'1 KIT_SKINNED {h}: Unity import weights failed')
gate('1 KIT_SKINNED', not fl, g1, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 2
vr = jl(D + '/verify_repo.json')
gp = jl(D + '/gate2_prefab.json')
fl = []
if not vr or not vr['pass']:
    fl.append('2 BODY_UNCHANGED: clip FBX / staged blend hashes or art-directory judgement failed: ' + json.dumps({k: vr.get(k) for k in ('clip_fbx_work', 'clip_fbx_unity', 'blends_equal')} if vr else 'missing'))
if not gp or not gp['pass']:
    fl.append('2 BODY_UNCHANGED: prefab fingerprint differs outside the six kit nodes')
gate('2 BODY_UNCHANGED', not fl, dict(repo=vr and {k: vr[k] for k in ('clip_fbx_work', 'clip_fbx_unity', 'blends_equal')}, prefab=gp), fl)

# ------------------------------------------------------------------------------------------------------------------------------ 3
RIGID = {'Sock_L', 'Sock_R', 'Shoe_L', 'Shoe_R'}
g3 = {}
fl = []
for h in HEROES:
    g = jl(f'{D}/gate3_{h}.json')
    sw = jl(f'{D}/sweep_{h}.json')
    if not g:
        fl.append(f'3 FOLLOWS_BODY {h}: no measurement')
        continue
    g3[h] = dict(summary=g['summary'], sweep=sw and sw['summary'], zone_n=g.get('zone_n'))
    for p in PIECES:
        s = g['summary'][p]
        if not s['pass_']:
            why = []
            t = s['thresholds']
            if s['poke_max_mm'] > t['poke_max']:
                why.append(f'poke max {s["poke_max_mm"]:.1f} > {t["poke_max"]:.0f} mm')
            if s['poke_p99_worst_mm'] > t['poke_p99']:
                why.append(f'poke p99 {s["poke_p99_worst_mm"]:.1f} > {t["poke_p99"]:.0f} mm')
            if s['float_max_mm'] > t['float_max']:
                why.append(f'float max {s["float_max_mm"]:.1f} > {t["float_max"]:.0f} mm')
            if s['float_p99_worst_mm'] > t['float_p99']:
                why.append(f'float p99 {s["float_p99_worst_mm"]:.1f} > {t["float_p99"]:.0f} mm')
            fl.append(f'3 FOLLOWS_BODY {h} {p}: ' + '; '.join(why) + f' (worst poke at {s["worst_poke_pose"]})')
gate('3 FOLLOWS_BODY', not fl, g3, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 4
fl = []
g4 = {}
if not unity:
    fl.append('4 UNITY_BIND: tests/unity_gates.json missing')
else:
    for s in unity['sexes']:
        g4[s['sex']] = dict(failures=s['failures'], rolesFound=s['rolesFound'], materialsOk=s['materialsOk'], max_pose_dev_mm=max(max(p['poseMaxMm']) for p in s['pieces']), max_bind_dev_mm=max(p['bindMaxMm'] for p in s['pieces']),
                            centroid_delta_mm=s['centroidDeltaMm'], unmatched=sum(p['unmatched'] for p in s['pieces']))
        for f_ in s['failures']:
            if 'role' in f_.lower() or 'colour' in f_.lower() or 'tint' in f_.lower() or 'SetKit' in f_ or 'default' in f_:
                continue
            fl.append('4 UNITY_BIND ' + f_)
gate('4 UNITY_BIND', not fl, g4, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 5
fl = []
g5 = {}
proof = jl(W + '/proof/unity/dressed_proof.json')
if unity:
    for s in unity['sexes']:
        g5[s['sex']] = dict(roles_found=s['rolesFound'], default_is_authored=s['defaultIsAuthored'], tint_ok=s['tintOk'])
        if s['rolesFound'] != 7:
            fl.append(f'5 ROLES_TINT {s["sex"]}: {s["rolesFound"]} of 7 role materials')
        if not s['defaultIsAuthored']:
            fl.append(f'5 ROLES_TINT {s["sex"]}: default is not the authored White kit')
        if not s['tintOk']:
            fl.extend(f'5 ROLES_TINT ' + f_ for f_ in s['failures'] if 'SetKit' in f_ or 'formula' in f_ or 'instance' in f_ or 'asset' in f_ or 'default' in f_)
else:
    fl.append('5 ROLES_TINT: unity_gates.json missing')
if proof:
    px = [r for r in proof['shots'] if r['file'].startswith('pixeltest_') and r['file'].endswith('_default.png')]
    g5['pixel_test_unity'] = [dict(file=r['file'], kitPixels=r['kitPixels'], changed=r['changed'], outsideMask=r['outsideMask']) for r in px]
    if len(px) != 2 or any(r['outsideMask'] != 0 or r['changed'] < 2000 for r in px):
        fl.append('5 ROLES_TINT: Unity pixel test (picks change only the kit): ' + json.dumps(g5['pixel_test_unity']))
else:
    fl.append('5 ROLES_TINT: Unity play-mode pixel test not run (proof/unity/dressed_proof.json missing)')
gate('5 ROLES_TINT', not fl, g5, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 6
fl = []
g6 = {}
lock = read(REPO + '/work/hero-mainstay/logs/locker_export.txt')
for h in ('Male', 'Female'):
    man = jl(f'{REPO}/GolfArcade/Unity/CharacterAssets/MatchHero_{h}.json')
    if not man:
        fl.append(f'6 SWIFT_MIRROR {h}: manifest missing')
        continue
    kit = [p for p in man['parts'] if p['kind'] == 'kit']
    roles = sorted({s['material'] for p in kit for s in p['submeshes']})
    g6[h] = dict(kit_parts=sorted(p['name'] for p in kit), roles=roles, swing_frames=len(man['swingFrames']))
    if len(kit) != 6 or len(roles) != 7:
        fl.append(f'6 SWIFT_MIRROR {h}: {len(kit)} kit parts, {len(roles)} roles in the manifest')
g6['cpu_skin_vs_bakemesh'] = re.findall(r'CPU skin vs Unity BakeMesh.*?: (Kit_\w+) max deviation ([\d.]+) mm', lock)
if not g6['cpu_skin_vs_bakemesh'] or any(float(x[1]) > 2 for x in g6['cpu_skin_vs_bakemesh']):
    fl.append('6 SWIFT_MIRROR: CPU skinning of the kit parts not verified (<= 2 mm) in the locker export log')
xl = ''.join(read(p) for p in sorted(glob.glob(W + '/logs/xcode_dressed*.log')))
cases = re.findall(r"Test Case '-\[GolfArcadeTests\.(\w+) (\w+)\]' (passed|failed)", xl)
g6['swift_tests'] = {f'{c}.{t}': r for c, t, r in cases}
need = ['DressedHeroSnapshotTests.testBothHeroesAreDressedInTheMirror', 'DressedHeroSnapshotTests.testDefaultKitIsTheAuthoredWhiteKit', 'DressedHeroSnapshotTests.testTintMathsMatchesTheUnitySide',
        'DressedHeroSnapshotTests.testPicksRecolourOnlyTheirRoles', 'DressedHeroSnapshotTests.testRecordDressedSnapshots', 'DressedHeroSnapshotTests.testRecordHostedDressedView']
for n in need:
    if g6['swift_tests'].get(n) != 'passed':
        fl.append(f'6 SWIFT_MIRROR: Swift test {n} = {g6["swift_tests"].get(n, "not run")}')
g6['swift_pixel_test'] = re.findall(r'\[DressedHero\] (\w+) (\w+): kit pixels (\d+), pixels changed by the picks (\d+), outside the kit mask (\d+)', xl)
g6['swift_proofs'] = sorted(os.path.basename(p) for p in glob.glob(W + '/proof/swift/*.png'))
if len(g6['swift_proofs']) < 12:
    fl.append(f'6 SWIFT_MIRROR: only {len(g6["swift_proofs"])} Swift proof images')
gate('6 SWIFT_MIRROR', not fl, g6, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 7
fl = []
g7 = {}
bud = re.findall(r'BUDGET (\w+): vertices (\d+) \(kit (\d+)\), triangles (\d+) \(kit (\d+)\); one swing frame = ([\d.]+) MB decompressed .*? base file ([\d.]+) MB; 12 morph targets resident = ([\d.]+) MB', lock)
sizes = sum(os.path.getsize(p) for p in glob.glob(REPO + '/GolfArcade/Unity/CharacterAssets/MatchHero_*'))
g7['per_hero'] = {b[0]: dict(vertices=int(b[1]), kit_vertices=int(b[2]), triangles=int(b[3]), kit_triangles=int(b[4]), swing_frame_mb=float(b[5]), base_file_mb=float(b[6]), resident_morph_mb=float(b[7])) for b in bud}
g7['matchhero_assets_bytes'] = sizes
g7['matchhero_assets_mb'] = round(sizes / 1024 / 1024, 1)
g7['matchhero_assets_mb_before'] = 22.0   # du -ch before this job (28 files)
g7['kit_fbx_bytes'] = {h: os.path.getsize(f'{W}/export/{h}_Kit.fbx') for h in ('Male', 'Female') if os.path.exists(f'{W}/export/{h}_Kit.fbx')}
for h, v in g7['per_hero'].items():
    if v['kit_triangles'] > 100000 or v['resident_morph_mb'] > 80:
        fl.append(f'7 BUDGET {h}: kit {v["kit_triangles"]} triangles / resident {v["resident_morph_mb"]} MB')
if g7['matchhero_assets_mb'] > 70:
    fl.append(f'7 BUDGET: MatchHero_* assets {g7["matchhero_assets_mb"]} MB > 70 MB')
bl = read(W + '/logs/xcode_build.log')
g7['xcodebuild_build'] = 'BUILD SUCCEEDED' if '** BUILD SUCCEEDED **' in bl else ('FAILED' if bl else 'not run')
if g7['xcodebuild_build'] != 'BUILD SUCCEEDED':
    fl.append('7 BUDGET: xcodebuild build of scheme GolfArcade did not succeed: ' + g7['xcodebuild_build'])
locker_tests = {k: v for k, v in g6['swift_tests'].items() if k.startswith('MatchHeroLockerTests.')}
g7['touched_tests'] = locker_tests
if not locker_tests or any(v != 'passed' for v in locker_tests.values()):
    fl.append('7 BUDGET: MatchHeroLockerTests (touched) not all passing: ' + json.dumps(locker_tests))
gate('7 BUDGET', not fl, g7, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 8
fl = []
g8 = {}
for h in HEROES:
    so = jl(f'{D}/sole_{h}.json')
    if not so:
        fl.append(f'8 RACKET_AND_FEET {h}: sole track missing')
        continue
    g8[h] = dict(bind_offset_mm=so['bind_offset_mm'], worst_planted_err_mm=so['worst_planted_err_mm'], p99_planted_err_mm=so['p99_planted_err_mm'], tolerance_mm=so['tolerance_mm'], ready0=so['ready0'], by_clip_planted_worst=so.get('by_clip_planted_worst'))
    if not so['pass_']:
        fl.append(f'8 RACKET_AND_FEET {h} SOLE_TRACK: worst planted-frame sole error {so["worst_planted_err_mm"]:.1f} mm > {so["tolerance_mm"]:.0f} mm (p99 {so["p99_planted_err_mm"]:.1f})')
g8['racket_and_hands_unchanged'] = bool(gp and gp['pass'])
if not g8['racket_and_hands_unchanged']:
    fl.append('8 RACKET_AND_FEET: racket / hand nodes or clip curves changed')
if unity:
    g8['unity_shoe_lowest_y_at_ready_mm'] = {s['sex']: s['shoeLowestYAtReadyMm'] for s in unity['sexes']}
    g8['unity_body_lowest_y_at_ready_mm'] = {s['sex']: s['bodyLowestYAtReadyMm'] for s in unity['sexes']}
gate('8 RACKET_AND_FEET', not fl, g8, fl)

# ------------------------------------------------------------------------------------------------------------------------------ 9
need = ['Sheet_Male_Dressed.png', 'Sheet_Female_Dressed.png', 'BEFORE_AFTER_Male.png', 'BEFORE_AFTER_Female.png', 'BEFORE_AFTER_all.png', 'WORST_POKE_Male.png', 'WORST_POKE_Female.png']
have = {n: os.path.exists(f'{W}/proof/{n}') and os.path.getsize(f'{W}/proof/{n}') > 0 for n in need}
unity_png = sorted(os.path.basename(p) for p in glob.glob(W + '/proof/unity/*.png'))
swift_png = sorted(os.path.basename(p) for p in glob.glob(W + '/proof/swift/*.png'))
docs = {n: os.path.exists(f'{W}/{n}') and os.path.getsize(f'{W}/{n}') > 0 for n in ('NOTE_DRESS_MATCH_HEROES.md', 'run_all.sh', 'README.md', 'GATE_RESULTS.md', 'checks.json') if n not in ('GATE_RESULTS.md', 'checks.json')}
fl = [f'9 PROOFS: {n} missing' for n, ok in have.items() if not ok] + [f'9 PROOFS: {n} missing' for n, ok in docs.items() if not ok]
if len(unity_png) < 20:
    fl.append(f'9 PROOFS: only {len(unity_png)} Unity play-mode frames')
if len(swift_png) < 12:
    fl.append(f'9 PROOFS: only {len(swift_png)} Swift mirror shots')
gate('9 PROOFS', not fl, dict(sheets=have, unity_frames=len(unity_png), swift_frames=len(swift_png), docs=docs), fl)

overall = all(g['pass_'] for g in gates.values())
json.dump(dict(overall='PASS' if overall else 'FAIL', gates=gates, failed_lines=lines), open(W + '/checks.json', 'w'), indent=1)
print('GATE: DRESS_MATCH_HEROES', 'PASS' if overall else 'FAIL')
for l in lines:
    print('  ' + l)
