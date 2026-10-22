from pathlib import Path
import json,subprocess,hashlib,collections
O=Path(__file__).resolve().parent;R=O.parents[2];P=O.parent/'original-native-adoption1'
package=json.loads((P/'package-audit.json').read_text());names=[x['file'] for x in package['resources']];assert len(names)==119 and len(set(names))==119
stems=[p+s+x for p,x in [('MatchHero_',''),('MatchHero_','_Distance'),('GolfKitHero_','')] for s in ['Male','Female']];fixtures=[s+'_golden.lzfse' for s in stems];out={}
for project in ['GolfArcade','GolfArcadeUnity']:
 p=R/(project+'.xcodeproj/project.pbxproj');d=json.loads(subprocess.check_output(['plutil','-convert','json','-o','-',str(p)]))['objects'];phases={}
 for targetName,required in [('GolfArcade',names),('GolfArcadeTests',fixtures)]:
  target=next(x for x in d.values() if x.get('isa')=='PBXNativeTarget' and x.get('name')==targetName);rs=[d[x] for x in target['buildPhases'] if d[x]['isa']=='PBXResourcesBuildPhase'];assert len(rs)==1
  registered=[d[d[x]['fileRef']].get('path') for x in rs[0]['files']]
  for n in required:assert registered.count(n)==1,(project,targetName,n,registered.count(n))
  phases[targetName]={'requiredRegisteredExactlyOnce':len(required),'totalResourceEntries':len(registered)}
 out[project]={'gate':'PASS ALREADY REGISTERED, NO PBX PATCH REQUIRED','projectSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'phases':phases}
provenance=json.loads((R/'GolfArcadeTests/VisualGolden/provenance.json').read_text());assert set(x['name'] for x in provenance)==set(stems)
report={'gate':'PBX REGISTRATION PASS; FRESH ASSET/FIXTURE BYTES PENDING','runtimeResourceCount':119,'goldenFixtureCount':6,'projects':out,'registrationsNeedMutation':False,'legacyRegistrationGenerator':'Do not run original-native-adoption1/stage-registration.py; it deliberately rejects Already registered','currentFixtureProvenance':{'sources':sorted(set(x['source'].split('/')[2] for x in provenance)),'isSmooth1FreshFixtureEvidence':False,'contract':'Fresh six exports + fixtures required. VISUAL_GOLDEN_DIR points at new work/golden raw fixtures for all tests; shipping requires refreshed6 packed goldens in already-registered VisualGolden files.'},'skinPigmentUVTestContract':'stage exact mode2 update; oldmode1 must fail new adopted assets','oldPackagePath':'Names only reused from original-native-adoption1/package-audit.json, no old bytes accepted','productionWrites':False}
(O/'registration-gate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
