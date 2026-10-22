from pathlib import Path
import subprocess, os
C=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/read-artdir-hero-base-lock-parallel')
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
for hero, female in [('male','0'),('female','1')]:
 env=os.environ.copy();env['FLUID_WAIT_XCODE']='0'
 subprocess.run([str(R/'work/emote-fluid/tools/unity_run.sh'),'GolfArcade.EditorTools.EmoteFilm.Run',str(C/f'work/manual37_game_{hero}.log'),'EF_REVIEW=1','EF_VIEW=game',f'EF_FEMALE={female}',f'EF_OUT={C}/work/manual37_game_frames/{hero}'],cwd=R,env=env,check=True)
 print('Game-camera capture ready:',hero,flush=True)
