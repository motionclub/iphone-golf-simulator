"""Smooth-shaded orthographic preview (z-buffer, interpolated original normals): LOD0 | LOD1 | LOD2 | 4x diff(LOD0,LOD1),
front and side, for a dumped mesh (test/<name>.bin + .l1/.l2 from LodHarness). numpy + PIL only."""
import sys, struct, numpy as np
from PIL import Image, ImageDraw
def load(path):
    f=open(path,'rb'); nv,ns=struct.unpack('<ii',f.read(8))
    pos=np.frombuffer(f.read(nv*12),'<f4').reshape(nv,3).astype(np.float64); f.read(nv*32)
    nrm=np.frombuffer(f.read(nv*12),'<f4').reshape(nv,3).astype(np.float64); f.read(nv*8)
    subs=[]
    for _ in range(ns):
        c,=struct.unpack('<i',f.read(4)); subs.append(np.frombuffer(f.read(c*4),'<i4'))
    return pos,nrm,np.concatenate(subs).reshape(-1,3)
def lod(path):
    f=open(path,'rb'); ns,=struct.unpack('<i',f.read(4)); out=[]
    for _ in range(ns):
        c,=struct.unpack('<i',f.read(4)); out.append(np.frombuffer(f.read(c*4),'<i4'))
    return np.concatenate(out).reshape(-1,3)
def render(pos,nrm,tris,ax,size,lo,scale,light):
    x,y,z=ax; img=np.zeros((size,size)); zb=np.full((size,size),-1e9)
    P=np.stack([(pos[:,x]-lo[0])*scale,(size-1)-(pos[:,y]-lo[1])*scale,pos[:,z]],1)
    for t in tris:
        a,b,c=P[t]; xs=(a[0],b[0],c[0]); ys=(a[1],b[1],c[1])
        x0=max(int(np.floor(min(xs))),0); x1=min(int(np.ceil(max(xs))),size-1); y0=max(int(np.floor(min(ys))),0); y1=min(int(np.ceil(max(ys))),size-1)
        if x1<x0 or y1<y0: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(d)<1e-12: continue
        w0=((b[1]-c[1])*(gx-c[0])+(c[0]-b[0])*(gy-c[1]))/d; w1=((c[1]-a[1])*(gx-c[0])+(a[0]-c[0])*(gy-c[1]))/d; w2=1-w0-w1
        m=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
        if not m.any(): continue
        zz=w0*a[2]+w1*b[2]+w2*c[2]
        n=w0[...,None]*nrm[t[0]]+w1[...,None]*nrm[t[1]]+w2[...,None]*nrm[t[2]]
        n/=np.linalg.norm(n,axis=-1,keepdims=True)+1e-9
        sh=np.abs(n@light)*.8+.2
        sub=zb[y0:y1+1,x0:x1+1]; upd=m&(zz>sub)
        sub[upd]=zz[upd]; img[y0:y1+1,x0:x1+1][upd]=sh[upd]
    return img
base=sys.argv[1]; out=sys.argv[2]; size=int(sys.argv[3]) if len(sys.argv)>3 else 520
pos,nrm,t0=load(base+'.bin'); t1=lod(base+'.l1'); t2=lod(base+'.l2')
ext=pos.max(0)-pos.min(0); up=int(np.argmax(ext)); depth=int(np.argmin(ext)); side=3-up-depth
rows=[]
for ax in [(side,up,depth),(depth,up,side)]:
    lo=(pos[:,ax[0]].min(),pos[:,ax[1]].min()); scale=(size-8)/max(ext[ax[0]],ext[ax[1]])
    L=np.zeros(3); L[ax[0]]=.35; L[ax[1]]=.45; L[ax[2]]=.82; L/=np.linalg.norm(L)
    ims=[render(pos,nrm,t,ax,size,lo,scale,L) for t in (t0,t1,t2)]
    diff=np.clip(np.abs(ims[0]-ims[1])*4,0,1)
    rows.append(np.concatenate(ims+[diff],1))
im=Image.fromarray((np.concatenate(rows,0)*255).astype(np.uint8))
dr=ImageDraw.Draw(im)
for i,(nm,t) in enumerate([('LOD0',t0),('LOD1',t1),('LOD2',t2),('4x |LOD0-LOD1|',None)]):
    dr.text((i*size+6,4),f'{nm} {len(t) if t is not None else ""}',fill=255)
im.save(out); print(out)
