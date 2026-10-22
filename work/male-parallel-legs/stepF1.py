import sys; sys.path.insert(0,'.')
from leglib import *
VA=np.load('data/V_A40.npy')
z=VA[:,2]
wf=np.where(ZONE,1.0,0.0)*smoothstep(0.17,0.11,z)       # foot region weight (1 below z=0.11, 0 above 0.17)
for it in (15,40,100):
    S=taubin(VA,wf,iters=it)
    d=S-VA; print(it,'max move mm',np.linalg.norm(d,axis=1).max()*1000,'rms',np.sqrt((np.linalg.norm(d,axis=1)[wf>0]**2).mean())*1000, 'min z',S[:,2].min())
    np.save(f'data/V_F1_{it}.npy',S)
