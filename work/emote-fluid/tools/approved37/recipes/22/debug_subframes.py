import sys,json,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import fbx_curves as FB,native_curves as NC
W=Path(__file__).resolve().parents[1]
for tag,clip,fr in [('Male','Intro_Pushups',65.5),('Male','Emote_Thrust',79.5)]:
 raw,v,models,ch=FB.read(W/'candidate/fbx'/f'{tag}_{clip}.fbx')
 for nm in ['Hips','Spine','Chest','Neck','Head','RightShoulder','RightUpperArm','RightLowerArm','RightHand']:
  print(clip,nm)
  for prop in ['Lcl Rotation','Lcl Translation']:
   for ax in 'XYZ':
    c=ch[nm,prop,ax];times=np.array(FB.data(c,b'KeyTime'))/NC.TIME*30;val=np.array(FB.data(c,b'KeyValueFloat'));i=np.searchsorted(times,fr)-1
    print(prop,ax,val[i-1:i+3], 'times',times[i-1:i+3],'eval',NC.evaluate(c,fr/30),'tan',NC.expand(c,b'KeyAttrDataFloat',4)[i])
