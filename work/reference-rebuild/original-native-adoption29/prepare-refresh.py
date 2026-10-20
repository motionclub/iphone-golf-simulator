from pathlib import Path
import json
O=Path(__file__).resolve().parent;R=O.parents[2];P=O.parent/'original-native-adoption1'
for name in ['export-work.py','package-resources.py','audit-package.py']:
 s=(P/name).read_text()
 if name=='audit-package.py':
  s=s.replace("l['skinPigmentUV']==1","l['skinPigmentUV']==contract['skinPigmentUV']").replace("pbx=TASK/(project+'.xcodeproj/project.pbxproj')","pbx=REPO/(project+'.xcodeproj/project.pbxproj')")
  s=s.replace(" d=json.loads((args.assets/(stem+'.json')).read_text());sex=d['sex'];", " profile='golf' if stem.startswith('GolfKit') else 'tennis-distance' if stem.endswith('_Distance') else 'tennis';identity=json.loads((TASK/(profile+'-export-identity.json')).read_text());assert identity['source_files']==contract['source_files'] and identity['unityPaletteShaderSha256']==contract['unity_palette_shader_sha256'],'Fresh export identity mismatch'\n d=json.loads((args.assets/(stem+'.json')).read_text());sex=d['sex'];")
  s=s.replace("assert g.is_file(),'Missing fresh independent fixture '+str(g)", "assert g.is_file(),'Missing fresh independent fixture '+str(g);assert g.stat().st_mtime>=identity['startedUnix'],'Stale fixture from before current export: '+str(g)")
  s=s.replace("report={'status':'PASS'", "if not args.manifest:assert len(plan)==119,'Unexpected runtime resource set; review before adoption'\nreport={'status':'PASS'")
 if name=='export-work.py':
  s=s.replace('import argparse,json,os,subprocess','import argparse,json,os,subprocess,hashlib,time').replace("['tennis','tennis-distance','golf','legacy-control']","['tennis','tennis-distance','golf']")
  s=s.replace("config=json.loads((TASK/'export-configs.json').read_text())", "config=json.loads((TASK/'export-configs.json').read_text());contract=json.loads((TASK/'accepted-contract.json').read_text())\nfor source,digest in contract['source_files'].items():assert hashlib.sha256((REPO/source).read_bytes()).hexdigest()==digest,'Frozen source hash changed: '+source\nassert hashlib.sha256((REPO/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader').read_bytes()).hexdigest()==contract['unity_palette_shader_sha256'],'Palette shader changed; regenerate exact contract after root accepts final palette'")
  s=s.replace("result=subprocess.run(command,cwd=REPO,env=dict(os.environ,**job['environment']))", "started=time.time();result=subprocess.run(command,cwd=REPO,env=dict(os.environ,**job['environment']))")
  s=s.replace("print(id+' export completed',flush=True)", "identity={'profile':id,'startedUnix':started,'endedUnix':time.time(),'environment':job['environment'],'source_files':contract['source_files'],'unityPaletteShaderSha256':contract['unity_palette_shader_sha256']}\n (TASK/(id+'-export-identity.json')).write_text(json.dumps(identity,indent=2)+'\\n')\n print(id+' export completed',flush=True)")
 if name=='package-resources.py':
  s=s.replace("assert names,'No garment maps'","assert names,'No garment maps'\nif not args.manifest:assert len(names)==50,'Unexpected complete garment map count; review before adoption'")
  s=s.replace("p.add_argument('--assets',type=Path,default=TASK/'export');args=p.parse_args()", "p.add_argument('--assets',type=Path,default=TASK/'export');p.add_argument('--manifest',action='append');args=p.parse_args()")
  old="for prefix,suffix in [('MatchHero_',''),('MatchHero_','_Distance'),('GolfKitHero_','')]:\n for sex in ['Male','Female']:\n  stem=prefix+sex+suffix;d=json.loads((EXPORT/(stem+'.json')).read_text());manifests.append(stem)"
  new="for stem in args.manifest or [prefix+sex+suffix for prefix,suffix in [('MatchHero_',''),('MatchHero_','_Distance'),('GolfKitHero_','')] for sex in ['Male','Female']]:\n  d=json.loads((EXPORT/(stem+'.json')).read_text());manifests.append(stem)"
  assert old in s;s=s.replace(old,new)
 (O/name).write_text(s)
flags={'VISUAL_ORIGINAL_SEAM':'1','VISUAL_ORIGINAL_BLINK':'1','VISUAL_ORIGINAL_EYE_MATERIAL':'1','VISUAL_CHARACTER_SKIN_FINISH':'1','VISUAL_CHARACTER_NORMALS':'continuous','VISUAL_REFERENCE_HEAD':'0','VISUAL_CHARACTER_LIP_FINISH':'1','MH_LOCKER_FACE_PARITY':'0'}
profiles={}
for name,method in [('tennis','Run'),('tennis-distance','RunDistance'),('golf','RunGolf')]:
 profiles[name]={'method':'GolfArcade.EditorTools.MatchHeroLockerExport.'+method,'environment':dict(flags,MH_LOCKER_OUT=str(O/'export'),MH_LOCKER_GOLDEN=str(O/'golden'),MH_LOCKER_REPORT=str(O/(name+'-export.txt'))),'logFile':str(O/(name+'-unity.log'))}
(O/'export-configs.json').write_text(json.dumps({'projectPath':str(R/'Unity'),'serial_order':list(profiles),'profiles':profiles,'all_output_paths_work_only':True,'cleanShippingClipContract':'tennis15 rig clips plus12 practice frames; golf6 clips plus0 practice frames; MH_LOCKER_FACE_PARITY0 prevents proof-only forehand clip tail','rootMustAuthorizeAndSerializeExports':True},indent=2)+'\n')
# Only8KB source harness; no big archives or old export/golden copying.
s=(P/'NativeParity.swift').read_text();s=s.replace('for (golf,distance) in [(false,false),(false,true),(true,false)]', 'let variants: [(Bool,Bool)] = ProcessInfo.processInfo.environment["NATIVE_PROOF_TENNIS_ONLY"] == "1" ? [(false,false),(false,true)] : [(false,false),(false,true),(true,false)]\n        for (golf,distance) in variants');(O/'NativeParity.swift').write_text(s)
