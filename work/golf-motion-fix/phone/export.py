from pathlib import Path
import subprocess,time,json
root=Path.cwd();out=root/'work/golf-motion-fix/phone'; moved=[]
before=set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
(out/'prebuild-status.txt').write_text(subprocess.check_output(['git','status','--short'],text=True))
try:
 for name in ['NativeSessionTests.cs','PlayerBaseTests.cs','StandardCharacterGameplayTests.cs']:
  for suffix in ['', '.meta']:
   p=root/'Unity/Assets/Tests/PlayMode'/(name+suffix); dest=out/(name+suffix+'.saved')
   if p.exists():
    assert not dest.exists(),str(dest)
    p.rename(dest);moved.append((p,dest))
 verdict=root/'Unity/Library/BuildResults/ios.txt'
 if verdict.exists():verdict.unlink()
 code=subprocess.call(['/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity','-batchmode','-quit','-projectPath',str(root/'Unity'),'-buildTarget','iOS','-executeMethod','GolfArcade.EditorTools.BuildMenu.BuildIOS','-logFile',str(out/'unity-export.log')])
 result=verdict.read_text() if verdict.exists() else 'Missing export result'
 (out/'unity-result.txt').write_text(result)
 print(result,flush=True)
 if code or not result.startswith('Succeeded'):raise SystemExit(code or 1)
finally:
 for p,dest in moved:
  if dest.exists():dest.rename(p)
 changed=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines()
 restored=[]
 for f in changed:
  if f not in before and (f.endswith(('.meta','.mat')) or f=='Unity/ProjectSettings/GraphicsSettings.asset'):
   (root/f).write_bytes(subprocess.check_output(['git','show','HEAD:'+f]));restored.append(f)
 (out/'restored-import-metadata.json').write_text(json.dumps(restored,indent=2))
 print('Restored temporary legacy test isolation and incidental import metadata.',flush=True)
