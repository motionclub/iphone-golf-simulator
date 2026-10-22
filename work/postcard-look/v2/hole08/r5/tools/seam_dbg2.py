import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
import hole08_look as K
bpy.context.view_layer.update()
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
cam,look,b=K.tee_cam()
def name(px,py):
    d=K._cam_ray(cam,look,px,py)
    ok,loc,n,i,ob,m=sc.ray_cast(dg,cam,d,distance=900)
    return ob.name if ok else "-"
for py in range(600,740,4):
    xs=list(range(0,900,2)); isp=[name(x,py).startswith("DRESS_PATH") for x in xs]
    tr=[xs[i] for i in range(1,len(xs)) if isp[i]!=isp[i-1]]
    ob_c=name(450,py)[:6]
    print("ROW",py,"center",ob_c,"path transitions",tr)
