import sys, os
CV=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../clothing-v2/py')); sys.path.insert(0,CV)
os.chdir(os.path.join(CV,'..'))
import numpy as np, cv2io, glib as G
from shoe2 import Frame, footprint, foot_top
for hid in ('MatchHero_Male','GolfKitHero_Male'):
    hero=cv2io.Hero(hid); body=G.Body(hero)
    for sd in ('R',):
        fr=Frame(body,sd); L=fr.L
        ys=np.linspace(0,L,21); xc,w=footprint(fr,ys); zt=foot_top(fr,ys,xc)
        print(hid, sd, 'L %.4f ankle %s origin %s'%(L, np.round(fr.ankle,3), np.round(fr.origin,3)))
        print(' y/L  ', ' '.join('%5.2f'%v for v in ys/L))
        print(' halfw', ' '.join('%5.3f'%v for v in w))
        print(' ftop ', ' '.join('%5.3f'%v for v in zt))
        q=fr.to(body.pos[(fr.wf+fr.wl)>.3])
        for z in (.06,.08,.10,.12,.14):
            m=np.abs(q[:,2]-z)<.005
            if m.sum(): print(' leg z=%.2f  y %.3f..%.3f  x %.3f..%.3f'%(z,q[m,1].min(),q[m,1].max(),q[m,0].min(),q[m,0].max()))
        # sock
        for k in hero.__dict__: pass
    print(' pieces', [k for k in getattr(hero,'kit',{}).keys()] if hasattr(hero,'kit') else dir(hero)[:40])
