"""Gate 2 BODY_UNCHANGED (files) and the ArtDir judgement.  python3 scripts/verify_repo.py [--write-after-fingerprint]
 (a) sha256 of the 32 clip FBXs in work/match-anim-set/export/fbx and of their 32 copies under Unity/Assets/Characters/MatchHeroes/<Sex>/ equal baseline/clip_fbx_sha256_before.txt
 (d) sha256 of the staged blends equals baseline/source_blends_sha256.txt
 (e) git status of ArtDir before vs after is listed; the gate fails only if one of THIS job's scripts mentions ArtDir (other sessions add files there)
Writes data/verify_repo.json."""
import hashlib
import json
import os
import re
import subprocess

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = REPO + '/work/hero-dressed'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


res = {}
base = {l.split()[1].split('/')[-1]: l.split()[0] for l in open(W + '/baseline/clip_fbx_sha256_before.txt') if l.strip()}
now = {f: sha(f'{REPO}/work/match-anim-set/export/fbx/{f}') for f in base}
res['clip_fbx_work'] = dict(count=len(base), equal=all(now[f] == base[f] for f in base), differing=[f for f in base if now[f] != base[f]])
unity = {}
for sex in ('Male', 'Female'):
    for f in base:
        if f.startswith(sex + '_'):
            p = f'{REPO}/Unity/Assets/Characters/MatchHeroes/{sex}/{f}'
            unity[f] = sha(p) if os.path.exists(p) else None
res['clip_fbx_unity'] = dict(count=len(unity), equal=all(unity[f] == base[f] for f in base), differing=[f for f in base if unity[f] != base[f]])
src = {l.split()[1]: l.split()[0] for l in open(W + '/baseline/source_blends_sha256.txt') if l.strip()}
res['blends'] = {k: sha(f'{REPO}/{k}') == v for k, v in src.items()}
res['blends_equal'] = all(res['blends'].values())
before = set(l.strip() for l in open(W + '/baseline/git_status_before.txt') if 'ArtDir' in l)
after = set(l.strip() for l in subprocess.run(['git', 'status', '--short'], cwd=REPO, capture_output=True, text=True).stdout.splitlines() if 'ArtDir' in l)
res['artdir'] = dict(added=sorted(after - before), removed=sorted(before - after))
mentions = []
for root, _, files in os.walk(W + '/scripts'):
    for f in files:
        if f.endswith(('.py', '.sh')) and f != 'verify_repo.py':
            if re.search(r'ArtDir', open(os.path.join(root, f), errors='ignore').read()):
                mentions.append(f)
for f in ('MatchHeroKit.cs', 'MatchHeroKitTests.cs', 'MatchHeroKitProbe.cs', 'MatchHeroKitBaseline.cs'):
    if 'ArtDir' in open(f'{REPO}/Unity/Assets/Editor/{f}').read():
        mentions.append(f)
res['artdir']['my_scripts_mentioning_ArtDir'] = mentions
res['artdir']['pass'] = not mentions
res['pass'] = bool(res['clip_fbx_work']['equal'] and res['clip_fbx_unity']['equal'] and res['blends_equal'] and res['artdir']['pass'])
json.dump(res, open(W + '/data/verify_repo.json', 'w'), indent=1)
print(json.dumps(res, indent=1)[:1500])
print('VERIFY_REPO', 'PASS' if res['pass'] else 'FAIL')
