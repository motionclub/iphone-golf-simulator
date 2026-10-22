import sys, numpy as np
sys.path.insert(0,'../male-micro1e')
import hand_sdf as H, run
V0=run.V0.astype(float); C=np.load('data/final_cur.npy').astype(float)
zR=run.ZR
for lo,hi in [(-0.20,-0.18),(-0.15,-0.13),(-0.12,-0.10),(-0.10,-0.085),(-0.085,-0.07),(-0.07,-0.055),(-0.055,-0.04),(-0.04,-0.02),(-0.02,0.0)]:
    for nm,V in (('base',V0),('final',C)):
        L=H.to_local(V,+1); m=zR&(L[:,2]>=lo)&(L[:,2]<hi)
        # area of the section: use convex-ish polygon via angular sort around centroid
        P=L[m][:,:2]; c=P.mean(0); ang=np.arctan2(P[:,1]-c[1],P[:,0]-c[0]); o=np.argsort(ang); Q=P[o]
        area=0.5*abs(np.sum(Q[:,0]*np.roll(Q[:,1],-1)-np.roll(Q[:,0],-1)*Q[:,1]))
        print(f'w[{lo:+.3f},{hi:+.3f}) {nm:5s} n={m.sum():3d} a-extent {1000*(P[:,0].max()-P[:,0].min()):.1f} n-extent {1000*(P[:,1].max()-P[:,1].min()):.1f} mm  area {area*1e4:.2f} cm2')
