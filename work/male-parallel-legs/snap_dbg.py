import sys; sys.path.insert(0,'.')
from snap import *
V=np.load('data/V_K2.npy'); n=normals(V)
zone_idx=np.nonzero(ZONE&(DEG>0))[0]
for v in VIEWD:
    disp,w=view_delta(V,n,v,zone_idx,maxd_px=0.022/cam(v)[0])
    sel=w>0.5
    mm=np.linalg.norm(disp[sel],axis=1)*1000
    mpp=cam(v)[0]
    print(v,'silhouette verts',sel.sum(),'|disp| mean %.2f median %.2f p90 %.2f mm'%(mm.mean(),np.median(mm),np.percentile(mm,90)),' mean vec (mm):',np.round(disp[sel].mean(0)*1000,2))
    # per z band mean signed displacement along the outward normal projected
    z=V[zone_idx,2]
    for z0 in (0.05,0.2,0.4,0.6):
        s=sel&(z>z0)&(z<z0+0.15)
        if s.sum(): 
            nn=n[zone_idx][s]; 
            print('    z %.2f-%.2f n=%d  mean disp mm'%(z0,z0+0.15,s.sum()),np.round(disp[s].mean(0)*1000,2),' mean along +normal %.2f'%((disp[s]*nn).sum(1).mean()*1000))
