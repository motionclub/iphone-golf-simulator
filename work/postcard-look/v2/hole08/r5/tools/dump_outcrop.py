import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
for ob in bpy.data.objects:
    if ob.name.startswith("ROCK_OUTCROP"):
        me=ob.data; mw=np.array(ob.matrix_world)
        print(ob.name, "loc", tuple(round(x,2) for x in ob.location), "scale", tuple(round(x,3) for x in ob.scale), "rot z", round(ob.rotation_euler.z,3), "mats",[m.name for m in me.materials], "polys",len(me.polygons))
        up={}
        for p in me.polygons:
            n=mw[:3,:3]@np.array(p.normal); n/=np.linalg.norm(n)
            c=mw@np.append(np.array(p.center),1)
            if n[2]>0.7:
                key=(round(c[2],1), me.materials[p.material_index].name)
                a=up.setdefault(key,[0,0.0]); a[0]+=1
                sc=np.linalg.det(mw[:3,:3])**(1/3)
                a[1]+=p.area*abs(np.linalg.det(mw[:3,:3]))**(2/3)
        for k in sorted(up): print("  up-facing z %.1f %s: %d faces, %.1f m2"%(k[0],k[1],up[k][0],up[k][1]))
