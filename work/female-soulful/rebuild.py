"""Reproducible serial export/bake/fit pipeline for one female kit."""
from pathlib import Path
import os,sys,subprocess
root=Path(__file__).resolve().parent
blender='/Applications/Blender.app/Contents/MacOS/Blender'
golf=sys.argv[1]=='golf';hero='GolfKitHero_Female' if golf else 'MatchHero_Female';sport='golf' if golf else 'tennis'
steps=[('polo_export' if golf else 'export',root/'source'/f'{sport}_top.blend',[hero] if golf else [hero,'Kit_Top','tank2',str(root/'source/tennis_top_export.blend')]),
       ('export',root/'source'/f'{sport}_skirt.blend',[hero,'Kit_Bottom','skirt2',str(root/'source'/f'{sport}_skirt_export.blend')]),
       ('maps',None,[hero]),('cover',None,[hero]),('correctives',None,[hero,'40' if golf else '32']),('cover',None,[hero]),('poke',None,[hero])]
env=dict(os.environ,CV2_CORR_MODE='lift',CV2_PIECES=os.environ.get('CV2_PIECES','Kit_Top,Kit_Bottom'))
for i,(mode,blend,args) in enumerate(steps):
 if len(sys.argv)>2 and i<int(sys.argv[2]):continue
 if mode=='poke' and os.environ.get('CV2_SKIP_AUDIT')=='1':continue
 if i==3:
  # A rebuilt pattern has a new topology. Old pose deltas cannot be used by
  # the initial coverage pass; the next step regenerates them.
  (root/'out'/hero/'unity/correctives.npz').unlink(missing_ok=True)
 cmd=[blender,'-b',str(blend)] if blend else [blender,'-b','--factory-startup']
 if golf and mode=='correctives':cmd+=['--python',str(root/'wrap_correctives.py')]
 else:cmd+=['--python',str(root/'pipeline.py'),'--',mode,*args]
 log=root/'logs'/f'rebuilt-{sport}-{i}-{mode}.log'
 print(log.name,flush=True)
 with log.open('w') as out:subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,env=env,check=True)
 if 'Traceback' in log.read_text():raise RuntimeError(log)
print('Complete',hero,flush=True)
