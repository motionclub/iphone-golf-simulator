#!/usr/bin/env python3
"""Integration 10-18 (chat 12): put the combined result into the real project, with ONE rollback.

    python3 -I install_real.py plan       # what would be copied / removed, and every conflict
    python3 -I install_real.py install    # copy, backing up every file it replaces (and listing every file it adds)
    python3 -I install_real.py rollback   # put back exactly what install changed

Three-way, per file, so nothing another chat changed since the integration snapshot is overwritten:
  base   = the snapshot the integration started from (~/integration-UnityClone2 for Unity/, ~/integration-work/native_base for the lobby)
  ours   = the combined result (~/integration-UnityClone, ~/integration-work/stage)
  theirs = the repo as it is now
A file changed base->ours is copied only if theirs is still base (or already equals ours); otherwise it is a CONFLICT and is left alone.
Unity Library/Temp/Logs/UserSettings and test-only tooling are skipped. Stages and commits nothing.
"""
import filecmp, json, os, shutil, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HOME = os.path.expanduser('~')
STATE = os.path.join(REPO, 'work/integration-1018/install_real')
# (label, base, ours, theirs, subdirs)
TREES = [
    ('unity', f'{HOME}/integration-work/Unity2', f'{HOME}/integration-work/Unity3', f'{REPO}/Unity', ['Assets', 'Packages', 'ProjectSettings']),
    ('lobby-assets', f'{HOME}/integration-work/native_base/CharacterAssets', f'{HOME}/integration-work/stage/GolfArcade/Unity/CharacterAssets', f'{REPO}/GolfArcade/Unity/CharacterAssets', ['.']),
    ('lobby-golden', f'{HOME}/integration-work/native_base/VisualGolden', f'{HOME}/integration-work/stage/GolfArcadeTests/VisualGolden', f'{REPO}/GolfArcadeTests/VisualGolden', ['.']),
]
SINGLE = [('look-sources', f'{HOME}/integration-work/native_base/look_sources.txt', f'{HOME}/integration-work/stage/work/hero-sync/look_sources.txt', f'{REPO}/work/hero-sync/look_sources.txt')]
# proof tooling copied into the clone for the tests only (not part of the game)
SKIP = ('Assets/Tests/PlayMode/IntegrationSmokeFilm.cs', 'Assets/Editor/MajesticWeatherShots.cs', 'Assets/Editor/MajesticHoleViews.cs',
        'Assets/Editor/MajesticGolfBudget.cs', 'Assets/Editor/MajesticKitShots.cs', 'Assets/Editor/FR60BLocal', 'Assets/Editor/GarmentPipeline/',
        'Assets/Editor/ChatTwelve',
        # a clone outside the repo has no ../../blender/tennis-clips.json, so GolferModelImporter writes these with no clips: never copy them
        'Assets/Resources/StandardCharacters/',
        # leftovers of interrupted test runs, and the folder metas of the test-only tooling above
        'Assets/InitTestScene', 'Assets/Editor/GarmentPipeline.meta', 'Assets/Editor/ChatTwelve.meta', 'Assets/Editor/FR60BLocal.meta')
SKIP_DIRS = ('Library', 'Temp', 'Logs', 'UserSettings', 'obj', '.vs')


def files(root, sub):
    out = set(); top = os.path.join(root, sub)
    if not os.path.isdir(top): return out
    for d, dirs, fs in os.walk(top):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in fs:
            if f == '.DS_Store': continue
            out.add(os.path.normpath(os.path.relpath(os.path.join(d, f), root)))
    return out


def same(a, b):
    if not os.path.exists(a) or not os.path.exists(b): return os.path.exists(a) == os.path.exists(b)
    return filecmp.cmp(a, b, shallow=False)


def plan():
    acts = []   # (kind, label, rel, ours_path, theirs_path)
    conflicts = []
    def consider(label, base, ours, theirs, rel):
        if any(rel.startswith(s) or rel == s for s in SKIP): return
        b, o, t = os.path.join(base, rel), os.path.join(ours, rel), os.path.join(theirs, rel)
        if same(b, o): return                      # we did not change it
        if same(o, t): return                      # already there
        if not same(b, t): conflicts.append((label, rel)); return
        acts.append(('remove' if not os.path.exists(o) else 'add' if not os.path.exists(t) else 'replace', label, rel, o, t))
    for label, base, ours, theirs, subs in TREES:
        for sub in subs:
            for rel in sorted(files(base, sub) | files(ours, sub)): consider(label, base, ours, theirs, rel)
    for label, b, o, t in SINGLE:
        if not same(b, o) and not same(o, t):
            if same(b, t): acts.append(('replace', label, os.path.basename(t), o, t))
            else: conflicts.append((label, t))
    return acts, conflicts


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    if mode == 'rollback':
        runs = [l.strip() for l in open(os.path.join(STATE, 'installs.txt')) if l.strip()]
        which = sys.argv[2] if len(sys.argv) > 2 else 'all'   # rollback [all|last]: every install, newest first, or only the last
        log = []
        for bk in (runs[-1:] if which == 'last' else runs): log += json.load(open(os.path.join(bk, 'installed.json')))
        for e in reversed(log):
            if e['backup']: shutil.copy2(e['backup'], e['theirs'])
            elif e['kind'] == 'add' and os.path.exists(e['theirs']): os.remove(e['theirs'])
        open(os.path.join(STATE, 'installs.txt'), 'w').write(''.join(r + '\n' for r in (runs[:-1] if which == 'last' else [])))
        print(f'rolled back {len(log)} files'); return
    acts, conflicts = plan()
    only = [x for x in os.environ.get('ONLY', '').split(',') if x]   # ONLY=lobby-assets,lobby-golden,look-sources: one part at a time
    if only: acts = [a for a in acts if a[1] in only]; conflicts = [c for c in conflicts if c[0] in only]
    by = {}
    for a in acts: by[(a[1], a[0])] = by.get((a[1], a[0]), 0) + 1
    for k, v in sorted(by.items()): print(f'{k[0]:13s} {k[1]:8s} {v}')
    for c in conflicts: print('CONFLICT (changed in the repo since the snapshot, left alone):', c[0], c[1])
    if mode == 'plan':
        for a in acts: print(a[0], a[1], a[2])
        return
    if mode != 'install': sys.exit('usage: plan|install|rollback')
    stamp = time.strftime('%Y%m%d_%H%M%S'); bk = os.path.join(STATE, 'backup_' + stamp); os.makedirs(bk, exist_ok=True)
    log = []
    for kind, label, rel, o, t in acts:
        backup = None
        if os.path.exists(t):
            backup = os.path.join(bk, label, rel); os.makedirs(os.path.dirname(backup), exist_ok=True); shutil.copy2(t, backup)
        if kind == 'remove': os.remove(t)
        else: os.makedirs(os.path.dirname(t), exist_ok=True); shutil.copy2(o, t)
        log.append({'kind': kind, 'label': label, 'rel': rel, 'theirs': t, 'backup': backup})
    json.dump(log, open(os.path.join(bk, 'installed.json'), 'w'), indent=1)
    open(os.path.join(STATE, 'installs.txt'), 'a').write(bk + '\n')
    json.dump({'stamp': stamp, 'conflicts': conflicts}, open(os.path.join(STATE, 'install_meta.json'), 'w'), indent=1)
    print(f'installed {len(log)} files; backup {bk}; rollback: python3 -I {os.path.abspath(__file__)} rollback')


if __name__ == '__main__':
    os.makedirs(STATE, exist_ok=True); main()
