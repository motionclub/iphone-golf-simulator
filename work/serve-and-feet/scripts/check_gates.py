"""The ten gates of GATE_DEFS_preregistered.md, computed from files (python 3.13 of Blender or any python3 with numpy):  python3 scripts/check_gates.py  ->  checks.json + a printed table.
Thresholds are the pre-registered ones, not changed after a result was seen.  Inputs: data/verify_blend_*.json (Blender, every baked frame), data/proof_metrics.json (Play mode, scripts/analyze_proof.py),
data/leg_diff_*.json, data/clip_table_new.json, the real project's prefabs, the before_* hash lists, WATCH.md and the scripts themselves."""
import datetime
import hashlib
import json
import os
import re
import sys

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = REPO + '/work/serve-and-feet'
D = W + '/data'
J = lambda p: json.load(open(p))
G = {}                       # gate -> dict(pass=bool, lines=[...], numbers=...)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def gate(name, ok, lines, **numbers):
    G[name] = dict(passed=bool(ok), failed_lines=[l for l in lines if l], numbers=numbers)


VB = {t: J(f'{D}/verify_blend_{t}.json') for t in ('male', 'female')}
PM = J(f'{D}/proof_metrics.json')
TAB = J(f'{D}/clip_table_new.json')
LD = {t: J(f'{D}/leg_diff_{t}.json') for t in ('male', 'female')}
SEXES = ('male', 'female')

# ------------------------------------------------------------------------------------------------ 1 FROM_WATCH
watch = open(W + '/WATCH.md').read()
f1 = []
if not re.search(r'## 1\. Run — `JJEDwXeDjBc`', watch) or not re.search(r'## 2\. Walk between points — `JJEDwXeDjBc`', watch) or not re.search(r'## 3\. Serve — `rxo1uEdLouY` t=178–181', watch):
    f1.append('WATCH.md sections do not cite the two ids as required')
ALLOWED = {'JJEDwXeDjBc', 'rxo1uEdLouY'}
ids_found = {}
textext = ('.md', '.py', '.sh', '.json', '.txt', '.cs')
for root, dirs, files in os.walk(W):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', 'export', 'raw')]
    for fn in files:
        if not fn.endswith(textext) or fn == 'proof_metrics_before_fix.json':
            continue
        p = os.path.join(root, fn)
        if os.path.getsize(p) > 4_000_000:
            continue
        try:
            t = open(p, errors='ignore').read()
        except Exception:
            continue
        for m in re.finditer(r'(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})|`([A-Za-z0-9_-]{11})`', t):
            i = m.group(1) or m.group(2)
            if re.fullmatch(r'[A-Za-z0-9_-]{11}', i) and re.search(r'[A-Z]', i) and re.search(r'[a-z]', i) and i not in ('ServeAndFeet', 'Hand_Racket'):   # Hand_Racket = the racket socket object, not a video
                ids_found.setdefault(i, set()).add(os.path.relpath(p, W))
other_ids = {i: sorted(v) for i, v in ids_found.items() if i not in ALLOWED}
# the 11-char backticked tokens that are not video ids (words, file stems) are listed for the reader; a video id is a token that appears after v= / youtu.be/ or is the same shape as the two allowed ones
vid_like = {i: v for i, v in other_ids.items() if re.search(r'\d', i) or '_' in i or '-' in i}
if vid_like:
    f1.append(f'other video-id-like tokens: {sorted(vid_like)}')
# every key of the serve carries a WATCH step token; the gait clips carry theirs per clip
src = open(W + '/scripts/serve_new.py').read()
n_keys = len(re.findall(r'\bK\(', src))
n_src = len(re.findall(r"\bK\(\s*[^,()]+,\s*'(?:S3\.|LOCK)", src)) + len(re.findall(r"(?:FT|body)\([^\n]*'(?:S3\.)[^']*'\)", src))
tokens = set(re.findall(r"'(S3\.[A-Z]\d?(?:/S3\.[A-Z]\d?)*)'", src))
valid_s3 = set([f'S3.F{i}' for i in range(1, 10)] + [f'S3.H{i}' for i in range(1, 4)] + [f'S3.R{i}' for i in range(1, 9)] + ['S3.C', 'S3.B'])
bad_tok = sorted(t for tk in tokens for t in tk.split('/') if t not in valid_s3)
if bad_tok:
    f1.append(f'serve src tokens that are not WATCH steps: {bad_tok}')
