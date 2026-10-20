import sys; sys.path.insert(0,'.')
from leglib import *
VA=np.load('data/V_A40.npy')
print('isolated verts (DEG==0):',(DEG==0).sum(), ' in zone:',((DEG==0)&ZONE).sum())
for name,sel in (('L',LEFT),('R',RIGHT)):
    f=sel&(VA[:,2]<0.03)
    P=VA[f][:,:2]; c=P.mean(0); u,s,vt=np.linalg.svd(P-c,full_matrices=False)
    ax=vt[0]; ang=np.degrees(np.arctan2(ax[0],-ax[1])) if ax[1]<0 else np.degrees(np.arctan2(-ax[0],ax[1]))
    print(name,'sole footprint n=%d centre (%.3f,%.3f) principal axis %s toe-out angle %.1f deg (positive = toe turned +x)'%(f.sum(),c[0],c[1],np.round(ax,3),ang))
    # stations along axis (toe direction -y)
    ff=sel&(VA[:,2]<0.20)
    Pf=VA[ff]; 
    print(' foot z<0.2: x [%.3f,%.3f] y [%.3f,%.3f] z[%.4f,%.3f]'%(Pf[:,0].min(),Pf[:,0].max(),Pf[:,1].min(),Pf[:,1].max(),Pf[:,2].min(),Pf[:,2].max()))
    for y0 in np.arange(-0.20,0.08,0.03):
        s_=ff&(VA[:,1]>=y0)&(VA[:,1]<y0+0.03)
        if s_.sum(): print('   y %.2f..%.2f  n=%d  x[%.3f,%.3f] w=%.3f  z max %.3f'%(y0,y0+0.03,s_.sum(),VA[s_,0].min(),VA[s_,0].max(),VA[s_,0].max()-VA[s_,0].min(),VA[s_,2].max()))
