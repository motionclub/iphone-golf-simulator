#!/usr/bin/env python3
"""Basalt colour statistics of Game-view stills using the PostcardProofMasks id render (basalt = id colour (40,200,200)).
usage: basalt_stats.py <full.png> <id.png> [...]   or  basalt_stats.py <dir> <prefix>   (dir has <prefix>.full.png/.id.png)"""
import sys, numpy as np
from PIL import Image
def hsv(a):
    a=a.astype(float)/255; mx=a.max(-1); mn=a.min(-1); d=mx-mn
    r,g,b=a[...,0],a[...,1],a[...,2]; h=np.zeros_like(mx); m=d>1e-9
    rm=m&(mx==r); gm=m&(mx==g)&~rm; bm=m&~rm&~gm
    h[rm]=((g-b)[rm]/d[rm])%6; h[gm]=(b-r)[gm]/d[gm]+2; h[bm]=(r-g)[bm]/d[bm]+4
    return h*60, np.where(mx>1e-9,d/np.maximum(mx,1e-9),0), mx
def stats(full, idm, tag):
    f=np.asarray(Image.open(full).convert("RGB")); i=np.asarray(Image.open(idm).convert("RGB")).astype(int)
    m=(abs(i[...,0]-40)<6)&(abs(i[...,1]-200)<6)&(abs(i[...,2]-200)<6)
    px=f[m]
    if len(px)<50: print(tag,"basalt px",len(px)); return
    lum=.2126*px[:,0]+.7152*px[:,1]+.0722*px[:,2]
    # non-glow: exclude pixels brighter than 1.8x median lum (glow joints)
    med=np.median(lum); ng=lum<med*1.6+8
    p=px[ng]; h,s,v=hsv(p)
    mean=p.mean(0); med3=np.median(p,0)
    hm,sm,vm=hsv(np.array([[mean]]).astype(float))
    hmed,smed,vmed=hsv(np.array([[med3]]).astype(float))
    print(f"{tag}: basalt px {len(px)} ({100*len(px)/m.size:.1f}% of frame), non-glow {ng.mean()*100:.1f}%  mean RGB ({mean[0]:.0f},{mean[1]:.0f},{mean[2]:.0f}) hue {hm[0,0]:.0f} S {sm[0,0]:.2f} V {vm[0,0]:.2f}  median RGB ({med3[0]:.0f},{med3[1]:.0f},{med3[2]:.0f}) S {smed[0,0]:.2f}  per-pixel S p50 {np.median(s):.2f} p90 {np.percentile(s,90):.2f}  lum median {np.median(.2126*p[:,0]+.7152*p[:,1]+.0722*p[:,2]):.0f}")
if __name__=="__main__":
    a=sys.argv[1:]
    if len(a)==2 and not a[0].endswith(".png"):
        stats(a[0]+"/"+a[1]+".full.png",a[0]+"/"+a[1]+".id.png",a[1])
    else:
        for k in range(0,len(a),2): stats(a[k],a[k+1],a[k])
