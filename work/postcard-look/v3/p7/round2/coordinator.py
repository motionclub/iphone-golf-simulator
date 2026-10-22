#!/usr/bin/env python3
"""Root-reviewed P7 round2 phases. Prepare writes scratch only; execution requires real heavy.sh.
No Unity, Git, automatic retries, rollback, baseline resets or threshold edits.
"""
import argparse, hashlib, json, os, re, shlex, shutil, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
V=R/'work/postcard-look/v3'; B=V/'p7/round2'; HEAVY=R/'work/postcard-look/heavy.sh'
BLENDER=Path('/Applications/Blender.app/Contents/MacOS/Blender')
HELPER=V/'p7/round1/source_batch/p7_batch.py'
TOOLS=[HEAVY,HELPER,R/'work/postcard-look/guards.sh',V/'audit/scoring_exact.py',V/'proof/check_protected.py',V/'proof/runtime/validate_installer.py',R/'work/postcard-look/v2/proof/install_holes.py',V/'start_sha.json',V/'additional_protected_sha.json']
ALLOWED={R/'blender/scripts/hole09_build.py',R/'blender/scripts/hole09_look.py',R/'blender/scripts/hole10_build.py'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def physical(p):
 p=Path(p).absolute()
 if p.resolve()!=p:raise RuntimeError('Symlink/noncanonical path: '+str(p))
 return p
def exact(p,s):
 p=physical(p);raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=s:raise RuntimeError('SHA drift: '+str(p))
 return raw
def fresh(p):
 p=physical(p)
 if not p.is_relative_to(B):raise RuntimeError('Output outside round2')
 p.mkdir(parents=True,exist_ok=False);return p
def save(p,q):
 p=physical(p)
 with p.open('x') as f:json.dump(q,f,indent=2);f.write('\n')
def hashes(paths):return {str(p):sha(p) for p in paths}
def check_hashes(q):
 for p,s in q.items():exact(p,s)
def heavy():
 owner=HEAVY.parent/'heavy.lock/owner'
 if not owner.is_file():raise RuntimeError('Actual heavy lock missing')
 pid=os.getppid()
 for _ in range(20):
  s=subprocess.check_output(['ps','-p',str(pid),'-o','ppid=','-o','args='],text=True).strip().split(None,1)
  if len(s)!=2:break
  argv=shlex.split(s[1])
  if argv and Path(argv[0]).name in ('bash','sh','zsh') and str(HEAVY) in argv[1:]:return
  pid=int(s[0])
  if pid<=1:break
 raise RuntimeError('Unchanged real heavy.sh shell ancestor required')
def protected_now():
 start=json.loads((V/'start_sha.json').read_bytes());extra=json.loads((V/'additional_protected_sha.json').read_bytes())['files']
 def frozen(p):return not (p.startswith('blender/scripts/') and not p.endswith('_design.py') and not p.startswith('blender/scripts/hole07') or p.startswith('Unity/Assets/Resources/Course/Look/') or p in {f'blender/hole_{n}.blend' for n in ('08','09','10')} or p in {f'Unity/Assets/Resources/Course/hole_{n}.fbx' for n in ('08','09','10')})
 files={p:s for p,s in start.items() if frozen(p)};files.update(extra);bad=[]
 for p,s in files.items():
  f=R/p
  if not f.is_file():bad.append(dict(path=p,reason='missing'));continue
  now=sha(f)
  if now!=s:bad.append(dict(path=p,expected=s,actual=now))
 return dict(gate='PROTECTED_FILES',ok=not bad,files_checked=len(files),changed_count=len(bad),changes=bad)
def same_protected(a,b):return all(a[k]==b[k] for k in ('gate','ok','files_checked','changed_count','changes'))
def guard(m,after):
 check_hashes(m['pins']);check_hashes(m['inputs_after' if after else 'inputs_before'])
 if not same_protected(protected_now(),m['reviewed_protected_FAIL']):raise RuntimeError('Unreviewed protected drift; original gate remains FAIL')
def call(out,name,argv,env=None,allow_rc=None):
 log=out/(name+'.log')
 e=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');e.update(env or {})
 with log.open('x') as f:rc=subprocess.run([str(x) for x in argv],cwd=R,env=e,stdout=f,stderr=subprocess.STDOUT).returncode
 print(name,'raw_exit',rc,'log',log,flush=True)
 if rc not in (allow_rc if allow_rc is not None else {0}):raise RuntimeError(name+' failed; raw log retained')
 return rc,log

def prepare(a):
 out=fresh(a.out);refs=[];entries=[]
 for p,s in zip(a.source_plan,a.source_sha):
  p=physical(p);q=json.loads(exact(p,s));refs.append(dict(path=str(p),sha256=s))
  if q['root']!=str(R) or q['v3']!=str(V):raise RuntimeError('Wrong upstream root')
  entries+=q['entries']
 if len({e['target'] for e in entries})!=len(entries) or not entries or any(Path(e['target']) not in ALLOWED for e in entries):raise RuntimeError('Overlapping/unapproved targets')
 targets={Path(e['target']) for e in entries}
 if not {R/'blender/scripts/hole09_build.py',R/'blender/scripts/hole09_look.py'}.issubset(targets):raise RuntimeError('The exact reviewed two-file H9 plan is required')
 before=json.loads((V/'p7/round1/rebuild/inputs_at_start.json').read_bytes())
 if len(before)!=48 or sum(p.endswith('.png') for p in before)!=31:raise RuntimeError('Established48 input set changed')
 before={str(R/p):s for p,s in before.items()};check_hashes(before);after=dict(before)
 for e in entries:
  exact(e['target'],e['old_sha256']);exact(e['old_snapshot'],e['old_sha256']);exact(e['draft'],e['new_sha256'])
  after[e['target']]=e['new_sha256']
 review=json.loads(exact(a.protected_review,a.protected_review_sha))
 if not same_protected(protected_now(),review):raise RuntimeError('Protected review is stale')
 eye=physical(a.eye_review);eyeq=json.loads(exact(eye,a.eye_review_sha))
 if eyeq.get('physicalImageReview') is not True or eyeq.get('round')!=2 or len(eyeq.get('holes',[]))!=3:raise RuntimeError('Physical round2 review missing')
 pins=hashes(TOOLS+[physical(__file__),eye,physical(a.protected_review)])
 for rec in eyeq['holes']:exact(rec['vsRef'],rec['vsRefSha256']);pins[rec['vsRef']]=rec['vsRefSha256']
 for ref in refs:pins[ref['path']]=ref['sha256']
 allrefs=[]
 for i,ref in enumerate(refs):
  q=json.loads(exact(ref['path'],ref['sha256']));q['protected']+= [dict(path=p,sha256=s) for p,s in pins.items()]
  p=out/f'derived_source_plan_{i}.json';save(p,q);allrefs.append(dict(path=str(p),sha256=sha(p)))
 merged=out/'source_batch.json';cmd=[sys.executable,HELPER,'compose']
 for ref in allrefs:cmd+=['--input-plan',ref['path'],'--input-sha',ref['sha256']]
 call(out,'compose',cmd+['--out',merged]);pins.update(hashes([merged]+[Path(x['path']) for x in allrefs]))
 stage=[p for n in ('08','09','10') for p in (V/f'hole{n}/stage').rglob('*') if p.is_file()]
 docs=[p for n in ('08','09','10') for p in (V/f'hole{n}').iterdir() if p.is_file() and (p.name=='INSTALL.md' or p.name.startswith('GATES') or p.name.endswith('sha256.txt') or 'sha_' in p.name)]
 special=V/'hole09/final/look_png_sha256_at_final_build.txt';docs.append(special)
 installed=[R/f'blender/hole_{n}.blend' for n in ('07','08','09','10')]+[R/f'Unity/Assets/Resources/Course/hole_{n}.{ext}' for n in ('07','08','09','10') for ext in ('fbx','fbx.meta')]
 for n in ('08','09','10'):
  paths=[s.split(None,1)[1] for s in (V/f'hole{n}/lib_sha_final.txt').read_text().splitlines() if re.match(r'^[a-f0-9]{64}\s',s)]
  if not paths or any(str(R/p) not in before for p in paths):raise RuntimeError('Unexpected lib list membership')
 pins.update(hashes([V/'p7/round1/rebuild/inputs_at_start.json']))
 m=dict(schema='p7_round2_reviewed_coordinator_v1',root=str(R),run=str(out),pins=pins,source_batch=str(merged),source_batch_sha=sha(merged),entries=entries,inputs_before=before,inputs_after=after,stages_before=hashes(stage),docs_before=hashes(docs),installed_before=hashes(installed),affected=sorted({Path(e['target']).name[4:6] for e in entries}),reviewed_protected_FAIL=review,native='UNMEASURED: separate final native runner; reused/skipped original still gates do not certify fresh candidate')
 p=out/'manifest.json';save(p,m);print('MANIFEST',p,'SHA256',sha(p))

def load(a):
 m=json.loads(exact(a.manifest,a.manifest_sha))
 if m['schema']!='p7_round2_reviewed_coordinator_v1' or m['root']!=str(R):raise RuntimeError('Wrong manifest')
 return m,physical(m['run'])
def receipt(out,q):
 p=out/'receipt.json';save(p,q);print('RECEIPT',p,'SHA256',sha(p),flush=True)
def source_apply(m,run):
 heavy();guard(m,False);check_hashes(m['stages_before']);check_hashes(m['docs_before']);check_hashes(m['installed_before'])
 out=fresh(run/'apply');call(out,'source_apply',[sys.executable,HELPER,'run','--manifest',m['source_batch'],'--manifest-sha',m['source_batch_sha'],'--result-dir',out/'actual_helper','--apply'])
 guard(m,True);receipt(out,dict(status='PASS',scope='Source apply only; build/native unverified',input_count=48))

def gates_json(p,key='gates'):
 q=json.loads(p.read_bytes());g=q[key] if key else q
 if not g or any(x.get('ok') is not True for x in g):raise RuntimeError('Original gates FAIL/empty: '+str(p))
 return g

def build(m,run):
 heavy();guard(m,True);check_hashes(m['stages_before']);check_hashes(m['docs_before']);check_hashes(m['installed_before']);out=fresh(run/'build')
 archive=out/'before';archive.mkdir();
 for p,s in {**m['stages_before'],**m['docs_before']}.items():
  dest=archive/Path(p).relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);exact(dest,s)
 save(out/'inputs_at_start.json',m['inputs_after']);stage=out/'candidate';stage.mkdir()
 measured={}
 for n in ('08','09','10'):
  target=stage/f'hole{n}/stage';target.mkdir(parents=True)
  if n not in m['affected']:
   for ext in ('blend','fbx'):shutil.copy2(V/f'hole{n}/stage/hole_{n}.{ext}',target/f'hole_{n}.{ext}')
   continue
  _,log=call(out,'build_hole'+n,[BLENDER,'-b','--factory-startup','--python',R/f'blender/scripts/hole{n}_build.py','--','--out',target,'--no-render','--qa'])
  if 'Traceback (most recent call last)' in log.read_text():raise RuntimeError('Builder exception even if Blender exit0')
  for ext in ('blend','fbx'):
   if not (target/f'hole_{n}.{ext}').is_file():raise RuntimeError('Missing export')
  bg=gates_json(target/('phase3_build.json' if n=='09' else 'build_gates.json'),'gates' if n=='09' else None)
  vf=out/f'verifier_hole{n}.json';args=[BLENDER,'-b','--factory-startup','--python',R/'blender/scripts/postcard_look_verify.py','--',str(int(n)),'--blend',target/f'hole_{n}.blend','--fbx',target/f'hole_{n}.fbx','--json',vf]
  # Existing H9 images verify only the original image-presence gate; these are not fresh compound-clump renders.
  stills=V/f'hole{n}/gate_stills'
  if n=='09' and all((stills/f'hole09_{shot}.png').is_file() for shot in ('tee','approach')):
   refs=hashes([stills/'hole09_tee.png',stills/'hole09_approach.png']);save(out/'reused_hole09_stills.json',dict(fresh_candidate=False,files=refs));args+=['--stills-dir',stills,'--require-stills']
  call(out,'verify_hole'+n,args);vg=gates_json(vf);measured[n]=dict(build=len(bg),verifier_measured=sum('SKIPPED' not in x['detail'] for x in vg),verifier_unmeasured=[x['name'] for x in vg if 'SKIPPED' in x['detail']],fresh_native=False)
  if n=='09':
   qa=out/'hole09_qa.json';call(out,'hole09_qa',[BLENDER,'-b','--factory-startup','--python',R/'blender/scripts/hole09_qa.py','--','--blend',target/'hole_09.blend','--fbx',target/'hole_09.fbx','--baseline',R/'work/postcard-look/baseline/blender/hole_09.blend','--json',qa]);measured[n]['qa']=len(gates_json(qa))
 # Execute the original comparator bytes unchanged: wrapper assigns __file__ to the original path and redirects only OUTPUT_STEM to an absolute scratch prefix.
 wrapper=out/'scoring_wrapper.py';wrapper.write_text("import os\nos.environ['POSTCARD_SCORING_STAGE_ROOT']="+repr(str(stage))+"\nos.environ['POSTCARD_SCORING_OUTPUT_STEM']="+repr(str(out/'scoring_exact'))+"\np="+repr(str(V/'audit/scoring_exact.py'))+"\nexec(compile(open(p,'rb').read(),p,'exec'),{'__name__':'__main__','__file__':p})\n")
 call(out,'scoring_exact',[BLENDER,'-b','--factory-startup','--python',wrapper]);q=json.loads((out/'scoring_exact.json').read_bytes())
 if not q['pass'] or len(q['results'])!=12 or any(not x['pass'] or x['threshold_m']!=0 or x['max_vertex_delta_m']!=0 or x['max_marker_delta_m']!=0 for x in q['results']):raise RuntimeError('Exact scoring12/12 threshold0 required')
 guard(m,True);check_hashes(m['stages_before']);check_hashes(m['docs_before']);check_hashes(m['installed_before'])
 artifacts=[p for p in stage.rglob('*') if p.is_file()]+list(out.glob('*.json'))+[wrapper]
 receipt(out,dict(status='PASS',scope='Original source/build/geometry/scoring only; fresh native UNMEASURED',affected=m['affected'],counts=measured,scoring_exact='12/12 threshold0m',artifacts=hashes(artifacts),inputs=m['inputs_after']))

