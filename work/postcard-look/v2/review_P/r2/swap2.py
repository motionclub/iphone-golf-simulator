import sys, os, math, collections, json
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_props_lib as PL
hole = os.environ.get("HOLE", "10"); seed = int(os.environ.get("SEED", "1"))
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
bpy.context.view_layer.update()
def wverts(o):
    me=o.data; co=np.empty(len(me.vertices)*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
    M=np.array(o.matrix_world); return co@M[:3,:3].T+M[:3,3]
leg={}
for o in PL.legacy_rocks():
    w=wverts(o); leg[o.name]=(w.min(0),w.max(0),o.data.name)
nleg=len(leg)
# land bvh from non-rock meshes
V=[];F=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(("TERRAIN","FAIRWAY","GREEN","TEE_BOX","BUNKER")): continue
    me=o.data; me.calc_loop_triangles(); w=wverts(o); b=len(V); V+=[tuple(p) for p in w]; F+=[tuple(b+i for i in lt.vertices) for lt in me.loop_triangles]
land=BVHTree.FromPolygons(V,F)
rep=[]
out=PL.swap_legacy_rocks(None, basalt=(hole=="10"), seed=seed, report=rep)
bpy.context.view_layer.update()
rocks=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(("ROCK_","CLIFF_")) and not any(c.name==PL.LIB_COLLECTION for c in o.users_collection)]
bad=0; mn=9; mx=0; mr=0; maxshear=0
for o in rocks:
    M=o.matrix_world.to_3x3()
    s=[M.col[i].length for i in range(3)]
    c=[M.col[i].normalized() for i in range(3)]
    maxshear=max(maxshear,abs(c[0].dot(c[1])),abs(c[0].dot(c[2])),abs(c[1].dot(c[2])))
    neg = M.determinant()<0
    mn=min(mn,min(s)); mx=max(mx,max(s)); r=max(s)/min(s); mr=max(mr,r)
    if min(s)<0.5-1e-3 or max(s)>2.0+1e-3 or r>2.0+1e-3: bad+=1
vmin=min(PL.welded_vertex_count(o.data) for o in rocks)
# stacked: pairs among all rocks with near xy centre and z separation
infos=[]
for o in rocks:
    w=wverts(o); infos.append((o,w.min(0),w.max(0)))
stk=[]
for i in range(len(infos)):
    for j in range(i+1,len(infos)):
        a,b=infos[i],infos[j]
        ca=(a[1]+a[2])/2; cb=(b[1]+b[2])/2
        fa=min(a[2][0]-a[1][0],a[2][1]-a[1][1]); fb=min(b[2][0]-b[1][0],b[2][1]-b[1][1])
        dxy=math.hypot(ca[0]-cb[0],ca[1]-cb[1])
        if dxy<0.3*min(fa,fb) and abs(ca[2]-cb[2])>0.3*min(a[2][2]-a[1][2],b[2][2]-b[1][2]) and min(fa,fb)>2:
            stk.append((a[0].name,b[0].name,round(dxy,2),round(ca[2]-cb[2],1)))
# groups: top delta and bottom vs ground
bot=[];top=[];flo=[]
for o in out:
    lg=leg.get(o.get("lk_swap"))
    if not lg: continue
w=None
# per lk_swap group
grp=collections.defaultdict(list)
for o in out: grp[o["lk_swap"]].append(o)
dtop=[];dbot=[]
for k,g in grp.items():
    lg=leg.get(k)
    if not lg: continue
    ws=np.vstack([wverts(o) for o in g])
    dtop.append((k,round(ws.max(0)[2]-lg[1][2],2),g[0].data.name))
    dbot.append((k,round(ws.min(0)[2]-lg[0][2],2),g[0].data.name))
# float check on dry rocks: lowest vertex height above ground raycast at footprint
fl=[]
for o in out:
    w=wverts(o); lo=w[w[:,2]<w[:,2].min()+0.3]
    p=lo.mean(0)
    h=land.ray_cast(Vector((p[0],p[1],500)),Vector((0,0,-1)),1000)
    if h[0] is not None:
        d=w[:,2].min()-h[0].z
        fl.append((o.name,round(d,2),round(float(w[:,2].min()),2)))
print(f"HOLE {hole} seed {seed}: legacy {nleg} out {len(out)} rocks {len(rocks)} scale {mn:.3f}..{mx:.3f} maxratio {mr:.3f} viol {bad} maxshear {maxshear:.4f} vmin {vmin}")
print(" stackedpairs(my metric)", len(stk), stk[:6])
dt=sorted(dtop,key=lambda x:x[1]); db=sorted(dbot,key=lambda x:x[1])
print(" top delta min/max", dt[:3], dt[-3:])
print(" bot delta min/max", db[:3], db[-3:])
fa=[f for f in fl if f[1]>0.5 and f[2]>0.3]
print(" floating>0.5 above terrain & z>0.3:", len(fa), fa[:6])
bu=[f for f in fl if f[1]<-1.5 and f[2]>0.3]
print(" buried>1.5:", len(bu), bu[:4])
print(" kinds", collections.Counter(o.data.name for o in rocks).most_common(14))
r=PL.swap_composition_report()
print(" comp", r['ok'], len(r['vertical_stacks']), len(r['clones']))
if os.environ.get("SAVE"): bpy.ops.wm.save_as_mainfile(filepath=os.environ["SAVE"])
print("=== stacked detail")
nm={o.name:(lo,hi) for o,lo,hi in infos}
seen=set()
for a,b,d,dz in stk[:40]:
    for n in (a,b):
        if n in seen: continue
        seen.add(n); lo,hi=nm[n]; o=bpy.data.objects[n]
        print(f"  {n:28s} swap={o.get('lk_swap')} xy=({(lo[0]+hi[0])/2:.1f},{(lo[1]+hi[1])/2:.1f}) z={lo[2]:.1f}..{hi[2]:.1f} size={hi[0]-lo[0]:.1f}x{hi[1]-lo[1]:.1f}")