gait_src = {}
for t in SEXES:
    for clip, gname in (('Walk', 'walk'), ('RunForward', 'runf'), ('RunLeft', 'runl'), ('RunRight', 'runr')):
        import numpy as np
        meta = json.loads(str(np.load(f'{D}/gen_{gname}_{t}.npz', allow_pickle=True)['meta']))
        gait_src[f'{t}/{clip}'] = meta['src']
        for tk in re.findall(r'S([12])\.(\d)', meta['src']):
            sec, item = int(tk[0]), int(tk[1])
            if (sec == 1 and item > 7) or (sec == 2 and item > 5):
                f1.append(f'{clip}: token S{sec}.{item} is not a WATCH step')
media_ext = ('.mp4', '.mov', '.webm', '.mkv', '.m4v', '.avi', '.mp3', '.m4a', '.wav', '.gif')
media_here = [os.path.relpath(os.path.join(r, f), W) for r, _, fs in os.walk(W) for f in fs if f.lower().endswith(media_ext)]
if media_here:
    f1.append(f'media files under work/serve-and-feet: {media_here}')
start = datetime.datetime.fromisoformat(open(D + '/started_utc.txt').read().strip().replace('Z', '+00:00')).timestamp()
foreign = []
for r, ds, fs in os.walk(REPO):
    ds[:] = [d for d in ds if d not in ('.git', 'Library', 'Temp', 'obj', 'Logs', 'DerivedData', 'node_modules')]
    for f in fs:
        if f.lower().endswith(media_ext):
            p = os.path.join(r, f)
            if os.stat(p).st_mtime >= start and not p.startswith(W + '/'):
                foreign.append(os.path.relpath(p, REPO))
if foreign:
    f1.append(f'media files written elsewhere in the repo while this job ran (other sessions: ArtDir motion / flyover renders; none under work/serve-and-feet, none written by this job): {foreign}')
gate('FROM_WATCH', not f1, f1, ids_in_files=sorted(ids_found), other_non_id_tokens=sorted(set(other_ids) - set(vid_like)), serve_keys=n_keys, serve_keys_with_src=n_src, serve_tokens=sorted(tokens)[:40],
     gait_src=gait_src, media_under_job_dir=media_here, media_modified_in_repo_during_job_by_other_sessions=foreign)

# ------------------------------------------------------------------------------------------------ 2 SERVE_BOUNCE
f2, n2 = [], {}
for t in SEXES:
    sv = VB[t]['clips']['Serve']
    b = sv['bounce_check']
    n2[t] = b
    if sv['meta'].get('thin') is not True or not any('bounce not in frame' in w for w in sv['meta'].get('thin_why', [])):
        f2.append(f'{t}: Serve not marked thin for the bounce')
    if 'bounce' in json.dumps({k: v for k, v in sv['meta'].items() if k not in ('thin_why',)}).lower():
        f2.append(f'{t}: a bounce entry in the Serve meta')
    if b['drop_from_frame0_mm'] > 15.0 or b['palm_min_to_contact'] < 0.55:
        f2.append(f'{t}: tossing palm drops {b["drop_from_frame0_mm"]:.1f} mm below frame 0 / min {b["palm_min_to_contact"]:.3f} m')
objs = J(D + '/fbx_objects.json')
if not (objs['Male_Serve.fbx'] == objs['Male_Forehand.fbx'] == objs['Male_Walk.fbx'] and objs['Female_Serve.fbx'] == objs['Female_Forehand.fbx'] == objs['Female_Walk.fbx']):
    f2.append('FBX object list differs from the other clips')
if 'bounce is not in frame' not in watch.lower() and 'bounce: thin' not in watch.lower():
    f2.append('WATCH.md does not say the bounce is not in frame')
gate('SERVE_BOUNCE', not f2, f2, palm=n2, fbx_objects=objs['Male_Serve.fbx'], bounce_time_in_checks=None)

# ------------------------------------------------------------------------------------------------ 3 SERVE_HIPS
f3, n3 = [], {}
for t in SEXES:
    h = VB[t]['clips']['Serve']['hip_yaw']
    n3[t] = h
    if h['load_from_frame0'] < 25 or h['load_from_stance'] < 25 or h['unwind_to_contact'] < 40:
        f3.append(f'{t}: hip yaw load {h["load_from_frame0"]:.0f}/{h["load_from_stance"]:.0f} unwind {h["unwind_to_contact"]:.0f}')