def approved_receipt(path,s):
 q=json.loads(exact(path,s))
 if q['status']!='PASS':raise RuntimeError('Reviewed predecessor did not PASS')
 check_hashes(q.get('artifacts',{}));return q

def promote(m,run,a):
 heavy();guard(m,True);check_hashes(m['stages_before']);check_hashes(m['docs_before']);check_hashes(m['installed_before']);q=approved_receipt(run/'build/receipt.json',a.predecessor_sha);out=fresh(run/'promote')
 for n in m['affected']:
  source=run/f'build/candidate/hole{n}/stage';current=V/f'hole{n}/stage';arch=out/f'stage_before_hole{n}';current.rename(arch);shutil.copytree(source,current)
 pngs=sorted((R/'Unity/Assets/Resources/Course/Look').glob('*.png'))
 if len(pngs)!=31:raise RuntimeError('31 actual PNGs required')
 docs=[]
 for n in ('08','09','10'):
  d=V/f'hole{n}';lib=d/'lib_sha_final.txt';libpaths=[s.split(None,1)[1] for s in lib.read_text().splitlines() if re.match(r'^[a-f0-9]{64}\s',s)]
  lib.write_text(''.join(f'{sha(R/p)}  {p}\n' for p in libpaths));(d/'look_png_sha_final.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(R)}\n' for p in pngs))
  stage=d/'stage';(d/'stage_sha256.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(R)}\n' for p in sorted(stage.rglob('*')) if p.is_file()))
  stagehash=''.join(f'{sha(stage/f"hole_{n}.{ext}")}  {(stage/f"hole_{n}.{ext}").relative_to(R)}\n' for ext in ('blend','fbx'))
  (d/'capture_sha256.txt').write_text(stagehash)
  text=f'# Hole{n}: current P7 round2 stage\n\n'+('Rebuilt from the reviewed round2 source changes.' if n in m['affected'] else 'Binary stage retained unchanged from round1; no new builder run claimed.')+' Original geometry/scoring thresholds unchanged. Fresh native and eye review remain UNMEASURED. Protected baseline remains FAIL. Current dependency lists verify actual48 input bytes; prior build provenance is archived in '+str(run/'build/before')+'.\n\n'+stagehash+'\nActual current dependency verification: lib_sha_final.txt; all31 PNGs: look_png_sha_final.txt. stage_sha256.txt and capture_sha256.txt are actual hashes. Use unchanged installer pre then install under heavy; preserve installed meta bytes.\n'
  (d/'INSTALL.md').write_text(text);docs.extend([lib,d/'look_png_sha_final.txt',d/'stage_sha256.txt',d/'capture_sha256.txt',d/'INSTALL.md'])
 special=V/'hole09/final/look_png_sha256_at_final_build.txt';special.write_text(''.join(f'{sha(p)}  {p.name}\n' for p in pngs));docs.append(special)
 for n in m['affected']:
  report=V/f'hole{n}/GATES_round2.txt';report.write_text((run/f'build/verify_hole{n}.log').read_text()+'\nFresh candidate native appearance/performance UNMEASURED; inherited/skipped still checks are not fresh native PASS.\n');docs.append(report)
 guard(m,True);check_hashes(m['installed_before'])
 artifacts=hashes(docs+[p for n in ('08','09','10') for p in (V/f'hole{n}/stage').rglob('*') if p.is_file()])
 receipt(out,dict(status='PASS',scope='Stage promotion only; installed assets untouched; native UNMEASURED',build_receipt_sha=a.predecessor_sha,artifacts=artifacts))

