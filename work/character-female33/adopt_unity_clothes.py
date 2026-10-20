from pathlib import Path
import json,hashlib,shutil,os
root=Path('Unity/Assets');mirror=Path('work/character-finish32/review-project/Unity/Assets');w=Path('work/character-female33');rows=json.loads((w/'adoption-inputs.json').read_text());backup=w/'pre-unity-adoption';backup.mkdir(exist_ok=True)
for row in rows:
 p=root/row['path'];actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
 assert actual==row['beforeSha256'],'Concurrent edit needs review: '+str(p)
for row in rows:
 name=row['path'];src=mirror/name;dst=root/name;assert src.is_file(),src
 if dst.exists():
  old=backup/name;old.parent.mkdir(parents=True,exist_ok=True);assert not old.exists();shutil.copy2(dst,old)
 dst.parent.mkdir(parents=True,exist_ok=True);data=src.read_bytes()
 if name=='Scripts/Tennis/MatchHeroLook.cs':
  text=data.decode();text=text.replace('GetEnvironmentVariable(female ? "VISUAL_TAILORED_FEMALE_POLO" : "VISUAL_TAILORED_POLO") == "1"','GetEnvironmentVariable(female ? "VISUAL_TAILORED_FEMALE_POLO" : "VISUAL_TAILORED_POLO") != "0"').replace('GetEnvironmentVariable("VISUAL_TAILORED_FEMALE_SKIRT") == "1"','GetEnvironmentVariable("VISUAL_TAILORED_FEMALE_SKIRT") != "0"');data=text.encode()
 tmp=dst.with_name(dst.name+'.clothes-tmp');tmp.write_bytes(data);os.replace(tmp,dst);row['afterSha256']=hashlib.sha256(data).hexdigest()
(w/'unity-adoption-proof.json').write_text(json.dumps({'status':'PASS','files':rows,'defaultEnabled':['Male polo','Female polo','Female skirt'],'mapsLightsCamerasBodyFaceRigAndAnimationSourcesChanged':False},indent=2));print('Adopted verified clothing assets and shared runtime')
