import bpy, sys
bpy.ops.wm.open_mainfile(filepath='baseline/HeroBase_Male_Silhouette.blend')
for n in ('Body_M','Face_M'):
    o=bpy.data.objects[n]; me=o.data
    print(n,'uv_layers',[u.name for u in me.uv_layers],'attrs',[a.name for a in me.attributes][:12],'color_attrs',[c.name for c in me.color_attributes])
