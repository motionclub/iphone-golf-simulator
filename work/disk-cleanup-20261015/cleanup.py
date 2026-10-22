"""Remove preflighted generated caches; preserve sources and custom captures."""
import os, json, shutil, subprocess, time
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
report=repo/'work/disk-cleanup-20261015'
rows=json.load(open('/private/tmp/tennis-cleanup-plan.json'))
cache_names={'APIUpdater','Artifacts','ArtifactDB','ArtifactDB-lock','Bee','BuildInstructions','BuildPlayerData','BuildProfiles','BurstCache','PackageCache','PackageManager','PlayerDataCache','ScriptAssemblies','ScriptMapper','Search','ShaderCache','ShaderCache.db','SourceAssetDB','SourceAssetDB-lock','SplashScreenCache','SpriteAtlasDatabase.asset','StateCache','TempArtifacts','com.unity.services.core'}
allowed_roots=[str(repo/'work')+'/', '/private/tmp/',os.path.realpath(os.environ['TMPDIR'])+'/']
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=repo).split(b'\0')
ps=subprocess.check_output(['ps','-axo','pid,command'],text=True)
lsof=subprocess.run(['lsof','-nP','-Fpn'],capture_output=True,text=True).stdout
out=[{'path':'/private/tmp/style-device-audit/DerivedData','status':'deleted','note':'Emergency first cleanup: 5.6 GiB allocated size, 4.7 GiB free immediately afterward.'}]
for r in rows:
 p=Path(r['path']); watch=str(p.parent if p.name=='Library' else p)
 if r['skip'] or watch in ps or watch in lsof:
  out.append(dict(r,status='kept',reason=r['skip'] or 'currently in use'));continue
 if not p.exists():continue
 if not any(os.path.realpath(p).startswith(a) for a in allowed_roots):raise RuntimeError('Outside allowed roots: '+str(p))
 targets=[p/n for n in sorted(cache_names) if (p/n).exists()] if p.name=='Library' else [p]
 if p.name!='Library' and p.name not in {'DerivedData','ModuleCache.noindex','swift-cache','swift-module-cache'}:raise RuntimeError('Unknown cache '+str(p))
 for t in targets:
  if t.is_symlink():continue
  try:rel=t.relative_to(repo).as_posix().encode()
  except ValueError:rel=None
  if rel and any(x==rel or x.startswith(rel+b'/') for x in tracked):raise RuntimeError('Tracked path '+str(t))
  rec={'path':str(t),'status':'deleting','time':time.time()}
  with open(report/'journal.jsonl','a') as f:f.write(json.dumps(rec)+'\n')
  try:
   if t.is_dir():shutil.rmtree(t)
   else:t.unlink()
   rec['status']='deleted'
  except OSError as e:rec['status']='error';rec['error']=str(e)
  out.append(rec)
  with open(report/'journal.jsonl','a') as f:f.write(json.dumps(rec)+'\n')
 print('CLEANED',p,flush=True)
json.dump(out,open(report/'results.json','w'),indent=2)
print(subprocess.check_output(['df','-h',str(repo)],text=True),flush=True)
