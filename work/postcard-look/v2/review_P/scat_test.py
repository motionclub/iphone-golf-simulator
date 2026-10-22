import sys, os, math, json, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P
import postcard_props_lib as PL
tag=os.environ.get("HOLE","08")
D = P.start(f"hole{tag}_design", out_dir=R + f"/work/postcard-look/v2/review_P/scr{tag}")
P.build_terrain(D); P.build_play_surfaces(D)
try: P.build_gameplay(D)
except Exception as e: print("build_gameplay fail", e)
bpy.context.view_layer.update()
PL._COUNTERS.clear(); PL.reset_scatter(D)
# my own BVH per prefix group
def bvh_for(prefixes):
    V=[];F=[]
    for o in bpy.data.objects:
        if o.type!='MESH' or not o.name.startswith(prefixes): continue
        me=o.data; me.calc_loop_triangles(); mw=o.matrix_world
        b=len(V); V+= [tuple(mw@v.co) for v in me.vertices]
        F+= [tuple(b+i for i in lt.vertices) for lt in me.loop_triangles]
    return BVHTree.FromPolygons(V,F) if F else None
land=bvh_for(("TERRAIN","FAIRWAY","GREEN","TEE_BOX","BUNKER"))
play=bvh_for(("FAIRWAY","GREEN","TEE_BOX","BUNKER"))
pin=[o for o in bpy.data.objects if o.name.startswith("HOLE_CUP")]
pinxy=[(o.matrix_world.translation.x,o.matrix_world.translation.y) for o in pin]
markers=[(o.name,o.matrix_world.translation.x,o.matrix_world.translation.y) for o in bpy.data.objects if o.name.startswith(("TEE_MARKER","BALL_START","FLAG","HOLE_CUP"))]
def check(objs,label):
    bpy.context.view_layer.update()
    on_water=0; dzmax=0; onplay=0; nearpin=1e9; nearmk=1e9; byond=0
    for o in objs:
        if o.get("lk_on_object"): continue
        p=o.matrix_world.translation
        h=land.ray_cast(Vector((p.x,p.y,500)),Vector((0,0,-1)),1000)
        if h[0] is None: on_water+=1; continue
        dzmax=max(dzmax,abs(p.z-h[0].z))
        if play is not None:
            hp=play.ray_cast(Vector((p.x,p.y,500)),Vector((0,0,-1)),1000)
            if hp[0] is not None and abs(hp[0].z-h[0].z)<0.3: onplay+=1
        for q in pinxy: nearpin=min(nearpin,math.hypot(p.x-q[0],p.y-q[1]))
        for m in markers: nearmk=min(nearmk,math.hypot(p.x-m[1],p.y-m[2]))
    print(f"  [{label}] n={len(objs)} onWater/noGround={on_water} onPlay={onplay} dzmax={dzmax:.3f} nearPin={nearpin:.1f} nearMarker={nearmk:.1f}")
    return on_water
tot=0;bad=0
plants=["PLANT_TUFT_A","PLANT_TUFT_B","PLANT_TUFT_C","PLANT_SHRUB_A","PLANT_SHRUB_B","PLANT_SHRUB_C","PLANT_FLOWER_A","PLANT_AGAVE_A","PLANT_PINE_A","PLANT_TREE_A"]
lib=[k for k in PL.library_report().get("kinds",[])] if hasattr(PL,"library_report") else []
print("HOLE",tag,"markers",markers[:4])
allp=list(PL.PLANT_KINDS)
print("plant kinds",allp)
regions={"None":None,"huge":(-2000,-2000,2000,2000),"tiny":(0,0,1,1),"zero":(5,5,5,5),"neg":(10,10,-10,-10),"disc_sea":PL.region_disc(0,-400,150)}
for k in allp:
    for rn,rg in regions.items():
        for seed in (3,):
            for cnt in (300,):
                try:
                    o=PL.scatter(D,k,cnt,region=rg,seed=seed)
                except Exception as e:
                    print("  EXC",k,rn,type(e).__name__,str(e)[:90]); continue
                tot+=len(o); 
                if o:
                    bad+=check(o,f"{k} {rn} s{seed} c{cnt}") if False else 0
                    # compact: only print failures
                    on_water=0
                    bpy.context.view_layer.update()
                    for ob in o:
                        if ob.get("lk_on_object"): continue
                        p=ob.matrix_world.translation
                        h=land.ray_cast(Vector((p.x,p.y,500)),Vector((0,0,-1)),1000)
                        if h[0] is None: on_water+=1
                        elif abs(p.z-h[0].z)>0.05: on_water+=100
                    bad+=on_water
                    if on_water: print("  BAD",k,rn,seed,cnt,on_water)
                PL.reset_scatter(D)
                for ob in o: bpy.data.objects.remove(ob,do_unlink=True)
print("TOTAL placed",tot,"bad",bad)
import postcard_look_lib as L
pathobjs=[]
if tag=="08":
    try:
        pathobjs=L.build_path(D,[(-9,-6),(-8.5,12),(-6,28),(-3,40)],width_m=2.6)
    except Exception as e: print("path build fail",e)
print("path objs",len(pathobjs))
# a mixed full-hole dressing, then full check on everything
PL.reset_scatter(D)
allobjs=[]
allobjs+=PL.scatter(D,{"PLANT_TUFT_A":3,"PLANT_TUFT_B":2,"PLANT_TUFT_C":2},1500,seed=9)
allobjs+=PL.scatter(D,["PLANT_SHRUB_A","PLANT_SHRUB_B","PLANT_SHRUB_C"],300,seed=10)
allobjs+=PL.scatter(D,["PLANT_PINE_A","PLANT_TREE_A"],40,seed=11)
allobjs+=PL.scatter(D,["PLANT_FLOWER_PURPLE","PLANT_AGAVE_A"],200,seed=12)
check(allobjs,"mixed")
bpy.context.view_layer.update()
if pathobjs:
    from mathutils import Vector as V3
    Pv=[];Pf=[]
    for o in pathobjs:
        me=o.data; me.calc_loop_triangles(); b=len(Pv); Pv+=[tuple(o.matrix_world@v.co) for v in me.vertices]; Pf+=[tuple(b+i for i in lt.vertices) for lt in me.loop_triangles]
    pb=BVHTree.FromPolygons(Pv,Pf)
    n=0;dmin=9e9
    for o in allobjs:
        p=o.location; hit=pb.find_nearest(V3((p.x,p.y,0)))
        # xy distance to path: use projection on z=0 plane trick via ray from above
        h=pb.ray_cast(V3((p.x,p.y,500)),V3((0,0,-1)),1000)
        if h[0] is not None: n+=1
    print("plants under path footprint",n)
json.dump([[o.name,*map(float,o.matrix_world.translation)] for o in allobjs],open(f"mixed_{tag}.json","w"))
# D=None path
try:
    o=PL.scatter(None,"PLANT_TUFT_A",50,region=(-200,-200,200,200),seed=1); print("D=None region scatter placed",len(o),"(no land mask)")
except Exception as e: print("D=None exc",e)
