import numpy as np
V=np.load('data/V_start.npy')
# right arm (x>0): cross sections by planes perpendicular to the arm axis
sh=np.array([0.20,-0.04,1.32]); 
# estimate axis by medial-axis of vertices x>0.28 : use PCA on x>0.30 & z<1.30 & z>0.9 verts
m=(V[:,0]>0.30)&(V[:,2]>0.90)&(V[:,2]<1.30)
P=V[m]; c=P.mean(0); u,s,vt=np.linalg.svd(P-c); ax=vt[0]; ax*= (1 if ax[0]>0 else -1)
print('axis',ax,'center',c)
# sections every 2 cm along the axis
t=(V-c)@ax
for tt in np.arange(-0.30,0.40,0.03):
    sel=(np.abs(t-tt)<0.006)&(V[:,0]>0.12)&(V[:,2]<1.45)&(V[:,2]>0.7)
    if sel.sum()<8: continue
    Q=V[sel]-c-np.outer(t[sel],ax)
    # in-plane basis: e1 = z-projected perpendicular (up), e2 = ax x e1 (depth ~ y)
    e1=np.array([0,0,1.0]); e1=e1-e1.dot(ax)*ax; e1/=np.linalg.norm(e1); e2=np.cross(ax,e1)
    a=Q@e1; b=Q@e2
    print(f't={tt:+.2f} n={sel.sum():3d} pos=({(c+tt*ax)[0]:.3f},{(c+tt*ax)[1]:.3f},{(c+tt*ax)[2]:.3f}) in-plane(up) {1000*(a.max()-a.min()):.0f}mm  depth {1000*(b.max()-b.min()):.0f}mm')
