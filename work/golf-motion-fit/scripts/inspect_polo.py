import bpy,json,sys
s=sys.argv[-1];p=bpy.data.objects['Golf_Polo'];r=bpy.data.objects['Rig_'+s];sc=bpy.context.scene
print('MODIFIERS',[(m.name,m.type,m.show_viewport,m.show_render) for m in p.modifiers]);print('COUNTS',len(p.data.vertices),len(p.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().vertices))
r.animation_data.action=bpy.data.actions['Drive_'+s+'_RH'];p.data.shape_keys.animation_data.action=bpy.data.actions['Drive_'+s+'_RH_Golf_Polo_Correctives'];sc.frame_set(186);bpy.context.view_layer.update();print('VALUES',[(k.name,k.value) for k in p.data.shape_keys.key_blocks]);print('SLOTS',p.data.shape_keys.animation_data.action_slot)
print('MAT',[(m.name, sum(1 for poly in p.data.polygons if poly.material_index==i)) for i,m in enumerate(p.data.materials)])
