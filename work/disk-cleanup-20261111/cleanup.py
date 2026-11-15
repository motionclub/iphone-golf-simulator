"""Delete regenerable caches from idle (>=24 h, not open by any process) Unity copies and Xcode build roots listed in preflight.json."""
import os, json, shutil, subprocess, time, sys
from pathlib import Path
report=Path(__file__).resolve().parent
repo=report.parents[1]
rows=json.load(open(report/'preflight.json'))
unity_cache={'APIUpdater','Artifacts','ArtifactDB','ArtifactDB-lock','Bee','BuildInstructions','BuildPlayerData','BuildProfiles','BurstCache','PackageCache','PackageManager','PlayerDataCache','ScriptAssemblies','ScriptMapper','Search','ShaderCache','ShaderCache.db','SourceAssetDB','SourceAssetDB-lock','SplashScreenCache','StateCache','TempArtifacts','com.unity.services.core'}
xcode_cache=['Build','Index.noindex','ModuleCache.noindex','SDKStatCaches.noindex','SDKExplicitPrecompiledModules','CompilationCache.noindex']
keep_paths={str(repo/'Unity'),str(repo.parent/'pointer-menu/Unity'),str(Path.home()/'Setup Guide In-Editor Tutorial')}
tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=repo).split(b'\0'))
ps=subprocess.check_output(['ps','-axo','command'],text=True)
lsof=subprocess.run(['lsof','-nP','-Fn'],capture_output=True,text=True).stdout
out=[]
def df():return int(subprocess.check_output(['df','-k','/System/Volumes/Data']).split()[-6])//1024
before=df()
for r in rows:
    p=Path(r['path'])
    if str(p) in keep_paths or r['age_h']<24 or str(p) in ps or str(p) in lsof:
        out.append(dict(r,status='kept'));continue
    targets=[p/'Library'/n for n in sorted(unity_cache)] if r['kind']=='unity' else [p/n for n in xcode_cache]
    for t in targets:
        if not t.exists() or t.is_symlink():continue
        try:rel=t.relative_to(repo).as_posix().encode()
        except ValueError:rel=None
        if rel and any(x==rel or x.startswith(rel+b'/') for x in tracked):raise RuntimeError('tracked '+str(t))
        rec={'path':str(t),'time':time.time()}
        try:
            shutil.rmtree(t) if t.is_dir() else t.unlink();rec['status']='deleted'
        except OSError as e:rec.update(status='error',error=str(e))
        out.append(rec)
        with open(report/'journal.jsonl','a') as f:f.write(json.dumps(rec)+'\n')
    print('CLEANED',p,'free MB',df(),flush=True)
json.dump(out,open(report/'results.json','w'),indent=1)
print('free MB before',before,'after',df(),'deleted',sum(o.get('status')=='deleted' for o in out),'errors',sum(o.get('status')=='error' for o in out))
