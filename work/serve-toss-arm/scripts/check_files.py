"""check_files.py : gate 7 (ONLY_TWO_FILES_CHANGED) against data/before_hashes.txt, run from the repo root."""
import hashlib, os, subprocess, sys
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
os.chdir(R)
before = {}
for ln in open('work/serve-toss-arm/data/before_hashes.txt'):
    h, p = ln.rstrip('\n').split('  ', 1); before[p] = h
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
changed, missing = [], []
for p, h in before.items():
    if not os.path.exists(p): missing.append(p)
    elif sha(p) != h: changed.append(p)
cur_fbx = set(subprocess.check_output(['bash', '-c', 'ls Unity/Assets/Characters/MatchHeroes/*/*.fbx Unity/Assets/Characters/MatchHeroes/*/*.meta']).decode().split())
new = sorted(p for p in cur_fbx if p not in before)
allowed = {'Unity/Assets/Characters/MatchHeroes/Male/Male_Serve.fbx', 'Unity/Assets/Characters/MatchHeroes/Female/Female_Serve.fbx', 'work/serve-and-feet/export/fbx/Male_Serve.fbx', 'work/serve-and-feet/export/fbx/Female_Serve.fbx'}
bad = [p for p in changed if p not in allowed]
print('changed files:', changed); print('missing:', missing); print('new files in the character folder:', new)
print('GATE 7', 'PASS' if not bad and not missing and not new and set(changed) == allowed else 'FAIL', '| unexpected:', bad)
