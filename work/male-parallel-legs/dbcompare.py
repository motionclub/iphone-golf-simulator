import sys, bpy
for path in sys.argv[sys.argv.index('--')+1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    out={}
    for attr in ('objects','meshes','materials','images','cameras','lights','collections','worlds','textures','node_groups','actions','armatures','curves','scenes'):
        c=getattr(bpy.data,attr)
        out[attr]=(len(c),sum(1 for x in c if getattr(x,'users',1)==0))
    print(path.split('/')[-1],out)
