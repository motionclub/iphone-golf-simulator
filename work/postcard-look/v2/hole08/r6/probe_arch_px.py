import sys, math, json
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO+"/blender/scripts")
import bpy
from mathutils import Vector
YD=0.9144
blend=sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.open_mainfile(filepath=blend)
pos=(-10.94,13.21,302.93); look=(-28.7,11.81,317.0)
cam=Vector((pos[0]*YD,pos[2]*YD,pos[1]*YD)); lk=Vector((look[0]*YD,look[2]*YD,look[1]*YD))
f=(lk-cam).normalized(); r=f.cross(Vector((0,0,1))).normalized(); u=r.cross(f).normalized()
th=math.tan(math.radians(30)); W,H=900,1600
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
def hit(px,py):
    x=((px+0.5)/W*2-1)*th*W/H; y=(1-(py+0.5)/H*2)*th
    d=(f+r*x+u*y).normalized()
    ok,loc,n,i,ob,m=sc.ray_cast(dg,cam,d,distance=900)
    if not ok: return None
    me=ob.data
    mat=None
    try:
        mat=me.materials[me.polygons[i].material_index].name
    except Exception: pass
    return ob.name,mat,tuple(round(c,2) for c in loc),tuple(round(c,2) for c in n)
for p in [(350,1500),(450,1480),(300,1450),(600,1500),(250,1560),(450,1560),(150,1500),(100,1300),(700,1580),(500,1420)]:
    print(p, hit(*p))
