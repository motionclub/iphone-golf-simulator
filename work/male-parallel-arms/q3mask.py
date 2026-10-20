import numpy as np
from PIL import Image
P='../../ArtDir/hero/base_lock/'
im=np.array(Image.open(P+'male_multiangle_body.jpg').convert('RGB')).astype(float)
lum=im.mean(2)
panels={'q3FL':(30,370,340,680),'q3FR':(340,370,650,680),'q3BL':(650,370,960,680),'q3BR':(960,370,1270,680)}
def label(mask):
    # simple 8-connected largest component via iterative flood fill using numpy (small images)
    from collections import deque
    H,W=mask.shape; seen=np.zeros_like(mask,bool); best=None
    for y in range(H):
        for x in range(W):
            if mask[y,x] and not seen[y,x]:
                q=deque([(y,x)]); seen[y,x]=True; comp=[(y,x)]
                while q:
                    cy,cx=q.popleft()
                    for dy in (-1,0,1):
                        for dx in (-1,0,1):
                            ny,nx=cy+dy,cx+dx
                            if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not seen[ny,nx]:
                                seen[ny,nx]=True; q.append((ny,nx)); comp.append((ny,nx))
                if best is None or len(comp)>len(best): best=comp
    out=np.zeros_like(mask)
    for y,x in best: out[y,x]=True
    return out
res={}
for k,(x0,y0,x1,y1) in panels.items():
    l=lum[y0:y1,x0:x1]
    # background estimate: median of border columns per row
    bgrow=np.median(np.concatenate([l[:,:6],l[:,-6:]],1),1)[:,None]
    m=(l-bgrow)>14
    m[-12:,:]=False if False else m[-12:,:]
    m=label(m)
    # fill holes
    from PIL import ImageFilter
    mi=Image.fromarray((m*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    m=np.array(mi)>127
    full=np.zeros(lum.shape,bool); full[y0:y1,x0:x1]=m
    ys,xs=np.nonzero(full); print(k,'bbox',xs.min(),ys.min(),xs.max(),ys.max(),'area',full.sum())
    Image.fromarray((full*255).astype(np.uint8)).save(f'data/plate_{k}_mask.png')
