from pathlib import Path
import json,numpy as np,hashlib,shutil,uuid
R=Path(__file__).resolve().parents[3];W=R/'work/full-visual-overhaul/garment-coverage';D=R/'proof/full-visual-overhaul/character-pose-data-1/poses';S=W/'sleeve-geometry-9';P=W/'cloth9-package';P.mkdir(exist_ok=True)
files=[];reports=[]
for sex in ['Male','Female']:
 samples=sorted(S.glob(sex.lower()+'_*.json'));assert len(samples)==10
 base=json.loads((D/(sex.lower()+'_intro.json')).read_text())['parts'][1];source=json.loads((S/(sex.lower()+'_intro.json')).read_text());verts=np.array(source['bindVertices']).reshape(-1,3)
 out={'vertexCount':len(verts),'vertices':verts.ravel().tolist(),'normals':base['normals'],'anchors':[]}
 maximum=0
 for p in samples:
  a=json.loads(p.read_text());assert a['inverseOracleMaxMetres']<.000002
  basis=np.array(a['bindVertices']).reshape(-1,3);assert np.linalg.norm(basis-verts,axis=1).max()<.000002
  for name in ['deltas','normalDeltas','feature']:assert np.isfinite(a[name]).all()
  out['anchors'].append({'shape':p.stem,'feature':a['feature'],'deltas':[round(v,7) for v in a['deltas']],'normalDeltas':[round(v,7) for v in a['normalDeltas']]})
  maximum=max(maximum,a['inverseOracleMaxMetres'])
 target=P/('SleeveFit_'+sex+'.json');target.write_text(json.dumps(out,separators=(',',':')));files.append(target)
 reports.append({'sex':sex,'anchors':len(samples),'vertexCount':len(verts),'inverseLBSMaxMetres':maximum,'sourceComparisons':['IntroWave45','ReadyMiddle','PushupMiddle'],'status':'SOURCE-VALIDATED CANDIDATE; actual all-slot/LOD visual review required'})
# Install only the already reviewed sleeve candidate. Preserve root-owned
# bottom delegation rather than replacing its newly changed Tailoring file.
target=R/'Unity/Assets/Scripts/Tennis/HeroGarmentTailoring.cs';text=target.read_text();old='if(r.name=="Kit_Top")src=HeroGarmentAxillaWeights.Prepare(hero,r,src,palette);';new='if(r.name=="Kit_Top"){src=HeroGarmentSleeveGeometry.Prepare(hero,r,src,palette);src=HeroGarmentAxillaWeights.Prepare(hero,r,src,palette);}'
assert old in text;target.write_text(text.replace(old,new));installed=[target]
for name in ['HeroGarmentSleeveGeometry.cs','HeroGarmentPoseCorrectives.cs']:
 target=R/'Unity/Assets/Scripts/Tennis'/name;shutil.copy2(W/name,target);installed.append(target)
 meta=Path(str(target)+'.meta')
 if not meta.exists():meta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n')
for p in files:
 target=R/'Unity/Assets/Resources/Tennis/Correctives'/p.name;shutil.copy2(p,target);installed.append(target)
manifest={'checkpoint':'Cloth9 fitted upper-arm sleeve','status':'INSTALLED CANDIDATE; source comparison clean, runtime all-slot and LOD gate pending','scope':'Tennis Kit_Top full+low bind sleeve length; exact existing Top topology/UV/weights/rig; existing safe bounded Body axilla field retained. Golf garment geometry unchanged.','rootBottomBranchPreserved':'HeroShortsTailoring' in (R/'Unity/Assets/Scripts/Tennis/HeroGarmentTailoring.cs').read_text(),'profileReports':reports,'sourcePlateDirectory':'work/full-visual-overhaul/garment-coverage/sleeve-geometry-9','files':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in installed]}
assert manifest['rootBottomBranchPreserved'];(P/'installed-cloth9-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