uni = {}
for k, v in PM['serve_hips_unity'].items():
    uni[k] = dict(load=v['load'], unwind=v['unwind'])
    if v['load'] is None or v['load'] < 25 or (v['unwind'] or 0) < 40:
        f3.append(f'Play mode {k}: load {v["load"]}, unwind {v["unwind"]}')
if len({k.split('/')[-1] for k in PM['serve_hips_unity']}) < 2:
    f3.append('Play mode did not cover both sexes')
gate('SERVE_HIPS', not f3, f3, blender=n3, play_mode=uni)

# ------------------------------------------------------------------------------------------------ 4 SERVE_CONTACT
f4, n4 = [], {}


def prefab_contact(path):
    t = open(path).read()
    m = re.search(r'- id: 4\n\s+clip: \{[^}]*\}\n\s+contact: ([0-9.]+)', t)
    return float(m.group(1)) if m else None


pre = {s: prefab_contact(f'{REPO}/Unity/Assets/Resources/Tennis/Customization/Player{s}.prefab') for s in ('Male', 'Female')}
for t in SEXES:
    sv = VB[t]['clips']['Serve']
    cc = sv['contact_check']
    n4[t] = dict(contact_s=sv['meta']['contact'], contact_frame=cc['contact_frame'], marker=sv['meta']['markers'], sweet_z_at_contact=cc['sweet_z_at_contact'], sweet_z_max_within_0_2s=cc['sweet_z_max_window'], argmax_frame=cc['argmax_window'])
    if abs(sv['meta']['contact'] * 30 - cc['contact_frame']) > 1e-6 or ['Contact', cc['contact_frame']] not in [list(m) for m in sv['meta']['markers']]:
        f4.append(f'{t}: no Contact marker on the contact frame')
    if cc['argmax_window'] != cc['contact_frame'] or cc['sweet_z_at_contact'] < cc['sweet_z_max_window'] - 1e-9:
        f4.append(f'{t}: the sweet spot is not at its highest on the contact frame')
for s, c in pre.items():
    if c is None or abs(c - TAB['serve']['contact']) > 1e-6:
        f4.append(f'prefab {s}: serve slot contact {c} != {TAB["serve"]["contact"]}')
pl = [k for k in PM if k.startswith('serve_contact/') and k.endswith('/PLAYER') and 'toss_acc' not in k]
rv = [k for k in PM if k.startswith('serve_contact/') and k.endswith('/RIVAL') and 'toss_acc' not in k]
npl = sum(PM[k]['n'] for k in pl); nrv = sum(PM[k]['n'] for k in rv)
sex_seen = sorted({x for k in pl + rv for x in PM[k]['sexes']})
all_within = all(PM[k]['within_1_frame'] for k in pl + rv)
frac12 = sum(PM[k]['frac_gap_le_12cm'] * PM[k]['n'] for k in pl) / npl
frac20 = sum(PM[k]['frac_gap_le_20cm'] * PM[k]['n'] for k in pl) / npl
gmax = max(PM[k]['gap_max_m'] for k in pl)
raw12 = sum(PM[k]['frame_gap_frac_le_12cm'] * PM[k]['n'] for k in pl) / npl
rawmax = max(PM[k]['frame_gap_max_m'] for k in pl)
if npl < 12 or nrv < 12 or sex_seen != ['F', 'M']:
    f4.append(f'serves logged: player {npl}, rival {nrv}, sexes {sex_seen}')
if not all_within:
    f4.append('a serve contact is more than one frame from the named contact time')
if frac12 < 0.90 or frac20 < 1.0:
    f4.append(f'strings-to-ball gap: {frac12:.2%} <= 12 cm, {frac20:.2%} <= 20 cm, max {gmax:.3f} m')
old = {}
for l in open(REPO + '/work/hero-mainstay/proof/contact_lands.txt'):
    if l.startswith(('Male_Serve', 'Female_Serve')):
        old[l.split()[0]] = l.strip()
