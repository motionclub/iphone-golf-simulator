"""Run the unchanged dressed-mesh collision detector for every candidate frame."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os,json
R=Path(__file__).resolve().parents[3];W=Path(os.environ.get('FLUID_WORK',str(R/'work/emote-fluid')))
CLIPS=['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
(W/'proof/collide').mkdir(parents=True,exist_ok=True)
def run(job):
 hero,clip=job;dest=W/'proof/collide'/f'{clip}_{hero}_c3.json';trace=W/'data/after'/f'trace_{hero}_{clip}.npz'
 if dest.exists():
  import numpy as np
  sha=json.loads(str(np.load(trace)['meta']))['sha256']
  if json.loads(dest.read_text()).get('fbx_sha256')==sha:return (hero,clip,'already measured')
 log=W/'logs'/f'collide_{hero}_{clip}.log';log.parent.mkdir(exist_ok=True)
 with log.open('w') as f:
  result=subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2',str(R/'work/hero-dressed/export'/f'HeroBase_{hero.title()}_Dressed.blend'),'--python',str(R/'work/emote-fluid/tools/collide_reimport.py'),'--',hero,clip,'every:1',str(dest)],cwd=R,env={**os.environ,'FLUID_WORK':str(W)},stdout=f,stderr=subprocess.STDOUT)
 if result.returncode or not dest.exists():raise RuntimeError(f'{hero}/{clip}: detector did not complete; {log}')
 data=json.loads(dest.read_text());bad=[dict(frame=x['frame'],part=part,mm=1000*x[part]['pen_skin']) for x in data['rows'] for part in ['L','R','racket'] if 1000*x[part]['pen_skin']>(20 if x['t']<=.25 or x['t']>=data['rows'][-1]['t']-.25 else 12)]
 return hero,clip,'FAIL' if bad else 'PASS',bad
with ThreadPoolExecutor(max_workers=2) as pool:
 heroes=os.environ.get('FLUID_COLLIDE_HEROES','male,female').split(',');clips=os.environ.get('FLUID_COLLIDE_CLIPS',','.join(CLIPS)).split(',')
 for result in pool.map(run,[(h,c) for h in heroes for c in clips]):print('MESH',json.dumps(result),flush=True)
