import sys,numpy as np,json
p='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0,p+'/work/emote-overhaul/scripts')
import emo_clips2 as E
for tag in ['male','female']:
 H=E.EH.EmoHero(tag);C=E.Thrust2(H)
 print(tag,'k',C.k,'arm',H.A)
 for t in [.45,.6]:
  P=C.P(t);i=H.solve(P)[2]
  print('pose',t,{n:np.round(C.A(i['Pos'][H.rig.idx[n]]),3).tolist() for n in ['Hips','UpperChest','LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm','LeftHand','RightHand']})
