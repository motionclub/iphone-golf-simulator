"""protected.py snapshot | verify : the files this job must not change (Serve, Walk, the three runs, the golf course, the shaders, the locker).

snapshot  hashes the protected set into data/protected_before.json ONCE (refuses to overwrite).
verify    hashes it again and lists every difference with its mtime; a difference is attributed to this job only when the file is on the job's own write list
          (data/my_writes.txt, one repo-relative path or glob per line, written by this job's scripts BEFORE they write).  Differences nobody on that list owns are
          reported as 'other session' (informational).  The gate line is PASS when no protected file is on the write list and no protected file was written inside one of
          this job's run windows (logs/runs.log).  Definitions are pre-registered in GATE_DEFS_preregistered.md and are not edited after a run."""
import fnmatch, glob, hashlib, json, os, subprocess, sys, time

R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = R + '/work/emotes'
PATTERNS = [
    'Unity/Assets/Characters/MatchHeroes/Male/Male_Serve.fbx*', 'Unity/Assets/Characters/MatchHeroes/Male/Male_Walk.fbx*',
    'Unity/Assets/Characters/MatchHeroes/Male/Male_RunForward.fbx*', 'Unity/Assets/Characters/MatchHeroes/Male/Male_RunLeft.fbx*', 'Unity/Assets/Characters/MatchHeroes/Male/Male_RunRight.fbx*',
    'Unity/Assets/Characters/MatchHeroes/Female/Female_Serve.fbx*', 'Unity/Assets/Characters/MatchHeroes/Female/Female_Walk.fbx*',
    'Unity/Assets/Characters/MatchHeroes/Female/Female_RunForward.fbx*', 'Unity/Assets/Characters/MatchHeroes/Female/Female_RunLeft.fbx*', 'Unity/Assets/Characters/MatchHeroes/Female/Female_RunRight.fbx*',
    'Unity/Assets/Scripts/Course/**', 'Unity/Assets/Resources/Course/**', 'Unity/Assets/Scripts/Shot/**', 'Unity/Assets/Scripts/Game/Golf*', 'Unity/Assets/Editor/Golf*',
    'Unity/Assets/**/*.shader', 'Unity/Assets/**/*.shader.meta', 'Unity/Assets/**/*.shadergraph', 'Unity/Assets/**/*.hlsl',
    'GolfArcade/Unity/Locker*.swift', 'GolfArcade/Unity/MatchHero*.swift', 'GolfArcade/Unity/CharacterModelPreview.swift', 'GolfArcade/Unity/CharacterAssets/**',
    'GolfArcadeTests/Locker*.swift', 'GolfArcadeTests/MatchHeroLocker*.swift', 'Unity/Assets/Editor/HeroLockerExport.cs*', 'Unity/Assets/Editor/MatchHeroLockerExport.cs*',
]


def files():
    out = set()
    for p in PATTERNS:
        for f in glob.glob(os.path.join(R, p), recursive=True):
            if os.path.isfile(f) and not f.endswith('.DS_Store'):
                out.add(os.path.relpath(f, R))
    return sorted(out)


def sha(p):
    h = hashlib.sha256()
    with open(os.path.join(R, p), 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def snap():
    return {p: dict(sha=sha(p), mtime=os.path.getmtime(os.path.join(R, p))) for p in files()}


def my_writes():
    f = W + '/data/my_writes.txt'
    return [l.strip() for l in open(f)] if os.path.exists(f) else []


def runs():
    f = W + '/logs/runs.log'
    out = []
    if os.path.exists(f):
        for l in open(f):
            a = l.split('|')
            if len(a) >= 3:
                try:
                    out.append((time.mktime(time.strptime(a[0].strip(), '%Y-%m-%d %H:%M:%S')), time.mktime(time.strptime(a[1].strip(), '%Y-%m-%d %H:%M:%S'))))
                except Exception:
                    pass
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    B = W + '/data/protected_before.json'
    if cmd == 'snapshot':
        if os.path.exists(B):
            print('baseline exists, refusing to retake'); sys.exit(1)
        s = snap(); json.dump(dict(taken=time.strftime('%Y-%m-%d %H:%M:%S'), n=len(s), files=s), open(B, 'w'), indent=1)
        print('snapshot', len(s), 'files')
    elif cmd == 'verify':
        b = json.load(open(B))['files']; a = snap()
        mine = my_writes(); win = runs()
        diff = []
        for p in sorted(set(a) | set(b)):
            if p not in a: diff.append((p, 'deleted'))
            elif p not in b: diff.append((p, 'added'))
            elif a[p]['sha'] != b[p]['sha']: diff.append((p, 'changed'))
        owned = [d for d in diff if any(fnmatch.fnmatch(d[0], m) for m in mine)]
        in_win = [d for d in diff if d[1] != 'deleted' and any(s <= a.get(d[0], {}).get('mtime', 0) <= e + 1 for s, e in win)]
        out = dict(checked=len(b), differences=[dict(path=p, kind=k, mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(a[p]['mtime'])) if p in a else None) for p, k in diff],
                   on_my_write_list=[d[0] for d in owned], inside_my_run_windows=[d[0] for d in in_win])
        json.dump(out, open(W + '/data/protected_verify.json', 'w'), indent=1)
        print(json.dumps(out, indent=1))
        print('GATE: UNTOUCHED', 'PASS' if not owned and not in_win else 'FAIL')
