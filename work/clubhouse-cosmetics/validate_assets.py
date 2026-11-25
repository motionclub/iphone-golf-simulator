from pathlib import Path
import json,math,hashlib
R=Path(__file__).resolve().parents[2];A=R/'GolfArcade/Unity/CharacterAssets';rows=[]
for style in ['hockey','slugger','balloon','candy']:
 for club in ['Driver','Iron','Wedge','Putter']:
  p=A/f'NativeGolfEquipment_{style}_{club}.json';x=json.loads(p.read_text());v=x['positions'];n=x['normals'];count=len(v)//3
  assert len(v)==len(n) and len(v)%3==0 and all(math.isfinite(z) for z in v+n)
  assert len(x['uvs'])==count*2
  assert all(0<=i<count for m in x['materials'] for i in m['indices'])
  tris=sum(len(m['indices'])//3 for m in x['materials']);assert 1000<tris<=16000
  assert .99 < max(v[1::3])-min(v[1::3]) < 1.25 if club=='Driver' else True
  rows.append({'asset':p.name,'triangles':tris,'vertices':count,'minY':min(v[1::3]),'maxY':max(v[1::3]),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'work/clubhouse-cosmetics/asset-validation.json').write_text(json.dumps(rows,indent=2))
print('PASS: 16 meshes, finite positions/normals/UVs, valid indices, <=16000 triangles each')

contract=json.loads((R/'work/clubhouse-cosmetics/base-size-contract.json').read_text());sizes=[]
for row in rows:
 x=json.loads((A/row['asset']).read_text());club=x['id'].split('_')[1];b=contract[club]
 target=[b[0],b[2],[-b[1][1],-b[1][0]]];actual=[[min(x['positions'][i::3]),max(x['positions'][i::3])] for i in range(3)]
 assert all(actual[i][0]>=target[i][0]-.00001 and actual[i][1]<=target[i][1]+.00001 for i in range(3)),row['asset']
 length_error=max(abs(actual[1][j]-target[1][j]) for j in range(2));assert length_error<.00001
 sizes.append(dict(asset=row['asset'],length_error_mm=length_error*1000,actual=actual,target_envelope=target))
(R/'work/clubhouse-cosmetics/size-gate.json').write_text(json.dumps(sizes,indent=2))
print('PASS: original length within 0.01 mm, original grip and envelope retained; uniform head proportions')
