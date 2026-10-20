import json,sys,itertools
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];R=W.parents[1]
sys.path.insert(0,str(R/'work/match-anim-set/scripts'));sys.path.insert(0,str(W/'scripts'))
import kin,motions
from golf_solver import GolfSolver
src=R/'work/match-anim-set/data';tag='male';k=kin.Rig(str(src/f'rig_{tag}.json'))
s=GolfSolver(k,json.load(open(src/f'racket_{tag}.json')),json.load(open(src/f'hands_{tag}.json')))
for name in ['AddressDriver','AddressIron','AddressWedge','AddressPutt']:
 d=motions.definition(name);best=[]
 for hip,chest,drop,forward,ballF in itertools.product([20,26,30],[14,20,26],[-.02,-.04,-.07],[.45,.52,.6],[.70,.75,.8]):
  p=motions.controls(d,0,s.scale);shaft=kin.unit([.035,forward,-1]);p['orientation']=motions.frame(shaft,[-1,0,0]);ball=d['ball'].copy();ball[1]=ballF;p['handle']=(ball-shaft*d['length'])*s.scale;p['pel_rot']=[0,hip,0];p['chest_rot']=[0,chest,0];p['pel_drop']=drop
  _,_,info=s.evaluate(p,'RH',d['length'],name=='AddressPutt')
  best.append((info['handle_projection_m'],abs(hip-20)+abs(chest-20)+abs(drop)*100+abs(ballF-.80)*30,hip,chest,drop,forward,ballF))
 valid=[x for x in best if x[0]<.0002]
 print(name,sorted(valid,key=lambda x:x[1])[:5] if valid else sorted(best)[:5],flush=True)
