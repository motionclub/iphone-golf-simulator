"""Merge independent Unity garment samples while preserving every other fixture sample."""
from pathlib import Path
import json,subprocess,hashlib,shutil,sys
w=Path('work/character-finish32/native');codec=w.resolve()/'cloth-codec';proof=Path('work/character-female33/fixture-proof');proof.mkdir(exist_ok=True);reports=[]
for stem in sys.argv[1:]:
 roles={'Kit_Top','Kit_Bottom'} if 'Female' in stem else {'Kit_Top'}
 candidate=w/'golden'/(stem+'_golden.json');source=json.loads(candidate.read_text());byKey={(s['clip'],s['frame'],s['part']):s for s in source['samples'] if s['part'] in roles}
 for folder in [Path('GolfArcadeTests/VisualGolden'),Path('GolfArcade/Unity/CharacterAssets')]:
  packed=folder/(stem+'_golden.lzfse')
  if not packed.exists():continue
  name=('tests-' if 'Tests' in str(folder) else 'app-')+stem;old=proof/(name+'-before.json');subprocess.run([str(codec),'decode',str(packed),str(old)],check=True);data=json.loads(old.read_text());originalOther=[s for s in data['samples'] if s['part'] not in roles];count=0
  for i,s in enumerate(data['samples']):
   if s['part'] not in roles:continue
   key=(s['clip'],s['frame'],s['part']);new=dict(byKey[key]);rows=new['vertices'];step=max(1,len(rows)//160);new['vertices']=rows[::step];data['samples'][i]=new;count+=1
  assert originalOther==[s for s in data['samples'] if s['part'] not in roles]
  merged=proof/(name+'.json');merged.write_text(json.dumps(data,separators=(',',':')));backup=proof/(name+'-before.lzfse');assert not backup.exists();shutil.copy2(packed,backup);temp=proof/(name+'.lzfse');subprocess.run([str(codec),'encode',str(merged),str(temp)],check=True);shutil.copy2(temp,packed)
  reports.append({'fixture':str(packed),'garmentParts':sorted(roles),'samplesUpdated':count,'nonGarmentSamplesPreserved':len(originalOther),'independentUnitySource':str(candidate),'sourceSha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'packedSha256':hashlib.sha256(packed.read_bytes()).hexdigest(),'status':'PASS'})
  if 'Tests' in str(folder):
   p=folder/'provenance.json';catalog=json.loads(p.read_text());row=next(x for x in catalog if x['name']==stem);row['garmentUpdate']=reports[-1];row['packedSha256']=reports[-1]['packedSha256'];row['packedBytes']=packed.stat().st_size;row['manifestSha256']=hashlib.sha256((Path('GolfArcade/Unity/CharacterAssets')/(stem+'.json')).read_bytes()).hexdigest();p.write_text(json.dumps(catalog,indent=2)+'\n')
(proof/'merge-report.json').write_text(json.dumps(reports,indent=2));print(reports)
