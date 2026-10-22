"""Preserve independent Unity samples as compact, bundled regression fixtures."""
from pathlib import Path
import hashlib, json, subprocess, sys

repo = Path(__file__).resolve().parents[2]
source = repo / sys.argv[1]
destination = repo / 'GolfArcadeTests/VisualGolden'
destination.mkdir(parents=True, exist_ok=True)
names = ['MatchHero_Male', 'MatchHero_Female', 'MatchHero_Male_Distance',
         'MatchHero_Female_Distance', 'GolfKitHero_Male', 'GolfKitHero_Female']
records = []
for name in names:
    fixture = source / (name + '_golden.json')
    document = json.loads(fixture.read_text())
    if len(document['samples']) <= 100: raise ValueError('Insufficient samples: ' + name)
    packed = destination / (name + '_golden.lzfse')
    subprocess.run(['/usr/bin/compression_tool', '-encode', '-a', 'lzfse',
                    '-i', str(fixture), '-o', str(packed)], check=True)
    records.append({'name': name, 'source': str(fixture.relative_to(repo)),
                    'unitySampleCount': len(document['samples']),
                    'unitySourceSha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
                    'packedSha256': hashlib.sha256(packed.read_bytes()).hexdigest(),
                    'packedBytes': packed.stat().st_size})
(destination / 'provenance.json').write_text(json.dumps(records, indent=2))
print('Bundled six independent Unity golden fixtures; ' + str(sum(x['packedBytes'] for x in records)) + ' bytes.')
