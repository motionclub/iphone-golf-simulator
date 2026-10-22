import sys, os, math, json
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P
import postcard_props_lib as PL
tag=os.environ.get("HOLE","09")
D = P.start(f"hole{tag}_design", out_dir=R + f"/work/postcard-look/v2/review_P/r2/scr{tag}")
P.build_terrain(D); P.build_play_surfaces(D)
try: P.build_gameplay(D)
except Exception as e: print("build_gameplay fail", e)
bpy.context.view_layer.update()
def land_hit(p):
    return None
V=[];F=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(("TERRAIN","FAIRWAY","GREEN","TEE_BOX","BUNKER")): continue
    me=o.data; me.calc_loop_triangles(); mw=o.matrix_world
    b=len(V); V+=[tuple(mw@v.co) for v in me.vertices]; F+=[tuple(b+i for i in lt.vertices) for lt in me.loop_triangles]
land=BVHTree.FromPolygons(V,F)
def chk(objs):
    w=0; zlow=1e9
    bpy.context.view_layer.update()
    for ob in objs:
        p=ob.matrix_world.translation; zlow=min(zlow,p.z)
        h=land.ray_cast(Vector((p.x,p.y,500)),Vector((0,0,-1)),1000)
        if h[0] is None or p.z<0.3: w+=1
    return w,zlow
combos=[]
sea=PL.region_disc(0,-300,120) 
cases={
 "safe=False,None":dict(region=None,safe=False),
 "respect=False":dict(region=None,respect=False),
 "z=1.0 seaRegion":dict(region=(-400,-400,400,-100),z=1.0),
 "z=-1 big":dict(region=(-2000,-2000,2000,2000),z=-1.0),
 "z=0.5 big safe=False":dict(region=(-2000,-2000,2000,2000),z=0.5,safe=False),
 "surface=sea":dict(region=None,surface='sea'),
 "surface=any":dict(region=None,surface='any'),
 "shore_margin=0":dict(region=None,shore_margin_m=0.0),
 "shore_margin=-5":dict(region=None,shore_margin_m=-5.0),
 "sink=-30":dict(region=None,sink=-30.0),
 "sink=40":dict(region=None,sink=40.0),
 "margin_m=-20":dict(region=None,margin_m=-20.0),
 "mask lambda True":dict(region=None,masks=(lambda x,y: True,)),
 "wet":dict(region=None,wet=True),
 "callable region":dict(region=lambda x,y: True),
 "big count":dict(region=None,count=4000),
}
tot=0
for kind in ("PLANT_TUFT_A","PLANT_PINE_A","PLANT_SHRUB_C","PLANT_AGAVE_A"):
    for name,kw in cases.items():
        kw=dict(kw); cnt=kw.pop("count",400)
        PL.reset_scatter(D)
        try: o=PL.scatter(D,kind,cnt,seed=5,**kw)
        except Exception as e:
            print(f"  {kind:14s} {name:24s} EXC {type(e).__name__}: {str(e)[:60]}"); continue
        w,zl=chk(o); tot+=len(o)
        print(f"  {kind:14s} {name:24s} n={len(o):4d} onWaterOrLow={w} zmin={zl:.2f}" + ("   <<<<< BAD" if w else ""))
        for ob in o: bpy.data.objects.remove(ob,do_unlink=True)
# place() direct
for z in (0.0,0.29,-3.0):
    try: PL.place(D,"PLANT_TUFT_A",(0,-200,z)); print("place z",z,"ACCEPTED  <<<< BAD")
    except Exception as e: print("place z",z,"refused")
# place_fit / alt kinds with plant: place_fit?
try:
    ob=PL.place_fit(D,"PLANT_TUFT_A",(0,-200,0.0),(1,1,1)); print("place_fit at z0 ACCEPTED (", ob.name,") <<<< check")
except Exception as e: print("place_fit refused",str(e)[:50])
# other dressing scatters that might sit on water: DRESS_ / vines
print("PLANT_KINDS",PL.PLANT_KINDS)
print("TOTAL",tot)
