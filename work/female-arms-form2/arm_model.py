"""Female arms form pass: pure numpy. build(params) -> new_co (full array), uses data/start_cur.npz + data/zones_cur.npz.
Only arm-zone vertices move; vertices touching the non-arm mesh (torso/hand/wrist ring) are pinned (weight 0)."""
import numpy as np, json
D=np.load('data/start_cur.npz'); CO0=D['co'].astype(np.float64); ED=D['edges']; N=len(CO0)
ARM=np.load('data/zones_cur.npz')['arm']
nbr=[[] for _ in range(N)]
for a,b in ED: nbr[a].append(b); nbr[b].append(a)
idx=np.where(ARM)[0]
# pinned = arm verts with a non-arm neighbour
PIN=np.array([any(not ARM[j] for j in nbr[i]) for i in idx])
SIDE=np.sign(CO0[idx,0])
def sstep(t): t=np.clip(t,0,1); return t*t*(3-2*t)
def win(z,z0,w): t=np.clip((z-z0)/w,-1,1); return 0.5*(1+np.cos(np.pi*t))*(np.abs((z-z0)/w)<1)
def lobe(th,th0,k): return ((1+np.cos(th-th0))/2)**k
def interp(z,tbl): t=np.array(tbl); return np.interp(z,t[:,0],t[:,1])
def taubin(P,fixed,it=30,lam=0.5,mu=-0.53):
    P=P.copy(); loc={g:i for i,g in enumerate(idx)}
    for _ in range(it):
        for f in (lam,mu):
            Q=P.copy()
            for k,g in enumerate(idx):
                if fixed[k]: continue
                ns=[CO0[j] if j not in loc else P[loc[j]] for j in nbr[g]]
                Q[k]=P[k]+f*(np.mean(ns,0)-P[k])
            P=Q
    return P
# ---- cache denoised copy and pin distance
import os
if os.path.exists('data/arm_smooth.npz'):
    z=np.load('data/arm_smooth.npz'); PS=z['PS']; DPIN=z['DPIN']
else:
    PS=taubin(CO0[idx],PIN,30)
    pinp=CO0[idx[PIN]]
    DPIN=np.sqrt(((CO0[idx][:,None,:]-pinp[None,:,:])**2).sum(2)).min(1)
    np.savez('data/arm_smooth.npz',PS=PS,DPIN=DPIN)
C0=[(0.845,.231),(0.86,.228),(0.89,.223),(0.92,.219),(0.95,.2135),(0.98,.2065),(1.01,.1985),(1.04,.1925),(1.07,.187),(1.10,.182),(1.13,.1765),(1.16,.1685),(1.19,.167),(1.22,.165),(1.25,.162),(1.28,.158),(1.31,.155),(1.34,.150)]
DEF=dict(R_pin=0.08,R_ysh=0.15,smooth_it=8,R_fair=0.05,fair_it=0,
 xsh=[(0.845,0.0),(0.93,0.001),(1.0,0.004),(1.08,0.008),(1.2,0.008),(1.30,0.006),(1.4,0.006)],
 ysh=[(0.845,0.0),(0.88,0.0048),(0.95,0.0168),(1.05,0.0336),(1.15,0.0432),(1.30,0.048),(1.4,0.048)],
 mods=[ # name, z0, w, theta0, k, amp   (theta0 None -> all-round)
  ('deltoid_round',1.265,0.075,None,0,0.06),
  ('deltoid_fb',1.265,0.075,'fb',0,0.06),
  ('triceps',1.13,0.085,np.pi/2,1.5,0.07),
  ('biceps',1.14,0.085,-np.pi/2,1.5,0.04),
  ('elbow_neck',1.045,0.04,None,0,-0.06),
  ('olecranon',1.025,0.035,np.pi/2,3,0.08),
  ('forearm_belly',0.975,0.055,0.0,1.0,0.11),
  ('forearm_front',0.965,0.05,-np.pi/2,1.5,0.05),
 ])
def build(P=None):
    P=dict(DEF) if P is None else {**DEF,**P}
    ps=PS; s=SIDE; u=ps[:,0]*s; y=ps[:,1]; z=ps[:,2]
    c0=interp(z,C0); du=u-c0; dy=y
    th=np.arctan2(dy,du)
    g=np.ones(len(idx))
    for (nm,z0,w,t0,k,A) in P['mods']:
        W=win(z,z0,w)
        if t0 is None: L=1.0
        elif t0=='fb': L=np.sin(th)**2
        else: L=lobe(th,t0,k)
        g=g+A*W*L
    ysh=interp(z,P['ysh'])
    wp=sstep(DPIN/P['R_pin']); wy=sstep(DPIN/P['R_ysh'])
    wp=np.where(PIN,0,wp); wy=np.where(PIN,0,wy)
    du2=du*g; dy2=dy*g
    # target in smooth frame
    tu=c0+du2; ty=dy2+ysh
    xs=interp(z,P['xsh'])
    Dx=((tu-u)*wp-xs*wy)*s            # x displacement (xsh = inward axis shift)
    Dy=(dy2-dy)*wp+ysh*wy
    Dz=np.zeros(len(idx))
    Dm=np.stack([Dx,Dy,Dz],1)
    loc={g:i for i,g in enumerate(idx)}
    for _ in range(P['smooth_it']):
        Q=Dm.copy()
        for k,g in enumerate(idx):
            if PIN[k]: continue
            ns=[Dm[loc[j]] if j in loc else np.zeros(3) for j in nbr[g]]
            Q[k]=0.5*Dm[k]+0.5*np.mean(ns,0)
        Dm=Q
    new=CO0.copy()
    new[idx]+=Dm
    # armpit fairing: Laplacian relax of free arm verts around the apex (pins and all non-arm verts stay put)
    pz=idx[PIN]; pz=pz[CO0[pz,2]>1.0]
    ap=CO0[pz[np.argsort(CO0[pz,2])[:8]]]
    da=np.sqrt(((CO0[idx][:,None,:]-ap[None,:,:])**2).sum(2)).min(1)
    wf=1-sstep(da/P['R_fair'])
    wf=np.where(PIN,0,wf)
    for _ in range(P['fair_it']):
        Q=new[idx].copy()
        for k,g in enumerate(idx):
            if wf[k]<=0: continue
            ns=np.mean([new[j] for j in nbr[g]],0)
            Q[k]=new[g]+0.5*wf[k]*(ns-new[g])
        new[idx]=Q
    return new.astype(np.float32)
if __name__=='__main__':
    import sys
    new=build(); out=sys.argv[-1]
    np.save(out,new)
    d=np.abs(new-CO0).max(1); print('moved',(d>0).sum(),'max',d.max(),'outside arm',(d[~ARM]>0).sum(),'pinned moved',(d[idx[PIN]]>0).sum())
