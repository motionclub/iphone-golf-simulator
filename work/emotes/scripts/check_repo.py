"""GATE EMOTES, repo / in-game / project lines (N1 N2 G1 G2 G3 X1 X2) + the supplementary measurements.  System python3.

  python3 check_repo.py <frames_male_dir> <frames_female_dir>   -> data/checks_repo.json"""
import csv, glob, hashlib, json, os, re, subprocess, sys

R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = R + '/work/emotes'
NAMES = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike', 'Intro_Wave', 'Intro_BringIt', 'Intro_Pushups']
EMOTE_CLIPS = {f'{s}_{n}' for s in ('Male', 'Female') for n in NAMES}
LEN = dict(Emote_Scuba=2.0, Emote_Thrust=2.0, Emote_Spike=2.0, Intro_Wave=2.0, Intro_BringIt=3.0, Intro_Pushups=3.0)
fr_dirs = dict(Male=sys.argv[1], Female=sys.argv[2])


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def ln(ok, **kw):
    return dict(ok=bool(ok), **kw)


out = {}
# ---------------------------------------------------------------- N1 / N2
n1 = {}
report = open(W + '/logs/wire_report.txt').read()
for s in ('Male', 'Female'):
    for n in NAMES:
        f = f'{W}/export/fbx/{s}_{n}.fbx'
        u = f'{R}/Unity/Assets/Characters/MatchHeroes/{s}/{s}_{n}.fbx'
        ok = os.path.exists(f) and os.path.exists(u) and sha(f) == sha(u) and os.path.exists(u + '.meta') and f'<- {s}_{n} ' in report
        n1[f'{s}_{n}'] = ln(ok, work=os.path.exists(f), unity_copy_identical=os.path.exists(u) and sha(f) == sha(u), imported_clip_named=f'<- {s}_{n} ' in report)
out['N1'] = ln(all(v['ok'] for v in n1.values()), files=12, detail=n1)
before = set(open(W + '/data/unity_files_before.txt').read().split())
now = set(subprocess.run(['find', 'Unity/Assets', '-type', 'f', '(', '-name', '*.fbx', '-o', '-name', '*.anim', '-o', '-name', '*.controller', '-o', '-name', '*.overrideController', '-o', '-name', '*.playable', ')'], cwd=R, capture_output=True, text=True).stdout.split())
added, removed = sorted(now - before), sorted(before - now)
want = sorted(f'Unity/Assets/Characters/MatchHeroes/{s}/{s}_{n}.fbx' for s in ('Male', 'Female') for n in NAMES)
out['N2'] = ln(added == want and not removed, added=len(added), removed=removed, unexpected=[a for a in added if a not in want])

# ---------------------------------------------------------------- G1 / G2 from the film traces
def trace(sex, name):
    rows = list(csv.DictReader(open(f'{fr_dirs[sex]}/{name}/trace.csv')))
    return rows


def runs(mask):
    out_, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out_.append((i, j)); i = j + 1
        else:
            i += 1
    return out_


g1, g2 = {}, {}
for sex in ('Male', 'Female'):
    for n in NAMES:
        rows = trace(sex, n)
        clip = f'{sex}_{n}'
        act = [i for i, r in enumerate(rows) if r['emoteActive'] == 'True']
        first = act[0] if act else 0
        expect = int(LEN[n] * 60)
        seg = rows[first:first + expect]
        frac = sum(1 for r in seg if r['playing'] == clip) / max(1, len(seg))
        others = sorted({r['playing'] for r in rows if r['playing'] in EMOTE_CLIPS and r['playing'] != clip})
        tail = rows[-1]
        mp4 = f'{W}/film/{n}_{sex.lower()}.mp4'
        n_frames = len(glob.glob(f'{fr_dirs[sex]}/{n}/game_*.png'))
        ok = frac >= 0.9 and not others and tail['playing'] == f'{sex}_ReadyIdle' and os.path.exists(mp4) and os.path.getsize(mp4) > 100000 and n_frames / 30.0 >= LEN[n]
        g1[clip] = ln(ok, played_fraction=frac, other_emote_clips=others, back_to_ready=tail['playing'] == f'{sex}_ReadyIdle', film=os.path.relpath(mp4, R), film_seconds=n_frames / 30.0, clip_seconds=LEN[n])
        # racket
        dist = [float(r['gripHandDist']) for r in rows]
        low = [float(r['racketLowY']) for r in rows]
        grip = [[float(x) for x in r['grip'].split(';')] for r in rows]
        gripw = [[float(x) for x in r['gripW'].split(';')] for r in rows]
        a0, a1 = first, min(len(rows) - 1, first + expect)
        if n not in ('Emote_Spike', 'Intro_Pushups'):
            mx = max(dist[a0:a1 + 1])
            g2[clip] = ln(mx <= 0.001, max_grip_hand_distance_m=mx)
        else:
            iv = runs([d > 0.02 for d in dist[a0:a1 + 1]])
            res = dict(intervals=len(iv))
            if len(iv) == 1:
                a, b = iv[0]
                dur = (b - a + 1) / 60.0
                after = max(dist[a0 + b + 1:a1 + 1] or [0.0])
                res.update(off_seconds=dur, max_dist_after_return_m=after)
                if n == 'Emote_Spike':
                    cont = runs([x <= 0.01 for x in low[a0:a1 + 1]])
                    org = [g[1] for g in grip[a0:a1 + 1]]
                    cf = cont[0][1] if cont else 0
                    rise = (max(org[cf:b + 1]) - min(org[cont[0][0]:cont[0][1] + 1])) if cont else 0
                    ok2 = 0.6 <= dur <= 1.4 and after <= 0.001 and len(cont) == 1 and rise >= 0.25
                    res.update(floor_contact_events=len(cont), origin_rise_m=rise)
                else:
                    seg2 = list(range(a, b + 1))
                    rest = runs([low[a0 + i] <= 0.03 for i in seg2])
                    rest = max(rest, key=lambda x: x[1] - x[0]) if rest else (0, 0)
                    ra, rb = a + rest[0], a + rest[1]
                    pts = gripw[a0 + ra:a0 + rb + 1]
                    mv = max(max(abs(p[k] - sum(q[k] for q in pts) / len(pts)) for k in range(3)) for p in pts) if pts else 9
                    ok2 = dur >= 1.2 and after <= 0.001 and (rb - ra + 1) / 60.0 >= 1.0 and mv <= 0.02
                    res.update(rest_seconds=(rb - ra + 1) / 60.0, rest_move_m=mv)
                g2[clip] = ln(ok2, **res)
            else:
                g2[clip] = ln(False, **res)
