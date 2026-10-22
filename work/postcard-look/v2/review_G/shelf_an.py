import numpy as np, sys
from math import hypot
d=np.load(sys.argv[1]); G=d['G']; cell=float(d['cell']); x0=float(d['x0']); y0=float(d['y0'])
land=(G==0); shelf=(G==1); surf=(G==2); ocean=(G==3)
print("cells land %d shelf %d surf %d ocean %d none %d"%(land.sum(),shelf.sum(),surf.sum(),ocean.sum(),(G<0).sum()))
print("visible shelf area m2 %.0f  surf area %.0f"%(shelf.sum()*cell**2, surf.sum()*cell**2))
# land boundary cells: land with a 4-neighbour non-land & non-none
pad=np.pad(land,1,constant_values=True)
nb=~(pad[:-2,1:-1]&pad[2:,1:-1]&pad[1:-1,:-2]&pad[1:-1,2:])
bd=land&nb
bj,bi=np.nonzero(bd)
print("boundary cells",len(bj), "perimeter approx m", len(bj)*cell)
# KD tree on boundary cells via grid chunk brute force using numpy (use scipy-less): sort and use coarse bucket
from collections import defaultdict
B=np.stack([bi,bj],1).astype(np.float32)
bucket=defaultdict(list)
S=16
for k,(i,j) in enumerate(B.astype(int)): bucket[(i//S,j//S)].append(k)
def nearest(i,j,rmax=200):
    best=1e9;bk=-1
    ci,cj=i//S,j//S
    R=1
    while True:
        for a in range(ci-R,ci+R+1):
            for b in range(cj-R,cj+R+1):
                if max(abs(a-ci),abs(b-cj))!=R and R>1: continue
                for k in bucket.get((a,b),()):
                    dd=(B[k,0]-i)**2+(B[k,1]-j)**2
                    if dd<best: best=dd;bk=k
        if bk>=0 and (R*S)**2>best*1.0+0: break
        R+=1
        if R*S>rmax*1.0/cell: break
    return bk,best**0.5*cell
sj,si=np.nonzero(shelf|surf)   # turquoise + white that is visible on top
res=[]
w_at=defaultdict(float)
dist=np.zeros(len(sj))
for n,(i,j) in enumerate(zip(si,sj)):
    k,dd=nearest(i,j); dist[n]=dd; w_at[k]=max(w_at[k],dd)
sh_only=shelf[sj,si]
print("visible shelf+surf cells: dist to land: median %.2f p95 %.2f max %.2f ; >6 m: %d cells (%.0f m2)"%(np.median(dist),np.percentile(dist,95),dist.max(),(dist>6).sum(),(dist>6).sum()*cell**2))
dsh=dist[sh_only]
print("shelf-only (turquoise on top): n %d median %.2f p95 %.2f max %.2f"%(len(dsh),np.median(dsh),np.percentile(dsh,95),dsh.max()))
# per boundary cell width (only boundary cells that face ocean-ish: have any non-land neighbour within 3 m being water)
W=np.zeros(len(B))
for k,v in w_at.items(): W[k]=v
# restrict to boundary cells touching water within 2.5 m (exclude cells along land-land gaps)
water=(G>=1)
facing=np.zeros(len(B),bool)
r=int(2.5/cell)
for k,(i,j) in enumerate(B.astype(int)):
    sl=water[max(j-r,0):j+r+1,max(i-r,0):i+r+1]
    facing[k]=sl.any()
Wf=W[facing]
print("shore-facing boundary cells %d : width median %.2f mean %.2f p95 %.2f max %.2f ; zero width %.0f%% ; >2.5m %.0f%% ; >4.5m %.0f%% ; >6 m %.0f%%"%(len(Wf),np.median(Wf),Wf.mean(),np.percentile(Wf,95),Wf.max(),100*(Wf<0.3).mean(),100*(Wf>2.5).mean(),100*(Wf>4.5).mean(),100*(Wf>6).mean()))
print("mean visible shelf ring width = area/perimeter = %.2f m"%(shelf.sum()*cell**2/(facing.sum()*cell)))
# dump hot spots: boundary cells with width>4.5
hs=np.nonzero(facing&(W>4.5))[0]
print("hot spots >4.5m: %d cells"%len(hs))
if len(hs):
    xs_=x0+B[hs,0]*cell; ys_=y0+B[hs,1]*cell
    # cluster by 10 m grid
    c=defaultdict(list)
    for x,y,w in zip(xs_,ys_,W[hs]): c[(round(x/10),round(y/10))].append(w)
    for k,v in sorted(c.items(),key=lambda kv:-max(kv[1]))[:12]: print("  near (%.0f,%.0f) m  n=%d max %.1f"%(k[0]*10,k[1]*10,len(v),max(v)))
# also: turquoise visible cells > 6m away
