"""FINAL torso fit (fit_torso_final.py) — plate side-contour depth remap + bust + gluteal cleft; fields evaluated on denoised positions.
Pipeline: extract.py -> zone.py -> fit_torso_final.py -> apply_coords_plain.py -> audit_zone.py -> final_metrics.py -> make_proofs.py
Torso fit v3 (fields evaluated on smoothed positions)
Torso fit v2: smooth weights, flattened (superelliptic) front, two-mound bust, graph-smoothed displacement.
Vertex order/topology untouched. Writes data/torso_v2.npy"""
import numpy as np, sys
sys.path.insert(0,'.')
from targets import curves
d=np.load('data/start.npz'); co0=d['co'].astype(np.float64); ed=d['edges']; zz=np.load('data/zone.npz')
T=zz['torso']; n=len(co0)
(fz,f1),(bz,b1)=curves()
def sstep(t): t=np.clip(t,0,1); return t*t*(3-2*t)
# ---------- weights (analytic, smooth)
def XBL(z): return np.where(z>=1.165,0.124,0.124+(1.165-z)*0.9)
def weights(co):
    z=co[:,2]; x=np.abs(co[:,0])
    wz=sstep((z-0.795)/0.085)*sstep((1.34-z)/0.09)
    warm=sstep((XBL(z)-x)/0.075)
    return np.where(T,wz*warm,0.0)
W=weights(co0)
# ---------- graph for smoothing
ea,eb=ed[:,0],ed[:,1]
deg=np.bincount(np.r_[ea,eb],minlength=n).astype(float)
def gsmooth(D,k=6,lam=0.5):
    D=D.copy(); zone=T
    for _ in range(k):
        s=np.zeros_like(D); np.add.at(s,ea,D[eb]); np.add.at(s,eb,D[ea])
        m=s/np.maximum(deg,1)
        D=np.where(zone,(1-lam)*D+lam*m,0.0)
    return D
def taubin_pos(P,iters=30,lam=0.5,mu=-0.53):
    P=P.copy()
    for it in range(iters):
        for k in (lam,mu):
            s=np.zeros_like(P); np.add.at(s,ea,P[eb]); np.add.at(s,eb,P[ea])
            m=s/np.maximum(deg,1)[:,None]
            P=P+k*(m-P)
    return P
PS=taubin_pos(co0)
Wf=weights(PS)
print('jitter |P-Ps| in zone (mm): mean %.2f p95 %.2f max %.2f'%tuple(np.r_[np.linalg.norm((co0-PS)[T],axis=1).mean()*1000,np.percentile(np.linalg.norm((co0-PS)[T],axis=1),95)*1000,np.linalg.norm((co0-PS)[T],axis=1).max()*1000]))
# ---------- section extents
ZG=np.arange(0.80,1.372,0.002)
TE=ed[T[ed[:,0]]&T[ed[:,1]]]
def section_extents(co,zg=ZG):
    za=co[TE[:,0],2]; zb=co[TE[:,1],2]; ya=co[TE[:,0],1]; yb=co[TE[:,1],1]
    fe=np.full(len(zg),np.nan); be=np.full(len(zg),np.nan)
    for i,z in enumerate(zg):
        m=(za-z)*(zb-z)<0
        if m.any():
            t=(z-za[m])/(zb[m]-za[m]); y=ya[m]+t*(yb[m]-ya[m]); fe[i]=y.min(); be[i]=y.max()
    return fe,be
def fillnan(a):
    a=a.copy(); bad=np.isnan(a); idx=np.where(~bad)[0]; a[bad]=np.interp(np.where(bad)[0],idx,a[idx]); return a
def gsm(a,sigma,step=0.002):
    k=np.arange(-int(4*sigma/step),int(4*sigma/step)+1)*step; ker=np.exp(-0.5*(k/sigma)**2); ker/=ker.sum()
    pad=len(k)//2; return np.convolve(np.pad(a,(pad,pad),mode='edge'),ker,mode='valid')
def smooth1(a,k=3):
    a=a.copy()
    for _ in range(k): a[1:-1]=0.25*a[:-2]+0.5*a[1:-1]+0.25*a[2:]
    return a
F0,B0=section_extents(PS); F0s=gsm(fillnan(F0),0.004); B0s=gsm(fillnan(B0),0.004)   # extents of the SAME smoothed surface used to evaluate t (consistent, no mismatch)
P=dict(pf=1.0,pb=1.0)   # flatten exponents
BUST=dict(z=1.190,rzu=0.088,rzd=0.046,x=0.057,rx=0.056,A=0.021)   # compact-support (1-r^2)^2 mounds: no tails toward the armpit
def g_front_back(t,pf,pb):
    t=np.clip(t,0,1)
    gf=0.5*(2*t)**pf
    gb=1-0.5*(2*(1-t))**pb
    return np.where(t<0.5,gf,gb)
def bust_term(co,t,A):
    z=co[:,2]; x=np.abs(co[:,0])
    ff=sstep((0.45-t)/0.30)
    rz=np.where(z>BUST['z'],BUST['rzu'],BUST['rzd'])
    r2=((x-BUST['x'])/BUST['rx'])**2+((z-BUST['z'])/rz)**2
    return -A*np.clip(1-r2,0,1)**2*ff
def taubin_y(y,iters=10,lam=0.5,mu=-0.53):
    y=y.copy()
    for it in range(iters):
        for f in (lam,mu):
            s=np.zeros_like(y); np.add.at(s,ea,y[eb]); np.add.at(s,eb,y[ea])
            m=s/np.maximum(deg,1)
            y=np.where(T,y+f*(m-y),y)
    return y
