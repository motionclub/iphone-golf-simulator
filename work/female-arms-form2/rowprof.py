import sys, numpy as np
from armmetrics import *
pre=sys.argv[1]
mm={v:np.array(Image.open(f'{pre}_{v}.png'))[:,:,3]>127 for v in('front','back')}
Mh=(half(mm['front'],440,-1).astype(float)+half(mm['front'],440,1).astype(float)+half(mm['back'],847,-1)+half(mm['back'],847,1))/4
def runs(r):
    d=np.diff(np.concatenate([[0],r.astype(int),[0]])); return list(zip(np.where(d==1)[0],np.where(d==-1)[0]))
print('row  z    | plate runs (dx px) | model runs')
for r in range(170,350,10):
    print(r, round((679-r)*S,3), [(a,b) for a,b in runs(T[r]>0.5)], [(a,b) for a,b in runs(Mh[r]>0.5)])
