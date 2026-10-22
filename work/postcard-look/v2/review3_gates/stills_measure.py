import numpy as np
from PIL import Image
import colorsys,glob,os,json
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
D=R+'ArtDir/screenshots/golf_postcards/look/'
def hsv(a):
    a=a.astype(np.float32)/255; mx=a.max(-1); mn=a.min(-1); d=mx-mn+1e-9
    r,g,b=a[...,0],a[...,1],a[...,2]
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
    s=np.where(mx>0,d/(mx+1e-9),0); return h,s,mx
names=['hole08_1_tee','hole08_2_approach','hole08_3_arch','hole09_1_tee','hole09_2_approach','hole09_3_ruin','hole10_1_tee','hole10_2_approach','hole10_3_lavarim']
out={}
for n in names:
    im=np.array(Image.open(D+n+'.png').convert('RGB')); H,W,_=im.shape
    h,s,v=hsv(im)
    lum=0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2]
    grass=(h>45)&(h<100)&(s>0.35)&(v>0.3)
    low=np.zeros_like(grass); low[int(H*0.4):]=True
    g=grass&low
    # flat windows 16x16 in the lower 60%: local lum std (high-pass: window sd after removing 64px blur)
    lw=lum[int(H*0.4):]; hh=(lw.shape[0]//16)*16; ww=(W//16)*16
    blk=lw[:hh,:ww].reshape(hh//16,16,ww//16,16).transpose(0,2,1,3).reshape(-1,256)
    sd=blk.std(1)/255
    # lava
    lava=(h>5)&(h<32)&(s>0.7)&(v>0.55)
    turq=(h>170)&(h<205)&(s>0.45)&(v>0.3)
    d_=dict(grass_px=int(g.sum()),grass_hue_mean=float(h[g].mean()) if g.sum() else None,grass_S=float(s[g].mean()) if g.sum() else None,grass_V=float(v[g].mean()) if g.sum() else None,
      lowsd=float(lum[int(H*0.4):].std()),flat_win_pct=float((sd<0.006).mean()*100),median_win_sd=float(np.median(sd)),
      lava_pct=float(lava.mean()*100),turq_pct=float(turq.mean()*100),unique_colors_q=int(len(np.unique((im//16).reshape(-1,3),axis=0))))
    if lava.sum()>1000: d_.update(lava_hue=float(h[lava].mean()),lava_S=float(s[lava].mean()),lava_V=float(v[lava].mean()),lava_inband=float(((h>8)&(h<28)&(s>=.75)&(v>=.7))[lava].mean()))
    out[n]=d_; print(n,{k:round(x,3) if isinstance(x,float) else x for k,x in d_.items()})
json.dump(out,open(R+'work/postcard-look/v2/review3_gates/stills_measure.json','w'),indent=1)
