import bpy,sys
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    if o.type=="MESH":
        print("OBJ",o.name,len(o.data.vertices),[m.name for m in o.data.materials if m][:3])
