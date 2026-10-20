import sys,json,numpy as np
from pathlib import Path
W=Path(__file__).resolve().parents[1];R=W.parents[1];sys.path.insert(0,str(R/'work/match-anim-set/scripts'));sys.path.insert(0,str(W/'scripts'));import kin,motions
from golf_solver import GolfSolver
for sex in ['Male','Female']:
 k=kin.Rig(str(R/f'work/match-anim-set/data/rig_{sex.lower()}.json'));s=GolfSolver(k,json.load(open(R/f'work/match-anim-set/data/racket_{sex.lower()}.json')),json.load(open(R/f'work/match-anim-set/data/hands_{sex.lower()}.json')))
 for drop in [-.48,-.5]:
  for fwd in [.32,.4]:
   s.reset();p=motions.controls(motions.definition('BallPickup'),1.15,s.scale);p['pel_drop']=drop;p['free_hand']=np.array([.10,fwd,.18 if sex=='Male' else .16])*s.scale;p['handle']=np.array([-.3,.10,.665])*s.scale;p['orientation']=motions.frame([-.75,0,-.66],[-1,0,0])
   B,loc,d=s.evaluate(p,'RH',.96);Q,P=k.fk(B,loc);print(sex,drop,fwd,'hand',np.round(P[k.idx['RightHand']],3),'tip',np.round(P[k.idx['RightMiddleDistal']],3),'contact',np.round(d['club_contact'],3))
