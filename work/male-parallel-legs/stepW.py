"""Step W: foot/ankle warp (heel back, toe forward, ankle back, toe-out).  python stepW.py <in.npy> <out.npy> [alpha_deg]"""
import sys; sys.path.insert(0,'.')
from leglib import *
inp=sys.argv[1]; outp=sys.argv[2]; alpha=float(sys.argv[3]) if len(sys.argv)>3 else 11.0
V=np.load(inp)
P=dict(heel=0.0205, toe=-0.0205, leg=0.020, xp=0.185, yp=0.0)
def warp(Pm, side):
    x=Pm[:,0]*side; y=Pm[:,1].copy(); z=Pm[:,2]
    m=smoothstep(0.15,0.06,z)
    dy_leg=P['leg']*smoothstep(0.28,0.17,z)
    t=np.clip((-0.03-y)/(0.209-0.03),0,1); S=t*t*(3-2*t)
    dy_foot=P['heel']+(P['toe']-P['heel'])*S
    y2=y+(1-m)*dy_leg+m*dy_foot
    th=np.radians(alpha)*smoothstep(0.15,0.07,z)
    dx=x-P['xp']; dyy=y2-P['yp']
    x3=P['xp']+dx*np.cos(th)-dyy*np.sin(th)
    y3=P['yp']+dx*np.sin(th)+dyy*np.cos(th)
    out=np.stack([x3*side,y3,z],1); return out
Vn=V.copy()
for sel,side in ((LEFT,+1),(RIGHT,-1)):
    sel=sel&(V[:,2]<0.30)
    Vn[sel]=warp(V[sel],side)
# zone fade: nothing above z=0.30 moves anyway; assert
mv=np.linalg.norm(Vn-V,axis=1); print('moved verts',(mv>0).sum(),'max mm',mv.max()*1000,'max z moved',V[mv>0,2].max())
print('foot y extents L:',Vn[LEFT&(V[:,2]<0.04)][:,1].min(),Vn[LEFT&(V[:,2]<0.04)][:,1].max(),' x',Vn[LEFT&(V[:,2]<0.04)][:,0].min(),Vn[LEFT&(V[:,2]<0.04)][:,0].max())
np.save(outp,Vn)
