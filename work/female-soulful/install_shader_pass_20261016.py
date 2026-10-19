#!/usr/bin/env python3
"""Female shader pass 2026-10-16: guarded production install.

Native: GolfArcade/Unity/MatchHeroSurfaces.swift from work/female-soulful/native-shader/.
Unity: HeroLighting.hlsl, HeroFaceSkin.shader, TennisCharacter.shader, TennisCloth.shader and
FemaleGarmentFinish.cs from work/female-soulful/unity/ (identical to the reviewed clone files).
Native: merges ONLY the material keys that the clone export changed (wrap, weaveNormal, weaveThread,
normalStrength, smoothness, femaleSurface) into the three female manifests; geometry, rig, maps and
goldens are untouched (their export hashes are identical to production). Refreshes the VisualGolden
provenance look-source hashes and female manifest hashes. Male payloads must not change.
Backups + before/after hashes: work/female-soulful/revisions/shader-pass-install-20261016/.
usage: install_shader_pass_20261016.py [--rollback]
"""
import hashlib, json, pathlib, shutil, sys

repo = pathlib.Path(__file__).resolve().parents[2]
work = repo / 'work/female-soulful'
backup = work / 'revisions/shader-pass-install-20261016'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
unity = {'HeroLighting.hlsl': 'Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl',
         'HeroFaceSkin.shader': 'Unity/Assets/Resources/Tennis/Shaders/HeroFaceSkin.shader',
         'TennisCharacter.shader': 'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader',
         'TennisCloth.shader': 'Unity/Assets/Resources/Tennis/Shaders/TennisCloth.shader',
         'FemaleGarmentFinish.cs': 'Unity/Assets/Scripts/Tennis/FemaleGarmentFinish.cs'}
clone = pathlib.Path('/private/tmp/female-soulful-UnityClone')
heroes = ['MatchHero_Female', 'MatchHero_Female_Distance', 'GolfKitHero_Female']
dst = repo / 'GolfArcade/Unity/CharacterAssets'; gold = repo / 'GolfArcadeTests/VisualGolden'
export = work / 'native-shader/assets'
keys = {'wrap', 'weaveNormal', 'weaveThread', 'normalStrength', 'smoothness', 'femaleSurface'}
native = repo / 'GolfArcade/Unity/MatchHeroSurfaces.swift'
targets = [repo / p for p in unity.values()] + [native] + [dst / (h + '.json') for h in heroes] + [gold / 'provenance.json']
# Production native file must still be the state this candidate was built on.
NATIVE_BEFORE = '8537cde6351c3aaada8dc3aa3f9cba46afa3df24844eca09fddce3eeceaa6542'

if '--rollback' in sys.argv:
    for t in targets: shutil.copy2(backup / t.name, t)
    print('rolled back', len(targets), 'files'); sys.exit()

# Reviewed sources: the work mirror must equal the clone that produced every proof image.
for name, rel in unity.items():
    src = work / 'unity' / name
    cl = clone / rel
    if cl.exists() and sha(src) != sha(cl): raise SystemExit('mirror != clone: ' + name)
male_before = {p.name: sha(p) for p in dst.glob('*Male*') if 'Female' not in p.name}
backup.mkdir(parents=True, exist_ok=True)
hashes = {'before': {str(t.relative_to(repo)): sha(t) for t in targets}}
for t in targets: shutil.copy2(t, backup / t.name)

if sha(native) != NATIVE_BEFORE: raise SystemExit('production MatchHeroSurfaces.swift changed since the candidate was built; re-port first')
tmp = native.with_name(native.name + '.installing'); shutil.copy2(work / 'native-shader/MatchHeroSurfaces.swift', tmp); tmp.replace(native)
for name, rel in unity.items():
    t = repo / rel; tmp = t.with_name(t.name + '.installing'); shutil.copy2(work / 'unity' / name, tmp); tmp.replace(t)

def merge(prod, new, path, changed):
    if isinstance(prod, dict) and isinstance(new, dict):
        for k in new:
            if k in keys and not isinstance(new[k], (dict, list)) and prod.get(k) != new[k]:
                changed.append(path + '/' + k); prod[k] = new[k]
            elif k in prod: merge(prod[k], new[k], path + '/' + k, changed)
    elif isinstance(prod, list) and isinstance(new, list):
        if len(prod) != len(new): raise SystemExit('list length differs at ' + path)
        for i, (a, b) in enumerate(zip(prod, new)): merge(a, b, f'{path}[{i}]', changed)

report = {}
for h in heroes:
    t = dst / (h + '.json'); prod = json.loads(t.read_text()); new = json.loads((export / (h + '.json')).read_text())
    for f in (h + '.lzfse', h + '_Rig.lzfse'):
        if sha(dst / f) != sha(export / f): raise SystemExit('geometry differs from export: ' + f)
    changed = []; merge(prod, new, '', changed); report[h] = changed
    tmp = t.with_suffix('.json.installing'); tmp.write_text(json.dumps(prod, indent=4)); tmp.replace(t)

rows = json.loads((gold / 'provenance.json').read_text())
paths = [s.strip() for s in (repo / 'work/hero-sync/look_sources.txt').read_text().splitlines() if s.strip() and not s.startswith('#')]
look = {s: sha(repo / s) for s in paths}
for row in rows:
    row['heroLookSourceFiles'] = look
    if row['name'] in heroes:
        row['manifestSha256'] = sha(dst / (row['name'] + '.json'))
        row['note'] = (row.get('note', '') + ' | Shader pass 2026-10-16: female skin/eye/knit material response; manifests carry the clone material values (geometry/goldens unchanged).').strip(' |')
    elif row.get('manifestSha256') and row['manifestSha256'] != sha(dst / (row['name'] + '.json')):
        raise SystemExit('Unexpected male payload change ' + row['name'])
(gold / 'provenance.json').write_text(json.dumps(rows, indent=2) + '\n')
if {p.name: sha(p) for p in dst.glob('*Male*') if 'Female' not in p.name} != male_before: raise SystemExit('Male payload changed')
hashes['after'] = {str(t.relative_to(repo)): sha(t) for t in targets}
hashes['manifestKeysChanged'] = {h: len(v) for h, v in report.items()}
(backup / 'hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
print('installed', len(unity), 'Unity files;', {h: len(v) for h, v in report.items()}, 'manifest keys; provenance refreshed; male unchanged')