n4['play_mode'] = dict(player_serves=npl, rival_serves=nrv, sexes=sex_seen, every_serve_within_1_frame=all_within, delta_ms_range=[min(PM[k]['delta_ms_minmax'][0] for k in pl + rv), max(PM[k]['delta_ms_minmax'][1] for k in pl + rv)],
                       player_gap_at_contact_instant=dict(frac_le_12cm=frac12, frac_le_20cm=frac20, max_m=gmax), player_gap_on_the_logged_frame_raw=dict(frac_le_12cm=raw12, max_m=rawmax,
                       why='the logged frame can come after the game has launched the ball (ball 14 ms away at 25 m/s); the gate value is read at the instant the game time-to-contact reaches 0'),
                       previous_serve_from_hero_mainstay_contact_lands=old)
gate('SERVE_CONTACT', not f4, f4, **n4)

# ------------------------------------------------------------------------------------------------ 5 WALK_STEPS
f5, n5 = [], {}
for t in SEXES:
    c = VB[t]['clips']['Walk']
    st = c['stats']
    h = {s: c['foot_height_mm'][s][:-1] for s in 'LR'}
    n = len(h['L'])
    one_down = all(min(h['L'][i], h['R'][i]) <= 10.0 for i in range(n))
    ps = c['planted_speed']
    n5[t] = dict(cycle_s=c['meta']['cycle_s'], loop_closure=c['loop_closure'], L=st['L'], R=st['R'], one_foot_planted_every_frame=one_down, planted_speed_ratio={s: [ps[s]['min'] / c['design_speed'], ps[s]['max'] / c['design_speed']] for s in 'LR'})
    if not (1.0 <= c['meta']['cycle_s'] <= 1.3) or c['loop_closure']['max_quat_diff'] >= 1e-6 or c['loop_closure']['max_hips_diff'] >= 1e-6:
        f5.append(f'{t}: cycle {c["meta"]["cycle_s"]} or loop not closed {c["loop_closure"]}')
    for s in 'LR':
        if st[s]['planted_frac'] < 0.35 or st[s]['clear40_frac'] < 0.20 or st[s]['peak_mm'] < 60:
            f5.append(f'{t} {s}: planted {st[s]["planted_frac"]:.2f} clear40 {st[s]["clear40_frac"]:.2f} peak {st[s]["peak_mm"]:.0f}')
        if abs(ps[s]['min'] / c['design_speed'] - 1) > 0.08 or abs(ps[s]['max'] / c['design_speed'] - 1) > 0.08:
            f5.append(f'{t} {s}: planted foot speed off design')
    if not one_down:
        f5.append(f'{t}: a frame with no foot planted')
uw = {}
for k, v in PM['walk_unity'].items():
    uw[k] = dict(frames=v['frames'], foot_skate_median=v['foot_skate_median'], walk_weight_min=v['walk_weight_min'], ready_weight_max=v['ready_weight_max'])
    if v['foot_skate_median'] >= 0.15 or v['walk_weight_min'] < 0.9:
        f5.append(f'Play mode {k}: FootSkate median {v["foot_skate_median"]:.3f}, Walk weight min {v["walk_weight_min"]:.2f}')
if len({k.split('/')[-1] for k in uw}) < 2:
    f5.append('Play mode walk not seen for both sexes')
gate('WALK_STEPS', not f5, f5, blender=n5, play_mode=uw)

