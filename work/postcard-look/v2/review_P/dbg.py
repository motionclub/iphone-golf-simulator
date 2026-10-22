import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P
import postcard_props_lib as PL
D = P.start("hole08_design", out_dir=R + "/work/postcard-look/v2/review_P/scr08")
P.build_terrain(D); P.build_play_surfaces(D); P.build_gameplay(D)
V=[];F=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(("TERRAIN","FAIRWAY","GREEN","TEE_BOX","BUNKER")):
        me=o.data; me.calc_loop_triangles(); b=len(V); V+=[tuple(o.matrix_world@v.co) for v in me.vertices]; F+=[tuple(b+i for i in lt.vertices) for lt in me.loop_triangles]
land=BVHTree.FromPolygons(V,F)
for k in ("PLANT_PINE_A","PLANT_AGAVE_A","PLANT_TUFT_A"):
    for o in PL.scatter(D,k,6,seed=1):
        p=o.matrix_world.translation; h=land.ray_cast(Vector((p.x,p.y,500)),Vector((0,0,-1)),1000)
        print(k,o.name,"loc",tuple(round(v,2) for v in p),"hit",None if h[0] is None else round(h[0].z,3),"local",tuple(round(v,2) for v in o.location),"parent",o.parent and o.parent.name)
