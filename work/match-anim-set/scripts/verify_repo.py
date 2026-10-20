"""NO_FOOTAGE_IN_REPO + source / ArtDir integrity (read-only, system python):  python3 verify_repo.py
Compares the repo with the baselines taken before the build (data/artdir_before.json, git_status_before.txt, media_before_*.txt) and writes data/verify_repo.json."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/match-anim-set'
DATA = WORK + '/data'
ART = REPO + '/ArtDir'
MEDIA_EXT = ('.mp4', '.mov', '.webm', '.mkv', '.m4a', '.part', '.m4v', '.avi')
SRC = {
    'male': (REPO + '/work/male-pelvis-form3/export/merged_fd04bc28.blend', 'd6c4dcfb1150853a8802a8dc7501aa64066adb8b2734c14a4d6ed8e82dada781'),
    'female': (REPO + '/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend', 'a1d73a334f4dc18052db0582df6b4b54b1df166d9a3531ab700ee114e86d2ac1'),
}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for ch in iter(lambda: f.read(1 << 20), b''):
            h.update(ch)
    return h.hexdigest()


res = dict(taken=time.strftime('%Y-%m-%d %H:%M:%S'))
fails = []

# ---- source SHAs
res['source_sha'] = {k: dict(path=p, sha256=sha(p), expected=e, equal=sha(p) == e) for k, (p, e) in SRC.items()}
for k, v in res['source_sha'].items():
    if not v['equal']:
        fails.append(f'source {k} blend SHA changed')

# ---- ArtDir manifest
man = {}
for root, dirs, files in os.walk(ART):
    for f in files:
        p = os.path.join(root, f)
        try:
            st = os.stat(p)
        except OSError:
            continue
        man[os.path.relpath(p, ART)] = [st.st_size, st.st_mtime_ns]
before = json.load(open(DATA + '/artdir_before.json'))
bm = before['manifest']
added = sorted(set(man) - set(bm))
removed = sorted(set(bm) - set(man))
changed = sorted(k for k in set(man) & set(bm) if list(man[k]) != list(bm[k]))
key_after = {}
for rel in sorted(man):
    if rel.startswith('hero/base_lock/') and man[rel][0] < 400 * 1024 * 1024:
        key_after[rel] = sha(os.path.join(ART, rel))
key_changed = sorted(k for k in set(key_after) | set(before['key_sha256']) if key_after.get(k) != before['key_sha256'].get(k))
res['artdir'] = dict(files_before=len(bm), files_after=len(man), added=added[:50], n_added=len(added), removed=removed[:50], n_removed=len(removed),
                     changed=changed[:50], n_changed=len(changed), base_lock_hash_changes=key_changed)
if added or removed or changed or key_changed:
    fails.append(f'ArtDir differs from the baseline: +{len(added)} -{len(removed)} ~{len(changed)} (base_lock hash changes: {len(key_changed)}) - see data/verify_repo.json; '
                 'none of the match-anim-set scripts opens an ArtDir path (checked below)')

# ---- do my scripts touch ArtDir at all?
touch = []
for fn in sorted(os.listdir(WORK + '/scripts')) + ['dev/' + f for f in sorted(os.listdir(WORK + '/scripts/dev'))]:
    p = WORK + '/scripts/' + fn
    if not os.path.isfile(p) or not fn.endswith(('.py', '.sh')):
        continue
    txt = open(p, errors='ignore').read()
    if 'ArtDir' in txt and fn != 'verify_repo.py':
        touch.append(fn)
res['scripts_mentioning_ArtDir'] = touch
if touch:
    fails.append('scripts mention ArtDir: ' + ', '.join(touch))

# ---- git status vs the baseline
cur = subprocess.run(['git', 'status', '--porcelain'], cwd=REPO, capture_output=True, text=True).stdout.splitlines()
base = [l for l in open(DATA + '/git_status_before.txt').read().splitlines() if l.strip()]


def path_of(l):
    return l[3:].strip().strip('"')
cur_set, base_set = {path_of(l) for l in cur}, {path_of(l) for l in base}
new_paths = sorted(cur_set - base_set)
gone = sorted(base_set - cur_set)
outside = [p for p in new_paths if not p.startswith('work/match-anim-set/')]
res['git'] = dict(baseline_entries=len(base_set), now_entries=len(cur_set), new=new_paths[:60], n_new=len(new_paths), disappeared=gone[:40], n_disappeared=len(gone), new_outside_match_anim_set=outside)
if outside:
    fails.append(f'git status has {len(outside)} new entries outside work/match-anim-set/: {outside[:6]}')

# ---- media files
found = []
for root, dirs, files in os.walk(REPO):
    if '.git' in root.split(os.sep) or '/Library/' in root:
        continue
    for f in files:
        if f.lower().endswith(MEDIA_EXT):
            found.append('./' + os.path.relpath(os.path.join(root, f), REPO))
base_media = set(l.strip() for l in open(DATA + '/media_before_outside_work.txt') if l.strip()) | set(
    './' + l.strip() for l in open(DATA + '/media_before_work.txt') if l.strip())
new_media = sorted(set(found) - base_media)
allowed = {'./work/match-anim-set/proof/Review_Male.mp4', './work/match-anim-set/proof/Review_Female.mp4'}
res['media'] = dict(baseline=len(base_media), now=len(found), new=new_media, allowed=sorted(allowed))
for p in new_media:
    if p not in allowed:
        fails.append(f'new media file {p}')

# ---- scripts: no network calls / YouTube URLs
bad = []
pat = re.compile(r'(https?://|youtube|youtu\.be|urllib|import requests|from requests|import socket|from socket|yt_dlp|yt-dlp|\bcurl\b|\bwget\b)', re.I)
for fn in sorted(os.listdir(WORK + '/scripts')) + ['dev/' + f for f in sorted(os.listdir(WORK + '/scripts/dev'))]:
    p = WORK + '/scripts/' + fn
    if not os.path.isfile(p) or not fn.endswith(('.py', '.sh')) or fn == 'verify_repo.py':
        continue
    for i, line in enumerate(open(p, errors='ignore'), 1):
        if pat.search(line):
            bad.append(f'{fn}:{i}: {line.strip()[:90]}')
res['network_or_youtube_references_in_scripts'] = bad
if bad:
    fails.append('script lines with network / YouTube references: ' + '; '.join(bad[:5]))

# ---- loose media inside work/match-anim-set other than the two reviews
loose = [os.path.relpath(os.path.join(r, f), WORK) for r, d, fs in os.walk(WORK) for f in fs if f.lower().endswith(MEDIA_EXT)]
res['media_inside_match_anim_set'] = loose
res['failed'] = fails
json.dump(res, open(DATA + '/verify_repo.json', 'w'), indent=1)
print('VERIFY_REPO_DONE', 'FAIL' if fails else 'PASS')
for f in fails:
    print('  FAIL', f)
