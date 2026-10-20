"""Silhouette snapping of the leg zone to the six plate masks.
python snap.py <in.npy> <out.npy> [iters] [gain]"""
import sys; sys.path.insert(0,'.')
import numpy as np
import raster
from raster import *
from leglib import *
VIEWD={'bald_front':np.array([0,1.,0]),'sheet_front':np.array([0,1.,0]),'bald_back':np.array([0,-1.,0]),'sheet_back':np.array([0,-1.,0]),'left':np.array([-1.,0,0]),'right':np.array([1.,0,0])}
RIGHTV={'bald_front':np.array([1.,0,0]),'sheet_front':np.array([1.,0,0]),'bald_back':np.array([-1.,0,0]),'sheet_back':np.array([-1.,0,0]),'left':np.array([0,1.,0]),'right':np.array([0,-1.,0])}
VW={'bald_front':1.0,'bald_back':1.0,'sheet_front':0.5,'sheet_back':0.5,'left':0.8,'right':0.8}
_contours={}
def contour_pts(v):
    if v in _contours: return _contours[v]
    m=target_mask(v)
    # exact half-pixel contour: midpoints between an inside pixel centre and its outside 4-neighbour
    P=[]
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        nb=np.roll(np.roll(m,-dy,axis=0),-dx,axis=1)      # neighbour at (y+dy,x+dx)
        sel=m&~nb
        ys,xs=np.nonzero(sel)
        P.append(np.stack([xs+0.5*dx,ys+0.5*dy],1))      # PIL/raster convention: pixel centre = integer coordinate
    P=np.vstack(P); _contours[v]=P; return P
def sample_mask(m,px,py):
    xi=np.clip(np.floor(px).astype(int),0,m.shape[1]-1); yi=np.clip(np.floor(py).astype(int),0,m.shape[0]-1)
    return m[yi,xi]
def view_delta(V,n,v,idx,maxd_px,sigma=0.30):
    """3D displacement (m) for vertices idx from view v (returns (len(idx),3) and weights)"""
    mpp,sole,cx=cam(v)
    px,py=raster.project(V[idx],v)          # pixel coords (continuous, pixel i spans [i,i+1) in this convention + raster used raw coords -> consistent with +0.5 centre convention below)
    d=VIEWD[v]; nd=(n[idx]@d)
    w=np.exp(-(nd*nd)/(2*sigma*sigma))
    # contour points (restrict to rows relevant: all)
    C=contour_pts(v)
    inside=sample_mask(target_mask(v),px,py)
    # nearest contour point (chunked brute force on a pre-filtered set around the zone rows)
    best=np.zeros((len(idx),2)); bd=np.zeros(len(idx))
    for a in range(0,len(idx),400):
        sl=slice(a,a+400)
        dd=(px[sl,None]-C[None,:,0])**2+(py[sl,None]-C[None,:,1])**2
        j=dd.argmin(1); best[sl]=C[j]-np.stack([px[sl],py[sl]],1); bd[sl]=np.sqrt(dd[np.arange(dd.shape[0]),j])
    # in-image displacement (px) towards the contour
    ok=(bd<=maxd_px)
    w=w*ok
    # world displacement: image x -> right vector * h_sign..., image y -> -z
    R=RIGHTV[v]
    # px increases with  h_sign*u  -> world right vector R already includes the sign convention (u axis= +x/+y world; h_sign flips) : image right = R
    disp=(best[:,0:1]*R[None,:]+(-best[:,1:2])*np.array([0,0,1.])[None,:])*mpp
    return disp,w
def snap(V,iters=3,gain=0.7,maxmm=8.0):
    V=V.copy()
    zone_idx=np.nonzero(ZONE&(DEG>0))[0]
    fade=smoothstep(ZT,ZT-0.07,V0[zone_idx,2])          # 0 at the zone top
    for it in range(iters):
        n=normals(V)
        tot=np.zeros((len(zone_idx),3)); wt=np.zeros(len(zone_idx))
        for v in VIEWD:
            disp,w=view_delta(V,n,v,zone_idx,maxd_px=0.022/cam(v)[0])
            z=V[zone_idx,2]
            if v in('left','right'):
                w=w*(1-smoothstep(0.69,0.74,z))                 # hands/arms overlap the thighs in profile
                w=w*np.where((z>0.045)&(z<0.17),0.0,1.0)        # far foot contaminates the profile plates between 4.5 and 17 cm
            w=w*VW[v]
            tot+=disp*w[:,None]; wt+=w
        D=tot/(wt[:,None]+0.35)
        D=D*gain
        # clamp
        mag=np.linalg.norm(D,axis=1,keepdims=True); D=D*np.minimum(1.0,maxmm/1000/np.maximum(mag,1e-12))
        # smooth the displacement field over the surface (Laplacian), zone only
        Dfull=np.zeros_like(V); Dfull[zone_idx]=D*fade[:,None]
        wmask=np.zeros(N); wmask[zone_idx]=1.0
        for k in range(12):
            Dfull+=0.5*wmask[:,None]*umbrella(Dfull)
        V[zone_idx]+=Dfull[zone_idx]
        V[zone_idx[V[zone_idx,2]<Z0_MIN],2]=Z0_MIN
    return V
Z0_MIN=V0[:,2].min()
if __name__=='__main__':
    V=np.load(sys.argv[1]); out=sys.argv[2]
    it=int(sys.argv[3]) if len(sys.argv)>3 else 3; gain=float(sys.argv[4]) if len(sys.argv)>4 else 0.7
    r0=metrics(V); print('before:',fmt(r0))
    Vn=snap(V,it,gain)
    r1=metrics(Vn); print('after: ',fmt(r1))
    d=np.linalg.norm(Vn-V,axis=1)*1000; print('moved',(d>0).sum(),'rms %.2f max %.2f mm'%(np.sqrt((d[d>0]**2).mean()),d.max()))
    np.save(out,Vn)