out['G1'] = ln(all(v['ok'] for v in g1.values()), detail=g1)
out['G2'] = ln(all(v['ok'] for v in g2.values()), detail=g2)

# ---------------------------------------------------------------- G3 triggers
g3 = {}
for sex in ('Male', 'Female'):
    t = json.load(open(f'{fr_dirs[sex]}/../ff_trig_{sex.lower()}/triggers.json')) if os.path.exists(f'{fr_dirs[sex]}/../ff_trig_{sex.lower()}/triggers.json') else json.load(open(f'{fr_dirs[sex]}/triggers.json'))
    ok = (t['plain_point_emotes'] == 0 and t['won_game_emotes'] == 1 and t['won_game_clip'] in ('EmoteScuba', 'EmoteThrust', 'EmoteSpike') and t['point_after_game_emotes'] == 0
          and t['play_taunt_spike']['ok'] and t['play_taunt_spike']['clip'] == 'EmoteSpike' and t['play_taunt_spike']['count'] == 1
          and t['intro_hook']['count'] == 1 and t['intro_hook']['clip'] in ('IntroWave', 'IntroBringIt', 'IntroPushups'))
    g3[sex] = ln(ok, **t)
out['G3'] = ln(all(v['ok'] for v in g3.values()), detail=g3)

# ---------------------------------------------------------------- X1 footage
media_ext = ('.mp4', '.mov', '.m4v', '.webm', '.mkv', '.avi', '.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
find = subprocess.run('find . -path ./.git -prune -o -path "*/DerivedData" -prune -o -path ./work/emotes/export -prune -o -type f -print', shell=True, cwd=R, capture_output=True, text=True).stdout.split('\n')
now_media = sorted(p for p in find if p.lower().endswith(media_ext))
before_media = set(open(W + '/data/media_before.txt').read().split('\n'))
new_media = [p for p in now_media if p not in before_media]
outside = [p for p in new_media if not p.startswith('./work/emotes/film/')]
bad_words = re.compile(r'https?://|yt-dlp|youtube-dl|wget|curl|pytube', re.I)
hits = []
for p in glob.glob(W + '/scripts/*') + glob.glob(R + '/Unity/Assets/Editor/Emote*.cs'):
    if os.path.isfile(p) and not p.endswith('enc') and not p.endswith('check_repo.py'):
        try:
            for i, l in enumerate(open(p, errors='ignore')):
                if bad_words.search(l):
                    hits.append(f'{os.path.relpath(p, R)}:{i + 1}')
        except Exception:
            pass
watch = open(W + '/WATCH_EMOTES.md').read()
out['X1'] = ln(not outside and not hits and not re.search(r'https?://', watch), new_media_files=len(new_media), new_media_outside_film=outside, script_hits=hits)

# ---------------------------------------------------------------- X2
pv = json.load(open(W + '/data/protected_verify.json')) if os.path.exists(W + '/data/protected_verify.json') else None
out['X2'] = ln(pv is not None and not pv['on_my_write_list'] and not pv['inside_my_run_windows'], differences_by_other_sessions=[d['path'] for d in (pv or {}).get('differences', [])], on_my_write_list=(pv or {}).get('on_my_write_list'), inside_my_run_windows=(pv or {}).get('inside_my_run_windows'))
json.dump(out, open(W + '/data/checks_repo.json', 'w'), indent=1)
for k in ('N1', 'N2', 'G1', 'G2', 'G3', 'X1', 'X2'):
    print('PASS' if out[k]['ok'] else 'FAIL', k, {kk: vv for kk, vv in out[k].items() if kk not in ('ok', 'detail')})
    if k in ('G1', 'G2', 'G3', 'N1') and not out[k]['ok']:
        for c, v in out[k]['detail'].items():
            if not v['ok']:
                print('    ', c, v)
