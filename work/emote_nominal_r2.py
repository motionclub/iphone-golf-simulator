import sys,numpy as np
r='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0,r+'/work/emote-overhaul/scripts')
import emo_clips2 as E
for tag in ['male','female']:
 H=E.EH.EmoHero(tag)
 for cname in ['Emote_Scuba','Emote_Thrust']:
  C=E.build(cname,H);data=[]
  for f in range(int(C.length*30)+1):
   t=f/30;P=C.P(t);i=H.solve(P)[2];Rp=C.pelvis_R(i);ix=H.rig.idx
   if cname=='Emote_Scuba' and .55<=t<=3.4:
    Q=i['Q'][ix['RightHand']];pm=np.degrees(np.arccos(np.clip(Q[:,2]@(Rp@np.array([1,0,0])),-1,1)));up=np.degrees(np.arccos(np.clip(Q[2,0],-1,1)))
    data.append([pm,up,np.linalg.norm(i['R_wrist']-i['R_shoulder']),180-i['R_elbow_flex_deg']])
   if cname=='Emote_Thrust' and .45<=t<=1.95 and C.th(t)[0]<=.1:
    data.append([180-i['L_elbow_flex_deg'],180-i['R_elbow_flex_deg'],i['L_wrist'][2]-i['L_shoulder'][2],i['R_wrist'][2]-i['R_shoulder'][2]])
  a=np.array(data);print(tag,cname,'min',a.min(0),'max',a.max(0),flush=True)
