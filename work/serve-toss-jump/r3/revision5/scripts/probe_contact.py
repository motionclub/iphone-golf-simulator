import sys,json,copy,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import loco,kin,pose as PS,clipkit_dj as CK,serve_dj as SD
for tag in ['male','female']:
 h=loco.Hero(tag); S=h.S;S.ready.update(gaze=None,r_hint=[0,0,0],r_hint_w=0.,r_tw=0.,r_tw_w=0.);d=SD.serve(S,h);c=CK.Clip(d,S.ready);P=c.params(1.7)
 old=np.load(loco.REPO+'/work/serve-dip-jump/data/gen_serve_'+tag+'.npz');b=np.array([kin.quat_to_mat(q) for q in old['quats'][51]]);Q,pos=h.rig.fk(b,old['hips'][51]);T=S.T_hr if hasattr(S,'T_hr') else None
 rk=json.load(open(loco.MA+'/data/racket_'+tag+'.json'));T=np.array(rk['T_hand_to_racket']);R=Q[h.rig.idx['RightHand']]@T[:3,:3];o=pos[h.rig.idx['RightHand']]+Q[h.rig.idx['RightHand']]@T[:3,3];sw=o+R@S.head_center
 print(tag,'sweet',sw,'O',S.O,'arm',S.a_u+S.a_f)
 out=[]
 for fwd in np.linspace(-.2,.18,20):
  p=copy.deepcopy(P);p['pel'][1]=fwd;p['rk_sweet']=kin.w2a(sw-S.O);p['rk_mode']='anchor';p['r_pole_w']=np.array([0.,-1.,0.]);S.reset();b,hh,info=S.solve(p);_,po=h.rig.fk(b,hh);sh,el,wr=[po[h.rig.idx[n]] for n in ['RightUpperArm','RightLowerArm','RightHand']];a=sh-el;v=wr-el;deg=np.degrees(np.arccos(np.clip(a@v/np.linalg.norm(a)/np.linalg.norm(v),-1,1)));err=np.linalg.norm(info['sweet']-sw)
  out.append((round(float(fwd),3),round(float(deg),1),round(float(err*1000),2)))
 print('forward, elbow included, sweet error mm',out)
 for dist in [.93,1.05,1.12,1.18,1.24]:
  p=c.params(.7);p['l_hand']=SD.RS(S,-22,68,dist,'L');S.reset();b,hh,i=S.solve(p);print('release radius',dist,'elbow flex',i.get('L_elbow_flex_deg'),'short',i.get('L_arm_short'))
