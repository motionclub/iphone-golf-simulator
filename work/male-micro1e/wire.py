"""Numpy wireframe plotter (no PIL): writes PNG via zlib."""
import numpy as np, zlib, struct
def write_png(path, img):
    h,w,_=img.shape
    raw=b''.join(b'\x00'+img[y].tobytes() for y in range(h))
    def chunk(t,d): 
        c=struct.pack('>I',len(d))+t+d; return c+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    open(path,'wb').write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))
def plot(co,edges,sel,ax,bounds,size=900,path='w.png',color=(230,230,230),pts=True,hi=None):
    """ax=(u,v) coordinate indices for horizontal, vertical; bounds=(umin,umax,vmin,vmax)."""
    umin,umax,vmin,vmax=bounds; s=size/max(umax-umin,vmax-vmin)
    W=int((umax-umin)*s); H=int((vmax-vmin)*s)
    img=np.full((H,W,3),30,np.uint8)
    m=sel[edges[:,0]]&sel[edges[:,1]]
    e=edges[m]
    a=co[e[:,0]][:,list(ax)]; b=co[e[:,1]][:,list(ax)]
    n=int(max(2,np.ceil(np.max(np.linalg.norm(b-a,axis=1))*s)))
    t=np.linspace(0,1,n)[None,:,None]
    p=a[:,None,:]*(1-t)+b[:,None,:]*t
    x=((p[...,0]-umin)*s).astype(int); y=((vmax-p[...,1])*s).astype(int)
    ok=(x>=0)&(x<W)&(y>=0)&(y<H)
    img[y[ok],x[ok]]=color
    if pts:
        q=co[sel][:,list(ax)]; x=((q[:,0]-umin)*s).astype(int); y=((vmax-q[:,1])*s).astype(int)
        ok=(x>=1)&(x<W-1)&(y>=1)&(y<H-1); 
        for dx in (-1,0,1):
            for dy in (-1,0,1): img[y[ok]+dy,x[ok]+dx]=(255,120,60)
    write_png(path,img)

def scatter(pts2,colors,bounds,size=900,path='s.png',r=2,grid=None):
    umin,umax,vmin,vmax=bounds; s=size/max(umax-umin,vmax-vmin)
    W=int((umax-umin)*s); H=int((vmax-vmin)*s)
    img=np.full((H,W,3),30,np.uint8)
    if grid:
        g=int(grid*s)
        for k in range(0,W,max(g,1)): img[:,k]=(55,55,55)
        for k in range(0,H,max(g,1)): img[k,:]=(55,55,55)
    x=((pts2[:,0]-umin)*s).astype(int); y=((vmax-pts2[:,1])*s).astype(int)
    for dx in range(-r,r+1):
        for dy in range(-r,r+1):
            ok=(x+dx>=0)&(x+dx<W)&(y+dy>=0)&(y+dy<H)
            img[(y+dy)[ok],(x+dx)[ok]]=np.asarray(colors)[ok]
    write_png(path,img)
