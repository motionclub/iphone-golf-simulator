import sys; sys.path.insert(0,'.')
from leglib import *
import footsdf as S
VW=np.load(sys.argv[1] if len(sys.argv)>1 else 'data/V_W2.npy')
# data: both feet (mirror right onto left), z<0.115
fl=LEFT&(VW[:,2]<0.115); fr=RIGHT&(VW[:,2]<0.115)
Pl=VW[fl]; Pr=VW[fr].copy(); Pr[:,0]*=-1
P=np.vstack([Pl,Pr]); print('foot data',P.shape)
# initial parameters (left foot), after the W2 warp: foot y from -0.225 to 0.085, x ~0.15..0.28, center x 0.21
init=np.array([
 # heel : c(x,y,z) r(x,y,z) yaw pitch
 0.200,0.040,0.050, 0.046,0.050,0.052, 0.0,0.0,
 # mid
 0.200,-0.050,0.050, 0.055,0.085,0.052, 0.0,-0.20,
 # ball
 0.215,-0.140,0.034, 0.066,0.070,0.036, 0.0,0.0,
 # toe
 0.220,-0.190,0.024, 0.055,0.045,0.026, 0.0,0.0,
 # column cx cy rx ry
 0.185,0.005,0.048,0.062,
 0.050,0.012])
lo=init.copy(); hi=init.copy()
def setb(i,a,b): lo[i]=a; hi[i]=b
for e in range(4):
    o=e*8
    for j in (0,1): setb(o+j,init[o+j]-0.05,init[o+j]+0.05)
    setb(o+2,0.015,0.08)
    for j in (3,4,5): setb(o+j,0.02,0.11)
    setb(o+6,-0.5,0.5); setb(o+7,-0.6,0.6)
setb(32,0.15,0.23); setb(33,-0.03,0.04); setb(34,0.035,0.06); setb(35,0.04,0.075)
setb(36,0.045,0.065); setb(37,0.010,0.02)
def resid(p):
    f=S.sdf(P,p)
    return f
def fit(p,iters=60):
    lam=1e-2
    r=resid(p); c=(r*r).sum()
    for it in range(iters):
        J=np.zeros((len(r),len(p)))
        for j in range(len(p)):
            h=1e-4 if j<32 or j>=36 else 1e-4
            q=p.copy(); q[j]+=h; J[:,j]=(resid(q)-r)/h
        A=J.T@J+lam*np.diag(np.diag(J.T@J)+1e-9); b=J.T@r
        try: dp=-np.linalg.solve(A,b)
        except np.linalg.LinAlgError: lam*=10; continue
        q=np.clip(p+dp,lo,hi); rq=resid(q); cq=(rq*rq).sum()
        if cq<c: p,r,c=q,rq,cq; lam=max(lam/3,1e-7)
        else: lam*=4
        if it%10==0: print(it,'cost %.4e rms %.3f mm'%(c,np.sqrt(c/len(r))*1000),'lam %.1e'%lam)
    return p,r
p,r=fit(init,80)
print('final rms %.3f mm  max %.2f mm'%(np.sqrt((r*r).mean())*1000,np.abs(r).max()*1000))
np.save(sys.argv[2] if len(sys.argv)>2 else 'data/foot_sdf_params.npy',p)
E,col,k,kf=S.unpack(p)
for n,e in zip(S.ELL,E): print(n,np.round(e,3))
print('col',np.round(col,3),'k',k,'kf',kf)