def original_protected(out,name,m):
 old=V/'proof/protected_strict.json'
 if old.exists():shutil.copy2(old,out/(name+'_global_before.json'))
 rc,_=call(out,name,[sys.executable,V/'proof/check_protected.py'],allow_rc={0,1});q=json.loads(old.read_bytes());save(out/(name+'.json'),q)
 if not same_protected(q,m['reviewed_protected_FAIL']) or rc!=(1 if not q['ok'] else 0):raise RuntimeError('Unreviewed protected drift/raw exit mismatch')
 return dict(gate='PROTECTED_FILES',status='PASS' if q['ok'] else 'FAIL',raw_exit=rc,changed=q['changed_count'],continuation='Exact foreign observation reviewed; gate not exempted or passed')
def install(m,run,a):
 heavy();guard(m,True);q=approved_receipt(run/'promote/receipt.json',a.predecessor_sha);check_hashes(m['installed_before']);out=fresh(run/'install')
 call(out,'guards_pre',['bash',R/'work/postcard-look/guards.sh']);before=original_protected(out,'protected_pre',m)
 call(out,'validate_installer',[sys.executable,V/'proof/runtime/validate_installer.py',R]);call(out,'required_pre',[sys.executable,R/'work/postcard-look/v2/proof/install_holes.py','pre'])
 guard(m,True);check_hashes(q['artifacts']);check_hashes(m['installed_before'])
 call(out,'required_install',[sys.executable,R/'work/postcard-look/v2/proof/install_holes.py','install'])
 metas={p:s for p,s in m['installed_before'].items() if p.endswith('.meta') or 'hole_07.' in p};check_hashes(metas)
 for n in ('08','09','10'):
  for ext in ('blend','fbx'):
   dest=R/f'blender/hole_{n}.blend' if ext=='blend' else R/f'Unity/Assets/Resources/Course/hole_{n}.fbx'
   exact(dest,sha(V/f'hole{n}/stage/hole_{n}.{ext}'))
 call(out,'guards_after',['bash',R/'work/postcard-look/guards.sh']);guard(m,True);after=original_protected(out,'protected_after',m)
 receipt(out,dict(status='PASS',scope='Required pre/install and byte/meta guards completed; overall goal remains FAIL; native unmeasured',protected_gate_before=before,protected_gate_after=after,installed=hashes([Path(p) for p in m['installed_before']])))

def main():
 ap=argparse.ArgumentParser();s=ap.add_subparsers(dest='phase',required=True)
 p=s.add_parser('prepare');p.add_argument('--out',required=True);p.add_argument('--source-plan',action='append',required=True);p.add_argument('--source-sha',action='append',required=True);p.add_argument('--eye-review',required=True);p.add_argument('--eye-review-sha',required=True);p.add_argument('--protected-review',required=True);p.add_argument('--protected-review-sha',required=True)
 for name in ('apply','build','promote','install'):
  p=s.add_parser(name);p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha',required=True)
  if name in ('promote','install'):p.add_argument('--predecessor-sha',required=True)
 a=ap.parse_args()
 if a.phase=='prepare':
  if len(a.source_plan)!=len(a.source_sha):raise RuntimeError('Every reviewed source plan needs its SHA')
  prepare(a);return
 m,run=load(a)
 if a.phase=='apply':source_apply(m,run)
 elif a.phase=='build':build(m,run)
 elif a.phase=='promote':promote(m,run,a)
 else:install(m,run,a)
if __name__=='__main__':main()
