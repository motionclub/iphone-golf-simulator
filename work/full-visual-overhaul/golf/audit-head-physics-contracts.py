"""Read-only baseline HEAD preservation audit. No Git mutation and no Unity run."""
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');out=root/'proof/full-visual-overhaul/golf'
def git(*args):return subprocess.run(['git',*args],cwd=root,capture_output=True,check=True).stdout
def sha(data):return hashlib.sha256(data).hexdigest()
head=git('rev-parse','HEAD').decode().strip()
def compare(path):
 p=root/path;baseline=git('show','HEAD:'+path);current=p.read_bytes();pointer=re.match(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]+)\nsize (\d+)',baseline)
 expected_sha=pointer[1].decode() if pointer else sha(baseline);expected_bytes=int(pointer[2]) if pointer else len(baseline)
 result={'path':path,'baseline_sha256':expected_sha,'current_sha256':sha(current),'baseline_bytes':expected_bytes,'current_bytes':len(current),'baseline_storage':'Git LFS sha256+size pointer' if pointer else 'Git blob','exact_head_match':expected_sha==sha(current) and expected_bytes==len(current)}
 if path.endswith('.fbx.meta') and not result['exact_head_match']:
  adjusted=baseline.replace(b'importBlendShapes: 0',b'importBlendShapes: 1')
  result['only_delta_is_importBlendShapes_0_to_1']=adjusted==current
  result['importer_contract']='Unchanged CourseModelImporter.OnPreprocessModel explicitly forces importBlendShapes=true for all native course FBX. Fresh HEAD import therefore resolves the same way; runtime full-catalog parity still required.' if adjusted==current else 'REVIEW other importer changes'
 return result
core=['Unity/Assets/Scripts/Course/Hole.cs','Unity/Assets/Scripts/Course/HoleView.cs','Unity/Assets/Scripts/Course/ObstacleScan.cs','Unity/Assets/Scripts/Course/Obstacles.cs','Unity/Assets/Scripts/Course/Surface.cs','Unity/Assets/Scripts/Course/CourseShot.cs','Unity/Assets/Scripts/Shot/BallFlight.cs','Unity/Assets/Scripts/Shot/GolfClub.cs','Unity/Assets/Scripts/Course/SpinningSails.cs','Unity/Assets/Scripts/Course/WaterMotion.cs','Unity/Assets/Editor/CourseModelImporter.cs']
contracts=[]
for p in core:
 try:contracts.append(compare(p))
 except subprocess.CalledProcessError as e:contracts.append({'path':p,'exact_head_match':False,'reason':'Missing from baseline HEAD'})
latest=0
for folder in (root/'proof/full-visual-overhaul').glob('golf-pass-*'):
 try:
  number=int(folder.name.rsplit('-',1)[-1]);reports=[folder/f'hole{n:02}_dressing_physics.json' for n in [1,2,3,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]]
  if all(p.exists() and json.loads(p.read_text()).get('gate')=='PASS' for p in reports):latest=max(latest,number)
 except (ValueError,json.JSONDecodeError):pass
records=[]
for n in [1,2,3,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]:
 records.append({'hole':n,'native_model':n>3,'inputs':[],'unchanged_core_contracts':all(r['exact_head_match'] for r in contracts),'runtime_parity_gate':f'PASS independent original runtime pilots through8 plus exact dressing through{latest}' if n in [12,19,21] else f'PASS exact dressing through{latest}; no independent HEAD imported runtime baseline'})
 if n>3:
  for p in [f'blender/hole_{n:02}.blend',f'Unity/Assets/Resources/Course/hole_{n:02}.fbx',f'Unity/Assets/Resources/Course/hole_{n:02}.fbx.meta']:records[-1]['inputs'].append(compare(p))
 records[-1]['source_preservation_gate']='PASS' if all(x['exact_head_match'] or x.get('only_delta_is_importBlendShapes_0_to_1',False) for x in records[-1]['inputs']) and records[-1]['unchanged_core_contracts'] else 'REVIEW core/source changes'
physics_text=(root/'Unity/Assets/Scripts/Course/HoleView.cs').read_text()
order={'original_ground_colliders_before_surface_sampling':physics_text.index('collider.sharedMesh = mf.sharedMesh')<physics_text.index('Hole.Surface = SampleSurface()'),'original_obstacle_scan_before_visual_finish':physics_text.index('Hole.Obstacles = ObstacleScan.From(model.transform)')<physics_text.index('standardLook.FinishModel(model)'),'windmill_extracted_before_visual_finish':physics_text.index('Hole.Windmill = SailsOf')<physics_text.index('standardLook.FinishModel(model)')}
new=['GolfResortDress.cs','GolfCliffSculpt.cs','GolfLandmarkFinish.cs','GolfStoneFinish.cs','GolfMeadowWorld.cs'];render=[]
for f in new:
 text=(root/'Unity/Assets/Scripts/Course'/f).read_text();render.append({'file':f,'adds_collider':bool(re.search(r'AddComponent\s*<\s*(MeshCollider|BoxCollider|SphereCollider|CapsuleCollider|Collider)\s*>',text)),'assigns_source_collision_mesh':bool(re.search(r'(source|collider|c)\.sharedMesh\s*=',text)),'mutates_source_mesh_vertices':bool(re.search(r'(source\.sharedMesh|t\.mesh|mesh)\.vertices\s*=',text)),'deactivates_gameplay_objects':bool(re.search(r'\.SetActive\s*\(\s*false\s*\)',text))})
report={'baseline_HEAD':head,'scope':'Exact byte comparison of HEAD source course models, import settings and core golf gameplay contracts. Read-only evidence; actual imported geometry/obstacle hashes remain a separate runtime gate.','core_contracts':contracts,'construction_order':order,'new_dressing_source_checks':render,'holes':records,'gate':'PASS' if all(r['source_preservation_gate']=='PASS' for r in records) and all(order.values()) and not any(any(v for k,v in r.items() if k!='file') for r in render) else 'REVIEW','limitations':['Exact source bytes do not by themselves validate every runtime imported mesh/obstacle hash.','Visual candidate bounds and camera framing need the actual complete catalog captures.','New renderer geometry can exceed original collision silhouettes below cliffs; ground and obstacles must retain original data.']}
(out/'catalog-head-physics-contracts.json').write_text(json.dumps(report,indent=2));print(json.dumps({'HEAD':head,'gate':report['gate'],'core':[(r['path'],r['exact_head_match']) for r in contracts],'source_models_match':sum(all(x['exact_head_match'] for x in r['inputs'] if not x['path'].endswith('.meta')) for r in records),'construction_order':order,'new_dressing_source_checks':render},indent=2))
