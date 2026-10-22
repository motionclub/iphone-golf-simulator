from pathlib import Path
import subprocess,shutil
r=Path(__file__).resolve().parents[2];w=r/'work/phone-build-20261006';u=r/'Unity';held=[]
try:
 for name in ['NativeSessionTests','PlayerBaseTests','StandardCharacterGameplayTests']:
  for suffix in ['.cs','.cs.meta']:
   src=u/'Assets/Tests/PlayMode'/(name+suffix);dst=w/'held-tests'/(name+suffix)
   dst.parent.mkdir(parents=True,exist_ok=True)
   assert src.exists() and not dst.exists(),str(src)
   shutil.move(src,dst);held.append((src,dst))
 req=u/'Library/TennisReview.request'
 if req.exists() and req.read_text().strip()=='status':req.unlink()
 result=subprocess.run(['/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity','-batchmode','-quit','-projectPath',str(u),'-buildTarget','iOS','-job-worker-count','1','--burst-disable-compilation','-executeMethod','GolfArcade.EditorTools.BuildMenu.BuildIOS','-logFile',str(w/'unity-export.log')])
 print('Unity exit:',result.returncode,flush=True)
finally:
 for src,dst in held:shutil.move(dst,src)
 print('Restored all held test files',flush=True)
