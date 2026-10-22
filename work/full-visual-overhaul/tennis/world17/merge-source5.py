from pathlib import Path
p=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/tennis/audience/tools/bake-tennis-audience.py');s=p.read_text()
s=s.replace("SKIN_BONES=['PELVIS','THIGH_L','SHIN_L','FOOT_L','THIGH_R','SHIN_R','FOOT_R']","SKIN_BONES=['PELVIS','THIGH_L','SHIN_L','FOOT_L','THIGH_R','SHIN_R','FOOT_R'];ALL_BONES=['BODY','HEAD','ARM_L','ARM_R']+SKIN_BONES")
s=s.replace("key=group_kind(names[group.group]);key=key if key in SKIN_BONES else 'PELVIS'", "key=group_kind(names[group.group]);key=key if key in SKIN_BONES else 'PELVIS'")
s=s.replace("  centre=(Vector(anchor['LeftUpperLeg'])+Vector(anchor['RightUpperLeg']))*.5\n  pelvis=", """  body_root=armature.edit_bones.new('BODY');body_root.head=(0,0,0);body_root.tail=(0,0,.15);bones['BODY']=body_root
  for part,source in [('HEAD','Neck'),('ARM_L','LeftUpperArm'),('ARM_R','RightUpperArm')]:
   bone=armature.edit_bones.new(part);bone.head=Vector(anchor[source]);bone.tail=bone.head+Vector((0,0,.15 if part=='HEAD' else -.25));bone.parent=body_root;bone.use_connect=False;bones[part]=bone
  centre=(Vector(anchor['LeftUpperLeg'])+Vector(anchor['RightUpperLeg']))*.5
  pelvis=""")
s=s.replace("bones['PELVIS']=pelvis\n  for side", "pelvis.parent=body_root;pelvis.use_connect=False;bones['PELVIS']=pelvis\n  for side")
at=s.index(" manifest.append",s.index(" if not SEATED:\n  armature="))
s=s[:at]+'''  # Merge the accepted rigid upper surfaces and continuous lower skin into
  # one renderer per active detail. Constant bone weights preserve every
  # upper vertex's exact rigid motion; lower weights retain the authored blends.
  for detail in ['near','far']:
   merged_vertices=[];merged_faces=[];merged_colours=[];merged_weights=[];old_objects=[]
   for part in OUTPARTS:
    object=objects[part] if detail=='near' else next(o for o in objects[part].children if '_FAR' in o.name)
    transform=root.matrix_world.inverted()@object.matrix_world;base=len(merged_vertices);mesh=object.data;palette=mesh.color_attributes['SpectatorPalette']
    merged_vertices.extend(transform@vertex.co for vertex in mesh.vertices);merged_faces.extend([base+v for v in polygon.vertices] for polygon in mesh.polygons)
    merged_colours.extend(tuple(palette.data[loop].color) for polygon in mesh.polygons for loop in polygon.loop_indices)
    for vertex in mesh.vertices:
     if part!='SKIN_LOWER':weights={part:1}
     else:weights={object.vertex_groups[group.group].name:group.weight for group in vertex.groups}
     merged_weights.append(weights)
    old_objects.append(object)
   mesh=bpy.data.meshes.new('Whole fitted visitor '+detail);mesh.from_pydata(merged_vertices,[],merged_faces);mesh.update();mesh.materials.append(mat)
   palette=mesh.color_attributes.new(name='SpectatorPalette',type='FLOAT_COLOR',domain='CORNER')
   for index,colour_value in enumerate(merged_colours):palette.data[index].color=colour_value
   for polygon in mesh.polygons:polygon.use_smooth=True
   object=bpy.data.objects.new('VISITOR_MESH'+('_FAR' if detail=='far' else ''),mesh);bpy.context.collection.objects.link(object);object.parent=root;object.hide_render=detail=='far'
   groups={name:object.vertex_groups.new(name=name) for name in ALL_BONES}
   for index,weights in enumerate(merged_weights):
    for name,weight in weights.items():groups[name].add([index],weight,'REPLACE')
   modifier=object.modifiers.new('Eleven cosmetic sporting visitor joints','ARMATURE');modifier.object=leg_rig;modifier.use_deform_preserve_volume=False
  # Remove the export-only intermediate rigid parts after both detail meshes
  # have been constructed. The original source files are read-only.
  for object in root.children.copy():
   if object.type=='MESH' and not object.name.startswith('VISITOR_MESH'):
    for child in object.children.copy():bpy.data.objects.remove(child,do_unlink=True)
    bpy.data.objects.remove(object,do_unlink=True)
'''+s[at:]
s=s.replace("visitors use only seven cosmetic lower-body joints.", "visitors use eleven cosmetic joints: seven continuous lower-body joints and four exact rigid upper transforms.")
p.write_text(s)
