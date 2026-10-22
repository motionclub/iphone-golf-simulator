"""Run the reused emo_clear obstacle and violation pass on all actual candidate FBX traces.
This reports violations; a report does not certify an independent collide3 pass.
"""
import sys,json,hashlib,os
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];W=Path(os.environ.get('FLUID_WORK',str(R/'work/emote-fluid')))
sys.path[:0]=[str(R/'work/emote-overhaul/scripts'),str(R/'work/emotes/scripts'),str(R/'work/match-anim-set/scripts'),str(Path(__file__).parent)]
import emo_hero as EH
from emo_clear import Clearance
from fluid_spec import CLIPS
for tag in ['male','female']:
 H=EH.EmoHero(tag);C=Clearance(H);ix=H.rig.idx
 for clip in CLIPS:
  z=np.load(W/'data/after'/f'trace_{tag}_{clip}.npz');rows=[]
  for f,M in enumerate(z['M']):
   attached=not (clip=='Emote_Scuba' and 6<=f<123 or clip=='Intro_Pushups' and 13<=f<73);info=dict(Pos=M[:,:3,3],Q=M[:,:3,:3],rk_origin=z['RC'][f,:3,3],rk_R=z['RC'][f,:3,:3],R_chest=M[ix['Chest'],:3,:3]);row=dict(frame=f,t=f/30)
   for side in 'LR':
    ignore=clip=='Emote_Scuba' and side=='L' and 16<=f<=104;pts,kind=C.arm_samples(info,side,side=='R' and attached);trees=C.obstacles(info,side,ignore,attached);viol,norm=C.violations(pts,kind,trees);row[side]=dict(max_violation_mm=float(max(0,viol.max())*1000),sample_count=len(viol),violating_samples=int(np.sum(viol>0)))
   rows.append(row)
  meta=json.loads(str(z['meta']));out=dict(hero=tag,clip=clip,fbx_sha256=meta['sha256'],method='Existing emo_clear.Clearance obstacle/sample/violation implementation; signed-distance report, not collide3 certification',rows=rows)
  (W/'proof'/f'clear_{tag}_{clip}.json').write_text(json.dumps(out,indent=2));print('EMO_CLEAR',tag,clip,'max_mm',max(x[s]['max_violation_mm'] for x in rows for s in 'LR'),flush=True)
