#!/usr/bin/env python3
"""SMOKE_SOFT numbers of a (full, dry) pair of Game-view frames, same definitions as proof/measure.py smoke_metrics (edge step p99 on a smooth backdrop, |dLum| median/p95/max, share_readable).
usage: smoke_stats.py <full.png> <dry.png> [more pairs...]"""
import sys, numpy as np
from PIL import Image
def lum(a): return .2126*a[...,0]+.7152*a[...,1]+.0722*a[...,2]
def stats(fp, dp, tag):
    full=np.asarray(Image.open(fp).convert("RGB")).astype(float); dry=np.asarray(Image.open(dp).convert("RGB")).astype(float)
    dl=np.abs(lum(full)-lum(dry)); mk=dl>1.5
    if mk.sum()<500: print(tag,"fewer than 500 changed px"); return
    v=dl[mk]
    def grad(a): gy,gx=np.gradient(lum(a)); return np.hypot(gx,gy)
    gf,gd=grad(full),grad(dry)
    pad=np.pad(mk,1,mode="edge"); c=pad[1:-1,1:-1]
    band=(c^pad[:-2,1:-1])|(c^pad[2:,1:-1])|(c^pad[1:-1,:-2])|(c^pad[1:-1,2:])
    pb=np.pad(band,1,mode="constant"); band=band|pb[:-2,1:-1]|pb[2:,1:-1]|pb[1:-1,:-2]|pb[1:-1,2:]
    band[:3,:]=False; band[-3:,:]=False; band[:,:3]=False; band[:,-3:]=False
    smooth=band&(gd<=3.0); step=np.abs(gf-gd)[smooth]; stepall=np.abs(gf-gd)[band]
    ep=np.percentile(step,99) if smooth.sum()>=50 else float("nan")
    ok = np.percentile(v,95)>=8 and (ep<=6) and v.max()<=110
    print(f"{tag}: changed {mk.mean()*100:.2f}% readable(>=10) {(dl>=10).mean()*100:.2f}%  |dLum| med {np.median(v):.1f} p95 {np.percentile(v,95):.1f} p99 {np.percentile(v,99):.1f} max {v.max():.1f}  edge p99 {ep:.2f} ({smooth.sum()} px; all-boundary p99 {np.percentile(stepall,99):.1f})  plume mean RGB {tuple(int(x) for x in full[mk].mean(0))}  {'ok' if ok else 'FAIL'}")
if __name__=="__main__":
    a=sys.argv[1:]
    for i in range(0,len(a),2): stats(a[i],a[i+1],a[i].split("/")[-1])
