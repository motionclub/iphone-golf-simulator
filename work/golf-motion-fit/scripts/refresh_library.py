"""Repeatable, sequential refresh; fail on Blender's Python errors even at exit 0."""
from pathlib import Path
import subprocess
W=Path(__file__).resolve().parents[1];R=W.parents[1]
blender='/Applications/Blender.app/Contents/MacOS/Blender'
import sys
for sex in [x for x in sys.argv[1:] if not x.startswith('--')] or ['Male','Female']:
 if '--fit' not in sys.argv and '--garments' not in sys.argv and '--bake' not in sys.argv:
  for hand in ['RH','LH']:
   log=W/f'logs/fit_grip_{sex}_{hand}.log';print('RUN fit_grip',sex,hand,flush=True)
   with log.open('w') as out:run=subprocess.run([blender,'-b',str(W/f'export/Golf_{sex}_Dressed.blend'),'-t','2','--python',str(W/'scripts/fit_grip.py'),'--',sex,hand],cwd=R,stdout=out,stderr=subprocess.STDOUT)
   if run.returncode or 'Traceback' in log.read_text():raise RuntimeError(log.read_text()[-3000:])
 for script,source,marker in [('fit_grip',f'Golf_{sex}_Dressed.blend','GRIP '+sex+' L'),('build_library',f'Golf_{sex}_Dressed.blend','MASTER_COMPLETE '+sex),('build_garments',f'Golf_{sex}_Master.blend','GARMENTS_COMPLETE '+sex),('pack_maps',f'Golf_{sex}_Dressed.blend','UV_PACK_COMPLETE '+sex),('fit_polo',f'Golf_{sex}_Dressed.blend','POLO_FIT_COMPLETE '+sex),('install_correctives',f'Golf_{sex}_Dressed.blend','CORRECTIVES_COMPLETE '+sex)]:
  if script=='fit_grip':continue
  if '--fit' in sys.argv and script not in ['fit_polo','install_correctives']:continue
  if '--garments' in sys.argv and script in ['fit_grip','build_library']:continue
  print('RUN',script,sex,flush=True);log=W/f'logs/{script}_{sex}.log'
  with log.open('w') as out:run=subprocess.run([blender,'-b',str(W/'export'/source),'-t','2','--python',str(W/'scripts'/(script+'.py')),'--',sex],cwd=R,stdout=out,stderr=subprocess.STDOUT)
  text=log.read_text()
  if run.returncode or 'Traceback (most recent call last)' in text or marker not in text:raise RuntimeError(str(log)+'\n'+text[-3000:])
  print('DONE',script,sex,flush=True)
print('REFRESH_COMPLETE',flush=True)
