import sys; sys.path.insert(0,'.')
import itertools, time
import raster
from raster import *
from leglib import *
from edges import spans
VA=np.load('data/V_A40.npy')
dyn_verts=np.zeros(N,bool); dyn_verts[ZONE&(V0[:,2]<0.31)]=True
dyn_faces=[p for p in F if any(dyn_verts[i] for i in p)]
sta_faces=[p for p in F if not any(dyn_verts[i] for i in p)]
VIEWS6=['bald_front','bald_back','sheet_front','sheet_back','left','right']
static={v: raster.mask(VA,v,sta_faces) for v in VIEWS6}
W={'bald_front':2,'bald_back':2,'sheet_front':1,'sheet_back':1,'left':1.5,'right':1.5}
def rows_for(v,kind):
    mpp,sole,cx=cam(v)
    if kind=='foot':
        if v in('left','right'): return slice(int(sole-0.045/mpp),H_)          # toe tip / heel only (far foot contaminates z 0.05..0.15)
        return slice(int(sole-0.16/mpp),H_)
    if kind=='ankle':
        return slice(int(sole-0.30/mpp),int(sole-0.16/mpp))
def warp(V,alpha,heel,toe,leg,xp,yp=0.0):
    Vn=V.copy()
    for sel0,side in ((LEFT,1),(RIGHT,-1)):
        sel=sel0&(V[:,2]<0.30); P=V[sel]
        x=P[:,0]*side; y=P[:,1]; z=P[:,2]
        m=smoothstep(0.15,0.06,z); dy_leg=leg*smoothstep(0.28,0.17,z)
        t=np.clip((-0.03-y)/(0.209-0.03),0,1); S=t*t*(3-2*t); dy_foot=heel+(toe-heel)*S
        y2=y+(1-m)*dy_leg+m*dy_foot
        th=np.radians(alpha)*smoothstep(0.15,0.07,z)
        dx=x-xp; dyy=y2-yp
        x3=xp+dx*np.cos(th)-dyy*np.sin(th); y3=yp+dx*np.sin(th)+dyy*np.cos(th)
        Vn[sel]=np.stack([x3*side,y3,z],1)
    return Vn
def cost(params,detail=False):
    alpha,heel,toe,leg,xp=params
    V=warp(VA,alpha,heel,toe,leg,xp)
    tot=0; det={}
    for v in VIEWS6:
        m=static[v]|raster.mask(V,v,dyn_faces); t=target_mask(v)
        for kind in ('foot','ankle'):
            r=rows_for(v,kind)
            if v in ('left','right') and kind=='foot': pass
            d=(m[r]!=t[r]).sum()
            # profile views: ignore the far foot (rows z in .045..0.16) already excluded; ankle rows z .16..0.30 fine
            tot+=W[v]*d/1000.0*(1.0 if kind=='foot' else 0.6)
            det[(v,kind)]=d
    return (tot,det) if detail else tot
if __name__=='__main__':
    p0=[0.0,0.0,0.0,0.0,0.185]
    print('A40 baseline cost',cost(p0))
    best=None
    t0=time.time()
    # coarse grid
    for alpha in (0,3,5,7,9,11):
        for heel in (0.0,0.01,0.02):
            for toe in (0.0,-0.01,-0.02):
                c=cost([alpha,heel,toe,0.02,0.185])
                if best is None or c<best[0]: best=(c,[alpha,heel,toe,0.02,0.185])
    print('coarse best',best,'time %.0fs'%(time.time()-t0))
    # coordinate refinement
    p=list(best[1]); c=best[0]
    steps=[1.0,0.004,0.004,0.004,0.008]
    for rnd in range(4):
        for i in range(5):
            for s in (steps[i],-steps[i]):
                q=list(p); q[i]+=s
                cq=cost(q)
                if cq<c: c=cq; p=q
        steps=[s/2 for s in steps]
    print('refined',c,p)
    c,det=cost(p,True)
    for k,vv in det.items(): print(k,vv)
    np.save('data/foot_params.npy',np.array(p))
