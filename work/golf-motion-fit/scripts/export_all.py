from pathlib import Path
import subprocess
W=Path(__file__).resolve().parents[1];R=W.parents[1]
for sex in ['Male','Female']:
 for script in ['export_fbx','export_native']:
  log=W/f'logs/{script}_{sex}.log';print('RUN',script,sex,flush=True)
  with log.open('w') as out:p=subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b',str(W/f'export/Golf_{sex}_Dressed.blend'),'-t','2','--python',str(W/'scripts'/(script+'.py')),'--',sex],stdout=out,stderr=subprocess.STDOUT,cwd=R)
  txt=log.read_text()
  if p.returncode or 'Traceback' in txt:raise RuntimeError(txt[-2000:])
  print('DONE',script,sex,flush=True)
print('EXPORT_ALL_COMPLETE',flush=True)
