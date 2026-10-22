"""Full unchanged contact pipeline with FBX-bound provenance. No production install."""
from pathlib import Path
import os,sys,subprocess,json,hashlib
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W=Path(os.environ['FLUID_WORK']).resolve()
CLIPS=['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
import numpy as np
for hero in ['male','female']:
 for clip in CLIPS:
  meta=json.loads(str(np.load(W/'data/after'/f'trace_{hero}_{clip}.npz')['meta']));path=Path(meta['path']);assert meta['sha256']==hashlib.sha256(path.read_bytes()).hexdigest(),(hero,clip,'stale trace')
env={**os.environ,'FLUID_WORK':str(W),'FLUID_COLLIDE_HEROES':'male,female','FLUID_COLLIDE_CLIPS':','.join(CLIPS)}
blender='/Applications/Blender.app/Contents/MacOS/Blender'
steps=[('clear_all',[blender,'-b','-t','2','--python',str(R/'work/emote-fluid/tools/clear_reimport.py')]),('collide_all',[sys.executable,str(R/'work/emote-fluid/tools/collide_batch.py')]),('gates_96',[blender,'-b','-t','2','--python',str(R/'work/emote-fluid/tools/gates_existing.py')])]
for label,cmd in steps:
 print('START',label,flush=True)
 with (W/'logs'/f'{label}.log').open('w') as log:subprocess.run(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('DONE',label,flush=True)
a=json.loads((W/'proof/existing_96.json').read_text());bad=[(h,c,k,v) for h,cs in a.items() for c,gs in cs.items() for k,v in gs.items() if not v['ok']];total=sum(len(gs) for cs in a.values() for gs in cs.values());assert total==96
print('ORIGINAL_GATES',total-len(bad),'PASS',len(bad),'FAIL',flush=True)
(W/'proof/contact_pipeline.json').write_text(json.dumps({'revision':int(W.name),'passing':total-len(bad),'required':96,'failures':bad,'all_collision_reports_fbx_bound':all(gs['G7']['hash_matches'] for cs in a.values() for gs in cs.values())},indent=2)+'\n')
