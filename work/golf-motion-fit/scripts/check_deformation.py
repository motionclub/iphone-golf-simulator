import bpy,sys,json
s=sys.argv[-1];r=bpy.data.objects['Rig_'+s];sc=bpy.context.scene
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Golf_Glove'):
  print('GLOVE',o.name,'parent',o.parent_type,tuple(o.matrix_world.translation),'mats',[(m.name,tuple(m.diffuse_color),tuple(m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value)) for m in o.data.materials],'mods',[(m.type,m.object.name if m.type=='ARMATURE' else None) for m in o.modifiers])
p=bpy.data.objects['Golf_Polo'];r.animation_data.action=bpy.data.actions['Drive_'+s+'_RH'];p.data.shape_keys.animation_data.action=bpy.data.actions['Drive_'+s+'_RH_Golf_Polo_Correctives'];sc.frame_set(80);bpy.context.view_layer.update();print('COEFFS',[(k.name,k.value) for k in p.data.shape_keys.key_blocks]);print('SHAPEDELTAS',[(k.name,max((a.co-b.co).length for a,b in zip(k.data,p.data.shape_keys.key_blocks[0].data))) for k in p.data.shape_keys.key_blocks])