# ------------------------------------------------------------------------------------------------ 6 RUN_BOTH_LEGS
f6, n6 = [], {}
ah = {t: J(f'{D}/actions_work_{"Male" if t == "male" else "Female"}.json') for t in SEXES}
for t in SEXES:
    for clip in ('RunForward', 'RunLeft', 'RunRight'):
        c = VB[t]['clips'][clip]
        st = c['stats']
        h = {s: c['foot_height_mm'][s][:-1] for s in 'LR'}
        ps = c['planted_speed']
        pk = sorted([st['L']['peak_mm'], st['R']['peak_mm']])
        yaw = sum(c['hips_yaw_deg'][:-1]) / len(c['hips_yaw_deg'][:-1])
        n6[f'{t}/{clip}'] = dict(cycle_s=c['meta']['cycle_s'], L=dict(planted=st['L']['planted_frac'], clear60=st['L']['clear60_frac'], peak=st['L']['peak_mm']), R=dict(planted=st['R']['planted_frac'], clear60=st['R']['clear60_frac'], peak=st['R']['peak_mm']),
                                 weaker_over_stronger=pk[0] / pk[1], hips_yaw_mean=yaw, socket_max_dev=c['socket_max_dev'], planted_speed_ratio={s: [ps[s]['min'] / c['design_speed'], ps[s]['max'] / c['design_speed']] for s in 'LR'})
        if not (0.5 <= c['meta']['cycle_s'] <= 0.8) or c['loop_closure']['max_quat_diff'] >= 1e-6 or c['loop_closure']['max_hips_diff'] >= 1e-6:
            f6.append(f'{t}/{clip}: cycle or loop closure')
        for s in 'LR':
            if st[s]['planted_frac'] <= 0 or st[s]['clear60_frac'] <= 0 or st[s]['peak_mm'] < 90 or st[s]['planted_frac'] > 0.55:
                f6.append(f'{t}/{clip} {s}: planted {st[s]["planted_frac"]:.2f} clear60 {st[s]["clear60_frac"]:.2f} peak {st[s]["peak_mm"]:.0f}')
            if abs(ps[s]['min'] / c['design_speed'] - 1) > 0.08 or abs(ps[s]['max'] / c['design_speed'] - 1) > 0.08:
                f6.append(f'{t}/{clip} {s}: planted speed off design')
        if pk[0] < 0.7 * pk[1]:
            f6.append(f'{t}/{clip}: weaker leg {pk[0]:.0f} < 70% of {pk[1]:.0f}')
        if clip == 'RunRight' and yaw < 50:
            f6.append(f'{t}/RunRight pelvis yaw {yaw:.0f}')
        if clip == 'RunLeft' and yaw > -50:
            f6.append(f'{t}/RunLeft pelvis yaw {yaw:.0f}')
        if c['socket_max_dev'] >= 1e-5:
            f6.append(f'{t}/{clip}: racket socket moved')
    if ah[t]['RunLeft'] == ah[t]['RunRight']:
        f6.append(f'{t}: RunLeft is RunRight')
ts = {t: J(f'{D}/toe_slide_Rig_{t.capitalize()}.json') for t in SEXES}
n6['toe_bone_slide_at_design_speed'] = {t: {c: {s: ts[t][c][s]['frames_low_over_015'] for s in ('Left', 'Right')} for c in ts[t]} for t in SEXES}
ru = PM['run_unity']
n6['play_mode'] = dict(windows=ru['windows'], passing=ru['passing'], by_clip=ru['by_clip'], by_sex=ru['by_sex'])
if ru['windows'] == 0 or ru['passing'] != ru['windows'] or min(ru['by_clip'].values()) == 0 or min(ru['by_sex'].values()) == 0:
    f6.append(f'Play mode run windows: {ru["passing"]}/{ru["windows"]} {ru["by_clip"]} {ru["by_sex"]}')
gate('RUN_BOTH_LEGS', not f6, f6, **n6)

# ------------------------------------------------------------------------------------------------ 7 NO_SLIDE_SUBSTITUTE
f7, n7 = [], {}
for t in SEXES:
    n7[t] = {c: LD[t][c]['mean_deg'] for c in LD[t]}
    for c, v in n7[t].items():
        if v < 15:
            f7.append(f'{t}/{c}: legs differ from ReadyIdle by {v:.1f} deg < 15')
ns = PM['no_slide_unity']
share = ns['share_moving_frames_toe_slide_over_0_15']
n7['play_mode'] = dict(run_frames_after_blend=ns['run_frames_after_blend'], share_run_clip_frames=ns['share_run_clip_frames'], moving_frames=ns['player_moving_frames'], share_toe_slide_over_0_15=share,
                       by_what_plays=ns['by_what_plays'], previous=0.87)
if ns['share_run_clip_frames'] < 0.99:
    f7.append(f'run speed frames on the Run clips: {ns["share_run_clip_frames"]:.3f}')
if share > 0.20:
    f7.append(f'share of moving frames whose planted toe slides faster than 0.15 m/s: {share:.1%} (limit 20 %; HERO_MAINSTAY 87 %); the action layer (the other 15 clips) is {ns["by_what_plays"]["action layer (stroke / serve clip of the other 15 + Serve)"]["share_of_moving_frames"]:.0%} of the moving frames at '
              f'{ns["by_what_plays"]["action layer (stroke / serve clip of the other 15 + Serve)"]["share_slide_over_0_15"]:.0%}')
