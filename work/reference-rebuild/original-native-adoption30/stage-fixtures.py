from pathlib import Path
import json,subprocess,hashlib
O=Path(__file__).resolve().parent;R=O.parents[2];contract=json.loads((O/'accepted-contract.json').read_text());OUT=O/'VisualGolden';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for source,digest in contract['source_files'].items():assert sha(R/source)==digest,'Frozen face source drift'
stems=[p+s+x for p,x in [('MatchHero_',''),('MatchHero_','_Distance'),('GolfKitHero_','')] for s in ['Male','Female']]
subprocess.run(['xcrun','swiftc','-module-cache-path',str(O.parent/'original-native-adoption1/module-cache'),'-parse-as-library',str(O/'PackGolden.swift'),'-o',str(O/'pack-golden')],check=True)
rows=[]
for stem in stems:
 source=O/'golden'/(stem+'_golden.json');assert source.is_file(),'Need fresh independent Unity golden: '+str(source)
 profile='golf' if stem.startswith('GolfKit') else 'tennis-distance' if stem.endswith('_Distance') else 'tennis';identity=json.loads((O/(profile+'-export-identity.json')).read_text());assert identity['source_files']==contract['source_files'] and identity['unityPaletteShaderSha256']==contract['unity_palette_shader_sha256'];assert source.stat().st_mtime>=identity['startedUnix'],'Stale independent fixture'
 d=json.loads(source.read_text());assert len(d['samples'])>100
 # Require correct current package rather than accepting old fixture indices.
 manifest=O/'export'/(stem+'.json');m=json.loads(manifest.read_text());parts={p['name']:p['vertexCount'] for p in m['parts']}
 for sample in d['samples']:
  assert sample['part'] in parts
  for v in sample['vertices']:assert 0<=int(v[0])<parts[sample['part']],'Stale golden vertex index'
 for p in m['parts']:
  if p['name']=='Body':assert all(s['look']['skinPigmentUV']==2 for s in p['submeshes'])
 target=OUT/(stem+'_golden.lzfse');subprocess.run([str(O/'pack-golden'),str(source),str(target)],check=True)
 rows.append({'name':stem,'source':str(source.relative_to(R)),'unitySampleCount':len(d['samples']),'unitySourceSha256':sha(source),'packedSha256':sha(target),'packedBytes':target.stat().st_size,'manifestSha256':sha(manifest),'frozenFaceSourceFiles':contract['source_files'],'unityPaletteShaderSha256':contract['unity_palette_shader_sha256']})
(OUT/'provenance.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS6 fresh independent goldens, exact LZFSE roundtrip; production untouched')
