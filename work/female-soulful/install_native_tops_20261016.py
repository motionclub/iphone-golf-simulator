"""Scoped native install of the 2026-10-16 female tops (explicit paths, before-hash guards).

Installs from native-combined/: the three female payloads (tennis, Distance, golf: manifest json,
mesh lzfse, rig lzfse, swing frames), the four top maps (png + ktx), and repacked visual goldens
with refreshed provenance. Material smoothness in each manifest is restored to the production values,
so native materials stay as they are (the material candidate belongs to the shader task). No male
payload, no other map. Backups + hashes in revisions/production-install-20261016/native/.

python3 -I install_native_tops_20261016.py [--dry-run]
"""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys
root = Path(__file__).resolve().parent; repo = root.parent.parent
src = root / 'native-combined'; dst = repo / 'GolfArcade/Unity/CharacterAssets'; gold = repo / 'GolfArcadeTests/VisualGolden'
backup = root / 'revisions/production-install-20261016/native'
dry = '--dry-run' in sys.argv
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
heroes = ['MatchHero_Female', 'MatchHero_Female_Distance', 'GolfKitHero_Female']
files = []
for h in heroes:
    files += [h + '.json', h + '.lzfse', h + '_Rig.lzfse']
    files += sorted(p.name for p in (src / 'assets').glob(h + '_Swing_*.lzfse'))
for sport in ['Tennis', 'Golf']:
    for kind in ['M', 'N']:
        for ext in ['png', 'ktx']: files.append(f'MatchHero_KitV2_{sport}_Female_Top_{kind}.{ext}')
for f in files:
    if not (src / 'assets' / f).exists(): raise SystemExit('missing staged ' + f)
    if not (dst / f).exists(): raise SystemExit('unexpected new production file ' + f)
for h in heroes:
    if not (src / 'golden' / (h + '_golden.json')).exists(): raise SystemExit('missing golden ' + h)
male_before = {p.name: sha(p) for p in dst.glob('*Male*') if 'Female' not in p.name}
before = {f: sha(dst / f) for f in files}
before.update({p.name: sha(p) for p in gold.glob('*Female*_golden.lzfse')}); before['provenance.json'] = sha(gold / 'provenance.json')
if dry:
    print('dry run:', len(files), 'payload/map files,', len(heroes), 'goldens'); raise SystemExit
backup.mkdir(parents=True, exist_ok=True)
(backup / 'before-hashes.json').write_text(json.dumps(before, indent=1))
for f in files: shutil.copy2(dst / f, backup / f)
for p in list(gold.glob('*Female*_golden.lzfse')) + [gold / 'provenance.json']: shutil.copy2(p, backup / p.name)

restored = {}
for f in files:
    target = dst / f
    if sha(target) != before[f]: raise SystemExit('GUARD: production changed during install ' + f)
    if f.endswith('.json'):
        new = json.loads((src / 'assets' / f).read_text()); old = json.loads((backup / f).read_text())
        oldm = {m.get('name'): m for m in old['materials']}
        for m in new['materials']:
            o = oldm.get(m.get('name'))
            if o is not None and 'smoothness' in o and m.get('smoothness') != o['smoothness']:
                restored.setdefault(f, []).append(m['name']); m['smoothness'] = o['smoothness']
        tmp = target.with_suffix('.json.installing'); tmp.write_text(json.dumps(new, indent=4)); tmp.replace(target)
    else:
        tmp = target.with_name(target.name + '.installing'); shutil.copy2(src / 'assets' / f, tmp); tmp.replace(target)
        if sha(target) != sha(src / 'assets' / f): raise SystemExit('VERIFY failed ' + f)

rows = json.loads((gold / 'provenance.json').read_text())
paths = [s.strip() for s in (repo / 'work/hero-sync/look_sources.txt').read_text().splitlines() if s.strip() and not s.startswith('#')]
look = {s: sha(repo / s) for s in paths}; heads = {s: v for s, v in look.items() if s.startswith('Unity/Assets/Resources/Tennis/OriginalSeamBlinkFinish/')}
for row in rows:
    name = row['name']; row['heroLookSourceFiles'] = look
    if name in heroes:
        p = src / 'golden' / (name + '_golden.json'); packed = gold / (name + '_golden.lzfse')
        subprocess.run([str(repo / 'work/hero-sync/out/PackGolden'), str(p), str(packed)], check=True)
        row.update(source=str(p.relative_to(repo)), unitySampleCount=len(json.loads(p.read_text())['samples']), unitySourceSha256=sha(p),
                   packedSha256=sha(packed), packedBytes=packed.stat().st_size, manifestSha256=sha(dst / (name + '.json')), frozenFaceSourceFiles=heads,
                   note='Female 2026-10-16: independent golf polo (panel-matched harmonic binding) and tennis tank (torso-skin follow binding), accepted arm/grip runtime; material smoothness kept at production values.')
    elif row.get('manifestSha256') and row['manifestSha256'] != sha(dst / (name + '.json')):
        raise SystemExit('Unexpected male payload change ' + name)
(gold / 'provenance.json').write_text(json.dumps(rows, indent=2) + '\n')
male_after = {p.name: sha(p) for p in dst.glob('*Male*') if 'Female' not in p.name}
if male_after != male_before: raise SystemExit('Male payload changed')
changed = [str((dst / f).relative_to(repo)) for f in files] + [str((gold / (h + '_golden.lzfse')).relative_to(repo)) for h in heroes] + [str((gold / 'provenance.json').relative_to(repo))]
(backup / 'installed-paths.json').write_text(json.dumps(changed, indent=1))
(backup / 'after-hashes.json').write_text(json.dumps({c: sha(repo / c) for c in changed}, indent=1))
print('installed', len(files), 'files +', len(heroes), 'goldens + provenance; smoothness restored in', {k: len(v) for k, v in restored.items()}, '; male payloads unchanged')
