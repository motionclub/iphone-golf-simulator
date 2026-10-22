"""Rerun the exact per-clip recipes composing candidate 37. Writes candidates only.
FLUID_WORK must name an isolated output containing data/before and rollback/fbx.
python3 rerun_candidate.py both [clip names]
"""
from pathlib import Path
import os,sys,subprocess,json
HERE=Path(__file__).resolve().parent
CLIPS=['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
args=sys.argv[1:];heroes=['male','female'] if not args or args[0]=='both' else [args[0]]
clips=args[1:] or CLIPS
out=Path(os.environ['FLUID_WORK']).resolve();jobs=[]
for hero in heroes:
 for clip in clips:
  recipe=clip if clip in ['Emote_Spike','Emote_Thrust','Intro_BringIt'] else '23' if hero=='male' and clip=='Intro_Pushups' else '20' if hero=='female' and clip=='Intro_Pushups' else '13'
  script=HERE/'recipes'/recipe/'fluid_pass.py'
  print('RECIPE',hero,clip,recipe,flush=True)
  subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python',str(script),'--',hero,clip],check=True,env={**os.environ,'FLUID_WORK':str(out)})
  jobs.append(dict(hero=hero,clip=clip,recipe=recipe))
(out/'proof'/('rerun_'+('_'.join(heroes))+'.json')).write_text(json.dumps(jobs,indent=2))
