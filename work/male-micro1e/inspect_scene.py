import bpy,numpy as np
bpy.ops.wm.open_mainfile(filepath='baseline/HeroBase_Male_Silhouette.blend')
s=bpy.context.scene
print('ENGINE',s.render.engine,s.render.resolution_x,s.render.resolution_y,s.render.film_transparent,s.unit_settings.system,s.unit_settings.scale_length)
for o in bpy.data.objects:
    print(o.name,o.type,tuple(round(x,3) for x in o.location),o.hide_render, o.data.ortho_scale if o.type=='CAMERA' else '', [m.type for m in o.modifiers] if hasattr(o,'modifiers') else '')
me=bpy.data.objects['Body_M'].data
print('verts',len(me.vertices),'edges',len(me.edges),'faces',len(me.polygons),'quads',sum(1 for p in me.polygons if len(p.vertices)==4),'tris',sum(1 for p in me.polygons if len(p.vertices)==3))
print('uv',[u.name for u in me.uv_layers],'attrs',[a.name for a in me.attributes],'vgroups',[g.name for g in bpy.data.objects['Body_M'].vertex_groups])
print('mats',[m.name for m in me.materials])
print('smooth',sum(p.use_smooth for p in me.polygons))
