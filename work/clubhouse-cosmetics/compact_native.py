"""Deduplicate identical exported position/normal/UV tuples without changing triangles."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
for p in (R/'GolfArcade/Unity/CharacterAssets').glob('NativeGolfEquipment_*_*.json'):
 x=json.loads(p.read_text());seen={};positions=[];normals=[];uvs=[];remap=[]
 for i in range(len(x['positions'])//3):
  key=tuple(x['positions'][i*3:i*3+3]+x['normals'][i*3:i*3+3]+x['uvs'][i*2:i*2+2])
  if key not in seen:
   seen[key]=len(positions)//3;positions.extend(key[:3]);normals.extend(key[3:6]);uvs.extend(key[6:])
  remap.append(seen[key])
 for m in x['materials']:m['indices']=[remap[i] for i in m['indices']]
 x.update(positions=positions,normals=normals,uvs=uvs);p.write_text(json.dumps(x,separators=(',',':')))
print('Compacted native geometry without changing topology or shading')
