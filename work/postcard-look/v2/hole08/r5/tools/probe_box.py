import sys, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
loc=Vector((-9.0,276.0,9.48)); look=Vector((-26.243,289.865,9.8))
fwd=(look-loc).normalized(); right=fwd.cross(Vector((0,0,1))).normalized(); up=right.cross(fwd).normalized()
th=math.tan(math.radians(30)); W,H=900,1600
def ray(px,py):
    x=((px+.5)/W*2-1)*th*W/H; y=(1-(py+.5)/H*2)*th
    d=(fwd+right*x+up*y).normalized()
    return sc.ray_cast(dg,loc,d,distance=4000)
from collections import Counter
cnt=Counter()
for py in range(1170,1280,6):
    for px in range(600,900,10):
        ok,p,n,idx,ob,mw=ray(px,py)
        if ok:
            me=ob.data; poly=me.polygons[idx]
            nw=(mw.to_3x3()@poly.normal).normalized()
            cnt[(ob.name, me.materials[poly.material_index].name, round(nw.z,1), round(p.z,1))]+=1
for k,v in cnt.most_common(30): print("BOX",k,v)
cnt=Counter()
for py in range(1190,1420,8):
    for px in range(200,880,12):
        ok,p,n,idx,ob,mw=ray(px,py)
        if ok:
            me=ob.data; poly=me.polygons[idx]
            nw=(mw.to_3x3()@poly.normal).normalized()
            cnt[(ob.name, me.materials[poly.material_index].name, round(nw.z,1), round(p.z,1))]+=1
for k,v in cnt.most_common(30): print("SLAB",k,v)
