"""Promote only the reviewed standalone Resort21 sources; root owns Unity proof."""
from pathlib import Path
import hashlib,json,re,shutil,uuid

stage=Path(__file__).resolve().parent
repo=stage.parents[3]
baseline=json.loads((stage/'baseline.json').read_text())
installed=[]
for relative,expected in baseline.items():
    target=repo/relative
    staged=stage/target.name
    if target.read_bytes()==staged.read_bytes():
        continue
    if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
        raise ValueError('Live source changed since staging: '+relative)
    shutil.copyfile(staged,target);installed.append(relative)
new='Unity/Assets/Scripts/Tennis/TennisResortVista.cs'
shutil.copyfile(stage/'TennisResortVista.cs',repo/new)
meta=repo/(new+'.meta')
if not meta.exists():meta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
installed.append(new)
fbx='Unity/Assets/Resources/Tennis/Premium/TennisCoconutPalm.fbx'
shutil.copyfile(stage/'palm/TennisCoconutPalm.fbx',repo/fbx)
meta=repo/(fbx+'.meta')
if not meta.exists():
    schema=(repo/'Unity/Assets/Resources/Tennis/Premium/TennisCanopy.fbx.meta').read_text()
    schema=re.sub(r'guid: [a-f0-9]{32}','guid: '+uuid.uuid4().hex,schema,count=1)
    schema=schema.replace('  importAnimation: 1','  importAnimation: 0')
    meta.write_text(schema)
installed.append(fbx)
canonical=repo/'ArtDir/tennis/venues/botany/source';canonical.mkdir(parents=True,exist_ok=True)
shutil.copyfile(stage/'palm/TennisCoconutPalm.blend',canonical/'TennisCoconutPalm.blend')
shutil.copyfile(stage/'palm/palm-manifest.json',canonical/'TennisCoconutPalm-manifest.json')
files=[]
for relative in [*baseline,new,fbx,fbx+'.meta',new+'.meta',
                 'ArtDir/tennis/venues/botany/build-coconut-palm.py',
                 'ArtDir/tennis/venues/botany/source/TennisCoconutPalm.blend']:
    path=repo/relative
    files.append({'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
manifest={'checkpoint':'Resort21 primary architecture / ocean vista / coconut crowns',
 'status':'source reviewed candidate installed; actual Unity art and counters pending',
 'invariants':['court/net/lines/contact geometry unchanged','custom ball/net/ground rules unchanged',
               'no decorative collider added or removed','quality settings/cascades/shadow distance unchanged',
               '8 lens/pitch choices are capture-only; existing gameplay/1/9/14 cameras unchanged'],
 'forms':['low stepped ocean parapet with planted end bays','three continuous distant lush island mountains',
          'closer lathed limestone colonnade with deep timber rafters','independent arched feathered coconut crowns and actual far mesh'],
 'palm':json.loads((stage/'palm/palm-manifest.json').read_text()),'files':files}
proof=repo/'proof/full-visual-overhaul/tennis/world21-installed-manifest.json'
proof.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'installed':installed,'manifest':str(proof)},indent=2))
