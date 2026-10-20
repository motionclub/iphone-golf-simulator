"""Fail closed on omitted LUT/KTX/blob/variant; emit exact publication plan only."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile
from PIL import Image
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,default=TASK/'export');p.add_argument('--golden',type=Path,default=TASK/'golden');p.add_argument('--bundle',type=Path);p.add_argument('--manifest',action='append');p.add_argument('--output',type=Path,default=TASK/'package-audit.json');args=p.parse_args()
contract=json.loads((TASK/'accepted-contract.json').read_text());required=args.manifest or [prefix+sex+suffix for prefix,suffix in [('MatchHero_',''),('MatchHero_','_Distance'),('GolfKitHero_','')]for sex in ['Male','Female']]
files=set();rows=[]
for stem in required:
 profile='golf' if stem.startswith('GolfKit') else 'tennis-distance' if stem.endswith('_Distance') else 'tennis';identity=json.loads((TASK/(profile+'-export-identity.json')).read_text());assert identity['source_files']==contract['source_files'] and identity['unityPaletteShaderSha256']==contract['unity_palette_shader_sha256'],'Fresh export identity mismatch'
 d=json.loads((args.assets/(stem+'.json')).read_text());sex=d['sex'];golf=stem.startswith('GolfKit');rig=d['rig']
 assert rig['bones']==contract['bones']+(['Club'] if golf else []),stem+': exact character/Club bone order'
 assert len(d['swingFrames'])==len(d['swingTimes'])==(0 if golf else 12),stem+': exact existing practice frame count (golf0/tennis12)'
 files.update([stem+'.json',stem+'.lzfse',rig['file']+'.lzfse']);files.update(f+'.lzfse' for f in d['swingFrames'])
 for role in ['Body','Face']:
  part=next(p for p in d['parts'] if p['name']==role);rp=next(p for p in rig['parts'] if p['part']==role)
  assert part['vertexCount']==rp['vertexCount']==contract['counts'][sex][role],stem+'/'+role+': accepted source count drift'
  assert part['uvOffset']>=0,stem+'/'+role+': required UV0 missing'
  assert (part['bindPositionOffset']>=0)==(role=='Body'),stem+'/'+role+': bind channel contract'
  assert rp['kind']=='skin',stem+'/'+role+': active original skinned source missing'
  assert [m['name'] for m in rp['morphs']]==contract['morph_names'],stem+'/'+role+': exact half/full blink contract'
  for sub in part['submeshes']:
   l=sub['look']
   if role=='Body':assert l['skinFinish']==(2 if sex=='Female' else 1) and l['skinPigmentUV']==contract['skinPigmentUV'] and l['baseMapLinear'] and l['baseMap']=='MatchHero_OriginalSeam_RelativeSkinPigment'
   else:assert l['anatomicalFace'] is True,'Do not re-enable old decal/gaze overlay on original features'
 for part in d['parts']:
  for sub in part['submeshes']:
   l=sub['look'];garment=l.get('useGarmentMaps',0)>.5
   for key in ['baseMap','bumpMap','normalMap','maskMap','weaveMap']:
    name=l.get(key)
    if name:files.add(name+('.ktx' if garment and key in ['normalMap','maskMap','weaveMap'] else '.png'))
 for suffix in ['_golden.json','_blink_parity.json','_emote_parity.json']:
  g=args.golden/(stem+suffix);assert g.is_file(),'Missing fresh independent fixture '+str(g);assert g.stat().st_mtime>=identity['startedUnix'],'Stale fixture from before current export: '+str(g)
 blink=json.loads((args.golden/(stem+'_blink_parity.json')).read_text())
 assert set(s['blink']for s in blink['samples'])=={0,.25,.5,.75,1},stem+': all blink stages required'
 assert set(s['part']for s in blink['samples'])=={'Body','Face'}
 rows.append({'manifest':stem,'sex':sex,'bones':len(rig['bones']),'source_counts':contract['counts'][sex]})
for name,digest in contract['luts'].items():
 assert sha(args.assets/name)==digest,'Accepted linear LUT changed: '+name
 files.add(name)
for path,digest in contract['source_files'].items():assert sha(REPO/path)==digest,'Unaccepted source substitution: '+path
# Both staged PBXs must actually copy every referenced file, not just list a group.
registrations={}
for project in ['GolfArcade','GolfArcadeUnity']:
 pbx=REPO/(project+'.xcodeproj/project.pbxproj');obj=json.loads(subprocess.check_output(['/usr/bin/plutil','-convert','json','-o','-',str(pbx)]))['objects']
 app=next(o for o in obj.values()if o.get('isa')=='PBXNativeTarget'and o.get('name')=='GolfArcade');phase=next(obj[i]for i in app['buildPhases']if obj[i]['isa']=='PBXResourcesBuildPhase')
 names=[obj[obj[b]['fileRef']].get('path')for b in phase['files']]
 for file in files:assert names.count(file)==1,project+': missing/duplicate app resource '+file
 registrations[project]='PASS every referenced app resource exactly once'
plan=[]
for name in sorted(files):
 source=args.assets/name;assert source.is_file(),'Missing runtime resource '+str(source)
 destination=REPO/'GolfArcade/Unity/CharacterAssets'/name
 row={'file':name,'sha256':sha(source),'bytes':source.stat().st_size,'current_production_sha256':sha(destination)if destination.is_file()else None}
 if args.bundle:
  bundled=args.bundle/name;assert bundled.is_file(),'Bundle copy missing '+str(bundled)
  row['bundleSha256']=sha(bundled)
  if row['bundleSha256']!=row['sha256']:
   # Xcode copypng emits CgBI iPhone-optimized PNGs. Verify the exact decoded
   # samples after reversing that container transform; never waive blob drift.
   assert name.endswith('.png') and b'CgBI' in bundled.read_bytes()[:64],'Bundle stale bytes: '+name
   with tempfile.TemporaryDirectory(prefix='bundle-png-',dir=TASK) as temp:
    decoded=Path(temp)/name
    subprocess.run(['xcrun','pngcrush','-revert-iphone-optimizations','-q',str(bundled),str(decoded)],check=True,capture_output=True)
    original=Image.open(source);restored=Image.open(decoded)
    assert original.size==restored.size and original.mode==restored.mode,'Bundle PNG format drift: '+name
    assert original.tobytes()==restored.tobytes(),'Bundle PNG pixel drift: '+name
    for key in ['icc_profile','gamma','srgb','chromaticity']:
     assert original.info.get(key)==restored.info.get(key),'Bundle PNG color metadata drift: '+name
    row['bundleVerification']='Exact decoded PNG samples and color metadata after Xcode CgBI reversal'
    row['decodedPixelSha256']=hashlib.sha256(original.tobytes()).hexdigest()
  else:row['bundleVerification']='Exact bytes'
 plan.append(row)
sidecars=[]
for name in sorted(files):
 if name.endswith('.ktx'):
  png=args.assets/(name[:-4]+'.png');assert png.is_file(),'Missing compression source '+str(png)
  sidecars.append({'file':png.name,'sha256':sha(png),'bytes':png.stat().st_size})
if not args.manifest:assert len(plan)==119,'Unexpected runtime resource set; review before adoption'
report={'status':'PASS','scope':'subset proof rehearsal'if args.manifest else'all six adoption exports','variants':rows,'registrations':registrations,'resources':plan,'source_png_sidecars':sidecars,'bundle':'PASS exact blobs and decoded PNG pixels/metadata'if args.bundle else'NOT RUN','production_writes':False}
args.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(required),'variants',len(plan),'exact runtime files; bundle',report['bundle'])
