import sys, numpy as np, bpy, bmesh
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ob=bpy.data.objects["DRESS_PATH_01"]; me=ob.data
bm=bmesh.new(); bm.from_mesh(me)
for f in bm.faces:
    if f.calc_area()<1e-8:
        print("ZERO", f.index, len(f.verts), [tuple(round(c,5) for c in v.co) for v in f.verts], "nz", f.normal.z, [len(e.link_faces) for e in f.edges])
# smallest 8 areas
a=sorted((f.calc_area(), f.index) for f in bm.faces)[:8]
print("SMALLEST", a)
