import sys, os, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, bmesh, numpy as np
from mathutils import Vector, Matrix
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
col=bpy.data.collections.new("c"); bpy.context.scene.collection.children.link(col)
def mk(name, meshname, bm, loc=(0,0,0), scale=(1,1,1), rot=(0,0,0)):
    me=bpy.data.meshes.new(meshname); bm.to_mesh(me); bm.free()
    ob=bpy.data.objects.new(name,me); col.objects.link(ob); ob.location=loc; ob.scale=scale; ob.rotation_euler=rot; return ob
def ico(sub):
    bm=bmesh.new(); bmesh.ops.create_icosphere(bm,subdivisions=sub,radius=1.0); return bm
def uv(seg):
    bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=seg,v_segments=seg//2,radius=1.0); return bm
def cube():
    bm=bmesh.new(); bmesh.ops.create_cube(bm,size=2.0); return bm
def split_ico():
    bm=ico(1); bmesh.ops.split_edges(bm,edges=bm.edges[:]); return bm
muts=[
 mk("ROCK_SMALL.001","ROCK_SMALL",ico(1),(10,0,1),(2,3,4)),
 mk("ROCK_X1","anything",ico(1),(20,0,1),(3,3,3),(0.3,0.2,1)),
 mk("CLIFF_ROCK.099","CLIFF_ROCK",split_ico(),(30,0,1),(5,5,2)),
 mk("ROCK_UV24","uv",uv(8),(40,0,1),(3,3,3)),
 mk("ROCK_CUBE","cube",cube(),(50,0,1),(4,4,4)),
 mk("ROCK_SKIN_BAD","skinmesh",ico(1),(60,0,1),(4,4,4)),
 mk("ROCK_BIGICO","bigico",ico(3),(70,0,1),(4,4,4)),
 mk("ROCK_WALL_FLAT.003","ROCK_WALL_FLAT",ico(1),(80,0,20),(40,3,40)),
]
try:
    print("assert before:",PL.assert_no_legacy_rocks(None,raise_on_fail=False)["offenders"])
except Exception as e: print("assert exc",e)
rep=[]
try:
    out=PL.swap_legacy_rocks(None,report=rep)
except Exception as e:
    print("swap exc",type(e).__name__,e); out=[]
bpy.context.view_layer.update()
print("after assert:",PL.assert_no_legacy_rocks(None,raise_on_fail=False))
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(("ROCK","CLIFF")): 
        s=o.matrix_world.to_scale(); print(" ",o.name,o.data.name,"verts",PL.welded_vertex_count(o.data),"scale",tuple(round(v,2) for v in s))
