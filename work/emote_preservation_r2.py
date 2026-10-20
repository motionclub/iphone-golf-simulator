import sys,ast,numpy as np
from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');sys.path.insert(0,str(r/'work/emote-overhaul/scripts'))
import emo_clips2 as E
old=ast.parse((r/'work/emote-overhaul/rollback_r2/source/emo_clips2.py').read_text())
ns=dict(vars(E))
for node in old.body:
 if isinstance(node,ast.ClassDef) and node.name in ['Scuba2','Thrust2']:
  node.name='Old'+node.name;exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'baseline','exec'),ns)
for tag in ['male','female']:
 H=E.EH.EmoHero(tag)
 for cname in ['Scuba2','Thrust2']:
  C=getattr(E,cname)(H);B=ns['Old'+cname](H)
  samples=[.2,.6,1.,1.7,2.8,3.,4.05,4.7] if cname=='Scuba2' else [0.,.45,.6,1.1667,1.7,2.8,3.,3.5]
  bodyworst=0.;strutworst=0.
  for t in samples:
   pn=C.P(t);po=B.P(t)
   ni=H.solve(pn)[2];oi=H.solve(po)[2]
   for n in ['Root','Hips','Spine','Chest','UpperChest','Neck','Head','LeftUpperLeg','LeftLowerLeg','LeftFoot','LeftToes','RightUpperLeg','RightLowerLeg','RightFoot','RightToes']:
    qn=ni['Q'][H.rig.idx[n]];qo=oi['Q'][H.rig.idx[n]];bodyworst=max(bodyworst,float(np.max(np.abs(qn-qo))))
   if cname=='Thrust2' and 2.8<=t<=3.0:
    for n in ['LeftShoulder','LeftUpperArm','LeftLowerArm','LeftHand','RightShoulder','RightUpperArm','RightLowerArm','RightHand']:
     strutworst=max(strutworst,float(np.max(np.abs(ni['Q'][H.rig.idx[n]]-oi['Q'][H.rig.idx[n]]))))
  print(tag,cname,'body_rotation_max_absolute_difference',bodyworst,'strut_arm_max_absolute_difference',strutworst,flush=True)
