import sys, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
ps=sorted({(i.name,i.filepath) for i in bpy.data.images if i.filepath})
for n,p in ps[:6]: print("IMG",n,p)
print("IMGCOUNT",len(ps), "relative:",sum(1 for n,p in ps if p.startswith("//")))