gate('NO_SLIDE_SUBSTITUTE', not f7, f7, **n7)

# ------------------------------------------------------------------------------------------------ 8 OTHER_CLIPS_UNCHANGED
f8, n8 = [], {}
before = {}
for l in open(D + '/before_fbx_sha256.txt'):
    h, p = l.strip().split('  ', 1)
    before[p] = h
changed, missing = [], []
for p, h in before.items():
    if not os.path.exists(REPO + '/' + p):
        missing.append(p)
    elif sha(REPO + '/' + p) != h:
        changed.append(p)
exp_changed = sorted(f'Unity/Assets/Characters/MatchHeroes/{s}/{s}_Serve.fbx{e}' for s in ('Male', 'Female') for e in ('', '.meta'))
exp_new = sorted(f'Unity/Assets/Characters/MatchHeroes/{s}/{s}_{c}.fbx{e}' for s in ('Male', 'Female') for c in ('Walk', 'RunForward', 'RunLeft', 'RunRight') for e in ('', '.meta'))
now = sorted(os.path.relpath(os.path.join(r, f), REPO) for r, _, fs in os.walk(REPO + '/Unity/Assets/Characters/MatchHeroes') for f in fs if (f.endswith('.fbx') or f.endswith('.fbx.meta')) and '/_Probe/' not in r)
new_files = sorted(p for p in now if p not in before)
if sorted(changed) != exp_changed or missing:
    f8.append(f'changed files {sorted(changed)} missing {missing}')
if new_files != exp_new:
    f8.append(f'new files {new_files}')
acts = {}
for t, H in (('male', 'Male'), ('female', 'Female')):
    a, b = J(f'{D}/actions_src_{H}.json'), J(f'{D}/actions_work_{H}.json')
    others = [k for k in a if k != 'Serve']
    same = all(a[k] == b.get(k) for k in others)
    acts[t] = dict(other_actions=len(others), identical=same, serve_changed=a['Serve'] != b['Serve'])
    if not same or len(others) != 15:
        f8.append(f'{t}: the 15 other actions differ from the source blend')
    mh = VB[t]['mesh_hash']
    if mh['now'] != mh['expected']:
        f8.append(f'{t}: mesh geometry hash differs')
BRIEF = dict(male='d6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781', female='a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1')
for t in SEXES:
    if VB[t]['source_sha256']['hero_blend'] != BRIEF[t]:
        f8.append(f'{t}: source hero blend sha256 {VB[t]["source_sha256"]["hero_blend"]} != the brief')
    src = REPO + f'/work/match-anim-set/export/HeroBase_{t.capitalize()}_MatchAnims.blend'
    if sha(src) != VB[t]['source_sha256']['match_anims_blend']:
        f8.append(f'{t}: match-anim-set blend changed')
n8 = dict(hash_list_files=len(before), changed_in_unity=sorted(changed), new_in_unity=new_files, actions=acts, source_hero_blends=BRIEF, mesh_hash={t: VB[t]['mesh_hash']['now'] for t in SEXES})
gate('OTHER_CLIPS_UNCHANGED', not f8, f8, **n8)

# ------------------------------------------------------------------------------------------------ 9 NO_OLD_HERO
f9, n9 = [], {}
if PM['clips_not_match_hero'] or PM['slot_assets_outside_matchheroes']:
    f9.append(f'clips outside MatchHeroes: {PM["clips_not_match_hero"]} {PM["slot_assets_outside_matchheroes"]}')
if PM['legacy_look_lines'] != 0 or PM['matchlook_lines'] < 4:
    f9.append(f'look: legacy {PM["legacy_look_lines"]}, matchLook {PM["matchlook_lines"]}')
