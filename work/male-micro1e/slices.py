import numpy as np,sys
sys.path.insert(0,'.')
from wire import write_png
def slice_pts(co,tri,z):
    """Return list of segments (p,q) where triangle edges cross plane z."""
    t=co[tri]; zz=t[:,:,2]-z
    segs=[]
    for i,j in ((0,1),(1,2),(2,0)):
        a=t[:,i];b=t[:,j];za=zz[:,i];zb=zz[:,j]
        m=(za*zb<0)
        u=(za[m]/(za[m]-zb[m]))[:,None]
        segs.append(a[m]+u*(b[m]-a[m]))
    return np.concatenate(segs)
def draw_slices(co,tri,zs,bounds,size,path,colors=None,xy=(0,1),extra=None):
    umin,umax,vmin,vmax=bounds; s=size/max(umax-umin,vmax-vmin)
    W=int((umax-umin)*s);H=int((vmax-vmin)*s); img=np.full((H,W,3),30,np.uint8)
    for k in range(0,W,int(0.01*s)): img[:,k]=(48,48,48)
    for k in range(0,H,int(0.01*s)): img[k,:]=(48,48,48)
    pal=[(255,90,90),(255,170,60),(240,240,80),(110,230,110),(80,200,255),(150,120,255),(255,120,220),(200,200,200)]
    for n,z in enumerate(zs):
        P=slice_pts(co,tri,z)
        x=((P[:,xy[0]]-umin)*s).astype(int); y=((vmax-P[:,xy[1]])*s).astype(int)
        ok=(x>=0)&(x<W)&(y>=0)&(y<H)
        c=(colors[n] if colors else pal[n%len(pal)])
        for dx in (0,1):
            for dy in (0,1):
                xx=np.clip(x+dx,0,W-1);yy=np.clip(y+dy,0,H-1); img[yy[ok],xx[ok]]=c
    write_png(path,img)
if __name__=='__main__':
    d=np.load('baseline/mesh.npz'); co=d['co']; tri=d['tri']
    zs=[1.455,1.47,1.485,1.50,1.515,1.53,1.545]
    draw_slices(co,tri,zs,(-0.13,0.13,-0.20,0.10),900,'r/slices_lower_face.png')
    print('slices drawn',zs)
