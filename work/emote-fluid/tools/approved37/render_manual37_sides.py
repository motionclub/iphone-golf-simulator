from pathlib import Path
import subprocess, os
C=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/read-artdir-hero-base-lock-parallel')
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
for hero, female in [('male','0'),('female','1')]:
 env=os.environ.copy();env.update(FLUID_WAIT_XCODE='0')
 subprocess.run([str(R/'work/emote-fluid/tools/unity_run.sh'),'GolfArcade.EditorTools.EmoteFilm.Run',str(C/f'work/manual37_side_{hero}.log'),'EF_REVIEW=1','EF_VIEW=side','EF_CLIPS=Emote_Scuba,Emote_Thrust',f'EF_FEMALE={female}',f'EF_OUT={C}/work/manual37_side_frames/{hero}'],cwd=R,env=env,check=True)
 env['EF_VIEW']='side'
 subprocess.run(['python3',str(C/'work/encode_manual37.py'),hero,'Emote_Scuba','Emote_Thrust'],cwd=C,env=env,check=True)
 print('Review movies ready:',hero,flush=True)