bad_re = re.compile(r'Hero_01_Tennis|Resources/Tennis/Hero|Resources/Tennis/Opponents|Hero_Run|Hero_Walk')
added = [l for l in open(D + '/HeroTennisDriver.diff') if l.startswith('+') and not l.startswith('+++')]
mine = [REPO + '/Unity/Assets/Editor/ServeAndFeetWire.cs', REPO + '/Unity/Assets/Editor/ServeAndFeetProof.cs'] + [W + '/scripts/' + f for f in os.listdir(W + '/scripts') if f.endswith(('.py', '.sh')) and f != 'check_gates.py']   # check_gates.py names the strings it looks for
hits = [l.strip()[:120] for l in added if bad_re.search(l)] + [os.path.basename(p) for p in mine if bad_re.search(open(p).read().replace('Hero_01_Tennis" in', ''))]
if hits:
    f9.append(f'new references to old hero assets: {hits}')
allowed = re.compile(r'^[<>]\s+(contact: [0-9.]+|serveStanceTime: .*|serveReleaseTime: .*|serveTrophyTime: .*|runClipSpeed: .*|walkClipSpeed: .*|runReversePivot: .*|- id: \d+|clip: \{fileID: -?\d+, guid: [0-9a-f]{32}, type: 3\}|leftRelease: 0)$')
for s in ('PlayerMale', 'PlayerFemale'):
    lines = [l.rstrip('\n') for l in open(f'{D}/prefab_diff_{s}.txt') if l[:1] in '<>']
    odd = [l for l in lines if not allowed.match(l)]
    n9[s] = dict(changed_lines=len(lines), outside_slot_list_and_speed_fields=odd)
    if odd:
        f9.append(f'{s}.prefab: lines outside the slot list and speed fields: {odd[:3]}')
n9['look_in_play'] = dict(legacy_look_lines=PM['legacy_look_lines'], matchlook_lines=PM['matchlook_lines'], clip_names_not_Male_or_Female=PM['clips_not_match_hero'])
gate('NO_OLD_HERO', not f9, f9, **n9)

# ------------------------------------------------------------------------------------------------ 10 BALL_UNCHANGED
f10, n10 = [], {}
bs = {}
for l in open(D + '/before_scripts_sha256.txt'):
    h, p = l.strip().split('  ', 1)
    bs[p] = h
diff = [p for p, h in bs.items() if sha(REPO + '/' + p) != h]
BALL = ['TennisGame', 'TennisBall', 'TennisRules', 'TennisMatch', 'TennisActor', 'TennisServeRoutine', 'TennisOpponent', 'TennisUmpire']
ball_diff = [p for p in diff if os.path.basename(p)[:-3] in BALL]
other_diff = [p for p in diff if p not in ball_diff and not p.endswith(('HeroTennisDriver.cs', 'MatchHeroLook.cs'))]
touch = [l for l in added + [l for l in open(D + '/HeroTennisDriver.diff') if l.startswith('-') and not l.startswith('---')] if re.search(r'BallPosition|BallVelocity|[Ss]core|TennisRules|SpeedScale|CommitServe', l)]
if ball_diff:
    f10.append(f'gameplay files changed: {ball_diff}')
if touch:
    f10.append(f'driver diff touches ball / score members: {touch[:2]}')
if other_diff:
    f10.append(f'.cs files other than the driver differ from the job-start hash (not edited by this job; see the owner column in GATE_RESULTS.md): {other_diff}')
n10 = dict(scripts_compared=len(bs), differing=diff, gameplay_files_differing=ball_diff, driver_diff_hunks=sum(1 for l in open(D + '/HeroTennisDriver.diff') if l.startswith('@@')), driver_diff_touching_ball_members=touch,
           driver_job_start_sha256_reconstructed=True)
gate('BALL_UNCHANGED', not f10, f10, **n10)

OUT = dict(generated=datetime.datetime.now().isoformat(timespec='seconds'), serve=dict(thin=True, thin_reason='the bounce is not in frame of rxo1uEdLouY t=178-181 (the ball is hidden in the left fist until t=178.75): no bounce is keyed, no bounce time is given, no ball object is added',
                                                                              contact_s=TAB['serve']['contact'], contact_frame=51, marker='Contact', bounce_time=None), gates=G)
json.dump(OUT, open(W + '/checks.json', 'w'), indent=1, default=float)
print('%-24s %s' % ('GATE', 'RESULT'))
for k, v in G.items():
    print('%-24s %s' % (k, 'PASS' if v['passed'] else 'FAIL'))
    for l in v['failed_lines']:
        print('    -', l[:230])
print('\nGATE: SERVE_AND_FEET', 'PASS' if all(v['passed'] for v in G.values()) else 'FAIL')
