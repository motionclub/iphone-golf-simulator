# independent waterline-based shelf width: horizontal ray at z=0.09 from open water to find the outer face of whatever stands at the waterline,
# then walk outward along the same line over the top-down category grid and measure how far SHELF/SURF continues.
import bpy, sys, numpy as np, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args = sys.argv[sys.argv.index("--")+1:]
CATS=(1,) if len(args)>3 and args[3]=="shelf" else (1,2)
BL=args[0]; NPZ=args[1]; STEP=float(args[2]) if len(args)>2 else 1.0
bpy.ops.wm.open_mainfile(filepath=BL)
d=np.load(NPZ); G=d['G']; cell=float(d['cell']); x0=float(d['x0']); y0=float(d['y0'])
V=[];F=[];NAME=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.name.startswith('WATER_'): continue
    M=o.matrix_world; base=len(V)
    V+= [tuple(M@v.co) for v in o.data.vertices]
    for p in o.data.polygons:
        vs=[base+i for i in p.vertices]
        for k in range(1,len(vs)-1): F.append((vs[0],vs[k],vs[k+1])); NAME.append(o.name)
bvh=BVHTree.FromPolygons(V,F)
land=(G==0).astype(np.float32)
# blur
def box(a,r):
    k=2*r+1
    c=np.cumsum(np.pad(a,((r+1,r),(0,0))),0); a1=(c[k:]-c[:-k])
    c=np.cumsum(np.pad(a1,((0,0),(r+1,r))),1); return (c[:,k:]-c[:,:-k])/(k*k)
r=int(3.0/cell)
Bl=box(land,r)
gy,gx=np.gradient(Bl)
pad=np.pad(G==0,1,constant_values=True)
nb=~(pad[:-2,1:-1]&pad[2:,1:-1]&pad[1:-1,:-2]&pad[1:-1,2:])
bd=(G==0)&nb
bj,bi=np.nonzero(bd)
sel=np.arange(0,len(bj),int(STEP/cell))
vis_l=[];foot_l=[];widths=[];pos=[];skipped=0;faces=[];nm=[]
H,W=G.shape
def cat_at(x,y):
    i=int((x-x0)/cell); j=int((y-y0)/cell)
    if 0<=i<W and 0<=j<H: return G[j,i]
    return -1
for k in sel:
    i,j=bi[k],bj[k]
    n=np.array([-gx[j,i],-gy[j,i]]); nn=np.hypot(*n)
    if nn<1e-6: skipped+=1; continue
    n/=nn
    x=x0+(i+.5)*cell; y=y0+(j+.5)*cell
    # must face water
    if cat_at(x+n[0]*2,y+n[1]*2) not in (1,2,3): skipped+=1; continue
    s=Vector((x+n[0]*10,y+n[1]*10,0.09))
    h=bvh.ray_cast(s,Vector((-n[0],-n[1],0)),22.0)
    if h[0] is None: skipped+=1; continue
    fx,fy=h[0].x,h[0].y
    off=math.hypot(fx-x,fy-y)
    if off>4.0: skipped+=1; continue   # blocked by a rock / not the shore face
    # walk outward from the face: skip land cover (overhang), then the first shelf/surf run
    last=0.0; t=0.0; gap=0; started=False; foot=0.0
    while t<14.0:
        t+=0.1
        c=cat_at(fx+n[0]*t,fy+n[1]*t)
        if c==0 and not started: foot=t; continue
        if c in CATS:
            if not started: started=True; first=t
            last=t; gap=0
        else:
            gap+=1
            if gap>8 and started: break
            if not started and gap>12: break
    if not started: first=last=foot
    vis=last-first
    edge=last   # distance from the waterline face to the outer edge of the turquoise/white
    widths.append(edge); vis_l.append(vis); foot_l.append(foot); pos.append((fx,fy)); nm.append(h[3] if False else NAME[h[2]])
widths=np.array(widths); vis_l=np.array(vis_l); foot_l=np.array(foot_l)
print('skin top-down overhang beyond the waterline face: median %.2f p95 %.2f max %.2f'%(np.median(foot_l),np.percentile(foot_l,95),foot_l.max()))
print('VISIBLE shelf/surf run (top-down, beyond skin footprint): median %.2f mean %.2f p95 %.2f max %.2f ; none %.0f%%'%(np.median(vis_l),vis_l.mean(),np.percentile(vis_l,95),vis_l.max(),100*(vis_l<0.2).mean()))
print("samples %d (skipped %d) every ~%.1f m"%(len(widths),skipped,STEP))
print("waterline-face visible shelf width: median %.2f mean %.2f p90 %.2f p95 %.2f max %.2f"%(np.median(widths),widths.mean(),np.percentile(widths,90),np.percentile(widths,95),widths.max()))
print("zero (no shelf) %.0f%% ; >2.5 m %.0f%% ; >4.5 m %.0f%% ; >6 m %.0f%%"%(100*(widths<0.2).mean(),100*(widths>2.5).mean(),100*(widths>4.5).mean(),100*(widths>6).mean()))
pos=np.array(pos)
for thr in (4.5,):
    idx=np.nonzero(widths>thr)[0]
    from collections import defaultdict
    c=defaultdict(list)
    for q in idx: c[(round(pos[q,0]/10),round(pos[q,1]/10))].append(widths[q])
    print(">%.1f m clusters:"%thr,[(k[0]*10,k[1]*10,len(v),round(max(v),1)) for k,v in sorted(c.items(),key=lambda kv:-max(kv[1]))[:10]])
# continuity: along ordered boundary samples? report share of >0.3 m samples and run structure by sorting by angle not available
np.save(BL.replace('.blend','_wl.npy'),np.column_stack([pos,widths]))
