import sys, numpy as np, math
sys.path.insert(0,"../proof")
import measure as M
from PIL import Image

def zhang_suen(img):
    img=img.copy().astype(np.uint8)
    def step(img,first):
        P=np.pad(img,1)
        p2=P[:-2,1:-1];p3=P[:-2,2:];p4=P[1:-1,2:];p5=P[2:,2:];p6=P[2:,1:-1];p7=P[2:,:-2];p8=P[1:-1,:-2];p9=P[:-2,:-2]
        nb=p2+p3+p4+p5+p6+p7+p8+p9
        seq=[p2,p3,p4,p5,p6,p7,p8,p9,p2]
        tr=sum(((seq[i]==0)&(seq[i+1]==1)).astype(np.uint8) for i in range(8))
        if first: c=(p2*p4*p6==0)&(p4*p6*p8==0)
        else: c=(p2*p4*p8==0)&(p2*p6*p8==0)
        rm=(img==1)&(nb>=2)&(nb<=6)&(tr==1)&c
        img[rm]=0
        return rm.any()
    ch=True
    while ch:
        a=step(img,True); b=step(img,False); ch=a or b
    return img

def junctions(sk):
    P=np.pad(sk,1)
    nb=sum(P[1+dy:P.shape[0]-1+dy,1+dx:P.shape[1]-1+dx] for dy in (-1,0,1) for dx in (-1,0,1) if (dy,dx)!=(0,0))
    j=(sk==1)&(nb>=3)
    # cluster junction pixels: count 8-connected clusters
    comps=M.components(j,1)
    return len(comps), int(sk.sum())

def analyse(rgb, region_mask, tag, minpx=6):
    hh,ss,vv=M.rgb2hsv(rgb)
    glow=region_mask&(hh>=5)&(hh<=35)&(ss>=0.55)&(vv>=0.40)
    comps=M.components(glow,minpx)
    tot=sum(c[0] for c in comps) or 1
    vert=rung=diag=blob=0; njunc=0; nskel=0; hs=[];ws=[]
    # skeleton over the whole mask (components >= minpx only)
    keep=np.zeros_like(glow)
    for n,ys,xs in comps:
        keep[ys,xs]=True
        el,ang,bh,bw=M.comp_shape(ys,xs); hs.append(bh); ws.append(bw)
        if el>=2.5 and ang<=35: vert+=n
        elif el>=2.5 and ang>=55: rung+=n
        elif el>=2.5: diag+=n
        elif el<2.0: blob+=n
    sk=zhang_suen(keep)
    nj,nsk=junctions(sk)
    print(f"{tag}: glow px {glow.sum()} comps {len(comps)} vert {vert/tot:.2f} rung {rung/tot:.2f} diag {diag/tot:.2f} blob {blob/tot:.2f} | skeleton {nsk} px, junction clusters {nj} -> {100*nj/max(nsk,1):.2f} per 100 skel px; comp height med {np.median(hs):.0f} width med {np.median(ws):.0f}")

ref=np.asarray(Image.open("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/environments/refs/crater.jpg").convert("RGB"))
for name,(x0,y0,x1,y1) in {"ref left wall":(0,60,640,340),"ref right wall":(780,100,1280,420),"ref tee ledge":(0,420,420,720)}.items():
    crop=ref[y0:y1,x0:x1]
    hh,ss,vv=M.rgb2hsv(crop)
    # basalt-ish: not the big bright lava - exclude pixels in neighbourhoods where >40% of 15x15 px are bright orange: approximate by removing comps > 600 px
    full=np.ones(crop.shape[:2],bool)
    analyse(crop,full,name)
for s in ("hole10_1_tee","hole10_2_approach","hole10_3_lavarim"):
    f=np.asarray(Image.open(f"../proof/masks/9/{s}.full.png").convert("RGB")); i=np.asarray(Image.open(f"../proof/masks/9/{s}.id.png").convert("RGB")).astype(int)
    m=(abs(i[...,0]-40)<6)&(abs(i[...,1]-200)<6)&(abs(i[...,2]-200)<6)
    analyse(f,m,s)
