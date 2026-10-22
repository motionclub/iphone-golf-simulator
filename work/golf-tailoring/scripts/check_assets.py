from pathlib import Path
import json,hashlib,struct
W=Path(__file__).resolve().parents[1];rows=[]
for sex in ['Male','Female']:
 path=W/'native'/f'GolfKitHero_{sex}.json';m=json.loads(path.read_text());cloth=[s['look'] for p in m['parts'] for s in p['submeshes'] if s.get('look',{}).get('shader')=='TennisCloth']
 assert cloth and all(x['fabricVersion']==2 for x in cloth)
 for part in m['parts']:
  if part['name']=='Kit_Top':
   for s in part['submeshes']:assert abs(s['look']['tileMetres']-.034)<1e-6
 files={x[k] for x in cloth for k in ['normalMap','maskMap','weaveMap'] if x.get(k)}
 for name in files:assert (W/'native'/f'{name}.ktx').exists() or (W.parents[1]/'GolfArcade/Unity/CharacterAssets'/f'{name}.ktx').exists(),name
 rows.append(dict(sex=sex,parts=len(m['parts']),clothSurfaces=len(cloth),maps=len(files),kitTriangles=json.loads((W/'data'/f'export_golf_{sex}.json').read_text())['totalKitTriangles']))
uv=json.loads((W/'data/uv_check.json').read_text());assert all(x['ambiguousTexels']==0 for x in uv)
(W/'data/final_asset_checks.json').write_text(json.dumps(dict(heroes=rows,uvAmbiguity=0),indent=2));print(rows)
