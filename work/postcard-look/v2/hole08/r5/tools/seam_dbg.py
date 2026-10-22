import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
import hole08_look as K
bpy.context.view_layer.update()
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
cam,look,b=K.tee_cam(); print("cam",cam,look,b)
for py in (640,660,667,671,675,680,700):
    row=[]
    for px in range(0,900,30):
        d=K._cam_ray(cam,look,px,py)
        ok,loc,n,i,ob,m=sc.ray_cast(dg,cam,d,distance=900)
        row.append((ob.name[:6] if ok else "-"))
    print(py,row)
