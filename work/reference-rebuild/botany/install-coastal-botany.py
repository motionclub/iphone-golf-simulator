"""Install only the inspected standalone coastal botany candidate. No shared kit edits."""
from pathlib import Path
import json,hashlib,shutil,uuid,re
stage=Path(__file__).resolve().parent;repo=stage.parents[2]
manifest=json.loads((stage/'source-manifest.json').read_text())
assert len(manifest['objects'])==12
assert all(x['boundary']==0 and x['nonmanifold']==0 for x in manifest['objects'])
for name in ['conifer-near.png','conifer-far.png','understory-near.png','understory-far.png']:
 assert (stage/name).is_file(),name
files=[]
for source,target in [
 (stage/'CoastalBotany.blend',repo/'ArtDir/golf/source/CoastalBotany.blend'),
 (stage/'CoastalBotany.fbx',repo/'Unity/Assets/Resources/Course/Resort/CoastalBotany.fbx'),
 (stage/'GolfCoastalBotany.cs',repo/'Unity/Assets/Scripts/Course/GolfCoastalBotany.cs')]:
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);files.append(target)
asset=repo/'Unity/Assets/Resources/Course/Resort/CoastalBotany.fbx.meta'
if not asset.exists():
 text=(repo/'Unity/Assets/Resources/Course/Resort/BotanicalKit.fbx.meta').read_text()
 text=re.sub(r'guid: [a-f0-9]{32}','guid: '+uuid.uuid4().hex,text,count=1)
 text=text.replace('  importAnimation: 1','  importAnimation: 0')
 assert '  isReadable: 1' in text
 asset.write_text(text)
files.append(asset)
code=repo/'Unity/Assets/Scripts/Course/GolfCoastalBotany.cs.meta'
if not code.exists():code.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
files.append(code)
for rel in ['ArtDir/golf/tools/build-coastal-botany.py','ArtDir/golf/tools/render-coastal-botany.py']:
 files.append(repo/rel)
for name in ['conifer-near.png','conifer-far.png','understory-near.png','understory-far.png']:
 files.append(stage/name)
manifest.update({'status':'installed source-reviewed candidate; root actual Unity art/counters pending',
 'runtime':'GolfArcade.Course.GolfCoastalBotany.Apply(model,hole); early returns unless hole12; root/golf owner hooks it after original physics/material setup',
 'invariants':['BotanicalKit and all other venue meshes unchanged','original Tree/Bush obstacle pivots retained','MeshFilters/colliders/obstacles/Ground/contact unchanged','new low crest clusters only on ray-validated original rough terrain, rejecting playable overlays/tee/green/landmarks','no added collider and no quality/camera/lighting/water/grass edit'],
 'detail':'one vertex-palette material, per-tree real near/far LOD,22-yard-cell understory batches with pocket-scale detail distance;42 maximum crest pockets',
 'files':[{'path':str(p.relative_to(repo)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files]})
(repo/'ArtDir/golf/coastal-botany-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'status':manifest['status'],'manifest':'ArtDir/golf/coastal-botany-manifest.json','installed':[str(p.relative_to(repo)) for p in files[:5]]},indent=2))