tri_=d['tri']
def vnormals(co):
    v0,v1,v2=co[tri_[:,0]],co[tri_[:,1]],co[tri_[:,2]]
    fn=np.cross(v1-v0,v2-v0)
    vn=np.zeros_like(co)
    for k in range(3): np.add.at(vn,tri_[:,k],fn)
    return vn/np.maximum(np.linalg.norm(vn,axis=1),1e-12)[:,None]
def fair_surface(co,sigma=0.014,zr=(0.70,1.46)):
    nrm=vnormals(co)
    data_idx=np.where((co[:,2]>zr[0])&(co[:,2]<zr[1])&(np.abs(co[:,0])<0.26))[0]
    tgt=np.where(T&(Wf>0))[0]
    ys=co[:,1].copy()
    P2=co[data_idx][:,[0,2]]; Y=co[data_idx,1]; side=np.sign(nrm[data_idx,1])
    for s in range(0,len(tgt),256):
        ids=tgt[s:s+256]
        d2=((co[ids][:,None,[0,2]]-P2[None,:,:])**2).sum(2)
        wgt=np.exp(-d2/(2*sigma**2))*(side[None,:]==np.sign(nrm[ids,1])[:,None])
        ys[ids]=(wgt*Y[None,:]).sum(1)/np.maximum(wgt.sum(1),1e-12)
    beta=np.clip((np.abs(nrm[:,1])-0.25)/0.5,0,1)
    beta=beta*beta*(3-2*beta)*np.clip(Wf/0.15,0,1)
    out=co.copy(); out[:,1]=np.where(T,co[:,1]+beta*(ys-co[:,1]),co[:,1])
    return out
TAUB=dict(on=False,iters=16,fair=False,denoise=True)
CLEFT=dict(sx=0.026,C=0.011)
def cleft_term(co,t):
    z=co[:,2]; x=np.abs(co[:,0])
    bf=sstep((t-0.55)/0.25)
    return -CLEFT['C']*sstep((0.95-z)/0.09)*np.exp(-(x/CLEFT['sx'])**2)*bf
def apply(fc,bc,A=BUST['A'],ksm=10):
    zv=PS[:,2]; yv=PS[:,1]
    F0v=np.interp(zv,ZG,F0s); B0v=np.interp(zv,ZG,B0s)
    F1=np.interp(zv,fz,f1)+np.interp(zv,ZG,fc); B1=np.interp(zv,bz,b1)+np.interp(zv,ZG,bc)
    t=(yv-F0v)/np.maximum(B0v-F0v,1e-6)
    # exponent for front flattening fades in/out with height so only chest+belly flatten
    pf=1.0+(P['pf']-1.0)*sstep((zv-0.84)/0.16)*sstep((1.32-zv)/0.12)
    pb=1.0+(P['pb']-1.0)*sstep((zv-0.96)/0.16)*sstep((1.34-zv)/0.10)   # flatten upper back, keep glute round
    pp=0.5*(pf+pb)
    tc=np.clip(t,1e-6,1-1e-6)
    gt=tc**pp/(tc**pp+(1-tc)**pp)        # smooth S-curve: flat front/back, identity-slope at lateral meridian (no kink)
    ynew=F1+gt*(B1-F1)
    D_remap=np.where(T,Wf*(ynew-yv),0.0)
    D_remap=gsmooth(D_remap,ksm)
    D_bust=np.where(T,Wf*(bust_term(PS,t,A)+cleft_term(PS,t)),0.0)
    co=co0.copy(); co[:,1]+=D_remap+D_bust
    if TAUB['on']:
        ys=taubin_y(co[:,1],TAUB['iters'])
        co[:,1]=np.where(T,co[:,1]+np.minimum(1.0,Wf/0.25)*(ys-co[:,1]),co[:,1])
    if TAUB.get('fair'): co=fair_surface(co)
    if TAUB.get('denoise'):
        Bw=np.where(T,np.clip(Wf/0.25,0,1),0.0); Bw=Bw*Bw*(3-2*Bw)
        co=co+Bw[:,None]*(PS-co0)
    return co
def run(iters=10,A=BUST['A'],verbose=True):
    fc=np.zeros(len(ZG)); bc=np.zeros(len(ZG))
    wz_g=sstep((ZG-0.795)/0.085)*sstep((1.34-ZG)/0.09)
    for it in range(iters):
        co=apply(fc,bc,A); fe,be=section_extents(co); fe=fillnan(fe); be=fillnan(be)
        rf=np.interp(ZG,fz,f1)-fe; rb=np.interp(ZG,bz,b1)-be
        sel=wz_g>0.9
        if verbose: print(f"iter {it}: front resid max {np.abs(rf[sel]).max()*1000:.1f} mm, back {np.abs(rb[sel]).max()*1000:.1f} mm")
        fc[sel]+=rf[sel]; bc[sel]+=rb[sel]; fc=gsm(fc,0.02); bc=gsm(bc,0.02)
    return apply(fc,bc,A),fc,bc
if __name__=='__main__':
    co,fc,bc=run()
    np.save('data/torso_final.npy',co)
    mv=np.abs(co-co0).max(1)>1e-9
    print("moved verts:",int(mv.sum()),"max |dy| mm:",np.abs(co-co0).max()*1000, "x,z moved?",np.abs(co-co0)[:,[0,2]].max())
