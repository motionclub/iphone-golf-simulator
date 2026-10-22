import sys; sys.path.insert(0,'.')
from leglib import *
VW=np.load('data/V_W2.npy'); z=VW[:,2]
wf=np.where(ZONE,1.0,0.0)*smoothstep(0.17,0.11,z)
sole=(VW[:,2]<0.006)
for it in (150,300,600):
    S=VW.copy()
    for k in range(it):
        S+=0.5*wf[:,None]*umbrella(S); S+=-0.53*wf[:,None]*umbrella(S)
        S[sole&ZONE,2]=np.maximum(S[sole&ZONE,2],VW[sole&ZONE,2]*0+0.0025)   # keep soles on the ground plane
    d=np.linalg.norm(S-VW,axis=1)*1000
    print(it,'rms %.2f max %.2f mm; foot minz %.4f'%(np.sqrt((d[wf>0]**2).mean()),d.max(),S[ZONE,2].min()))
    np.save(f'data/V_F2_{it}.npy',S)
