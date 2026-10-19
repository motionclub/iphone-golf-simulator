import os,json,subprocess,shutil,time
from pathlib import Path
report=Path(__file__).resolve().parent
roots=[Path(os.environ['TMPDIR'])/x for x in ['acc-native-current/dd','acc-native-baseline/dd','cv2-xc2/dd']]+[Path('/private/tmp/tennis-calibration-build'),Path.cwd()/'work/tennis-chase-camera/native-derived']
default=Path('/Users/adnanyonathan/Library/Developer/Xcode/DerivedData')
roots += [p for p in default.iterdir() if p.name.startswith(('GolfArcade-','GolfArcadeUnity-')) and (p/'info.plist').is_file()]
ps=subprocess.check_output(['ps','-axo','pid,command'],text=True)
opened=subprocess.run(['lsof','-nP','-Fpn'],capture_output=True,text=True).stdout
tracked=subprocess.check_output(['git','ls-files','-z']).split(b'\0')
result=[]
for root in roots:
 if str(root) in ps or str(root) in opened:
  result.append({'path':str(root),'status':'kept','reason':'active process/open file'});continue
 for name in ['Build','Index.noindex','ModuleCache.noindex','SDKStatCaches.noindex','SDKExplicitPrecompiledModules','CompilationCache.noindex']:
  p=root/name
  if not p.exists() or p.is_symlink():continue
  try:rel=p.relative_to(Path.cwd()).as_posix().encode()
  except ValueError:rel=None
  assert not rel or not any(t==rel or t.startswith(rel+b'/') for t in tracked),str(p)
  record={'path':str(p),'status':'deleting','time':time.time()}
  with open(report/'journal.jsonl','a') as f:f.write(json.dumps(record)+'\n')
  try:shutil.rmtree(p);record['status']='deleted'
  except OSError as e:record.update(status='error',error=str(e))
  result.append(record)
  with open(report/'journal.jsonl','a') as f:f.write(json.dumps(record)+'\n')
json.dump(result,open(report/'native_results.json','w'),indent=2)
print('Deleted entries:',sum(r['status']=='deleted' for r in result),'Errors:',sum(r['status']=='error' for r in result),flush=True)
print(subprocess.check_output(['df','-h','.'],text=True))
