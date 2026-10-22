from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');p=R/'ArtDir/tennis/audience/tools/bake-tennis-audience.py';s=p.read_text()
a=s.index("R=Path(");b=s.index('\nskins=',a)
s=s[:a]+'''R=Path(__file__).resolve().parents[4];W=R/'ArtDir/tennis/audience/staging5';P=R/'proof/full-visual-overhaul/tennis/audience5';W.mkdir(parents=True,exist_ok=True);P.mkdir(parents=True,exist_ok=True)
SEATED='--seated' in sys.argv;ASSET='TennisSeatedHero3' if SEATED else 'TennisPromenadeHero3';cloth_cut=1.19
PARTS=['BODY','HEAD','ARM_L','ARM_R'] if SEATED else ['BODY','HEAD','ARM_L','ARM_R','THIGH_L','THIGH_R','SHIN_L','SHIN_R','FOOT_L','FOOT_R','SKIN_LOWER']
OUTPARTS=PARTS if SEATED else ['BODY','HEAD','ARM_L','ARM_R','SKIN_LOWER']
SKIN_BONES=['PELVIS','THIGH_L','SHIN_L','FOOT_L','THIGH_R','SHIN_R','FOOT_R']
from mathutils.kdtree import KDTree
'''+s[b:]
s=s.replace("   if src.name=='Kit_Bottom':return 'BODY'", "   if src.name=='Kit_Bottom':return 'BODY' if SEATED else 'SKIN_LOWER'")
s=s.replace("   if src.name.startswith('Kit_Shoe'):return ('FOOT_L' if src.name.endswith('_L') else 'FOOT_R') if not SEATED else 'BODY'", "   if src.name.startswith(('Kit_Shoe','Kit_Sock')) and not SEATED:return 'SKIN_LOWER'\n   if src.name.startswith('Kit_Shoe'):return 'BODY'")
s=s.replace("   if src.name=='Kit_Top' and part=='HEAD':return 'BODY'", "   if src.name=='Kit_Top' and part not in ['ARM_L','ARM_R']:return 'BODY'")
s=s.replace("    leg=leg_weight/len(poly.vertices)>.35", "    leg=leg_weight/len(poly.vertices)>.35\n    if leg and not SEATED:part='SKIN_LOWER'")
s=s.replace("    if part=='BODY' and centre.z<sock_top-.018:continue", "    if part in ['BODY','SKIN_LOWER'] and centre.z<sock_top-.018:continue\n    if part=='SKIN_LOWER' and centre.z>bottom_floor+.015:continue")
s=s.replace("'FOOT_R':200}[part]", "'FOOT_R':200,'SKIN_LOWER':1300}[part]")
s=s.replace(" if not near:\n  original=mesh;", " if not near and not name.startswith('Kit_Sock'):\n  original=mesh;")
s=s.replace("(100 if src.name.startswith('Kit_Shoe') else 40)", "(280 if src.name.startswith('Kit_Shoe') else 110)")
s=s.replace("   def snapshot(ob,count):return {'source':src.name,'part':part,'vertices':[list(v.co) for v in ob.data.vertices],'faces':[list(p.vertices) for p in ob.data.polygons],'roles':[roles[p.material_index] for p in ob.data.polygons],'triangles':count}",'''   def snapshot(ob,count):
    result={'source':src.name,'part':part,'vertices':[list(v.co) for v in ob.data.vertices],'faces':[list(p.vertices) for p in ob.data.polygons],'roles':[roles[p.material_index] for p in ob.data.polygons],'triangles':count}
    if part=='SKIN_LOWER':
     # Lower-body vertices remain one continuous weighted surface. Retain real
     # source skin blend weights through simplified fitted geometry. Footwear
     # is a complete closed sneaker bound to its ankle, never a split shell.
     constant='FOOT_'+('L' if src.name.endswith('_L') else 'R') if src.name.startswith('Kit_Shoe') else None
     tree=KDTree(len(coords));original_weights=[]
     for index,vertex in enumerate(m.vertices):
      tree.insert(coords[index],index);weights={}
      for group in vertex.groups:
       if group.group>=len(names):continue
       key=group_kind(names[group.group]);key=key if key in SKIN_BONES else 'PELVIS';weights[key]=weights.get(key,0)+group.weight
      if not weights:weights={'PELVIS':1}
      total=sum(weights.values());original_weights.append({key:value/total for key,value in weights.items()})
     tree.balance();all_weights=[]
     for vertex in ob.data.vertices:
      if constant:weights={constant:1}
      else:
       weights={}
       nearest=tree.find_n(vertex.co,4)
       for point,index,distance in nearest:
        influence=1/max(1e-5,distance)**2
        for key,value in original_weights[index].items():weights[key]=weights.get(key,0)+value*influence
       weights=dict(sorted(weights.items(),key=lambda item:-item[1])[:4]);total=sum(weights.values());weights={key:value/total for key,value in weights.items()}
      all_weights.append(weights)
     result['weights']=all_weights
    return result''')
s=s.replace("   else:\n    mod=far.modifiers.new('Distant fitted silhouette','DECIMATE');mod.ratio=.20;", "   else:\n    mod=far.modifiers.new('Distant fitted silhouette','DECIMATE');mod.ratio=.65 if part=='SKIN_LOWER' else .20;")
s=s.replace(" verts=[];faces=[];colors=[]\n for p in items:", " verts=[];faces=[];colors=[];weights=[]\n for p in items:")
s=s.replace("base=len(verts);verts.extend(p['vertices']);faces.extend", "base=len(verts);verts.extend(p['vertices']);weights.extend(p.get('weights',[{} for v in p['vertices']]));faces.extend")
s=s.replace(" mesh.calc_loop_triangles();return mesh,len(mesh.loop_triangles)\nfor i", " mesh.calc_loop_triangles();return mesh,len(mesh.loop_triangles),weights\nfor i")
s=s.replace(" for part in PARTS:\n  name=", " for part in OUTPARTS:\n  name=")
s=s.replace("mesh,n=make_piece(i,part,prepared[sex],pivot)","mesh,n,weights=make_piece(i,part,prepared[sex],pivot)")
s=s.replace("mesh,n=make_piece(i,part,far_prepared[sex],pivot)","mesh,n,far_weights=make_piece(i,part,far_prepared[sex],pivot)")
s=s.replace("  mesh,n,far_weights=", "  if part=='SKIN_LOWER':ob['source_weights']=json.dumps(weights)\n  mesh,n,far_weights=")
s=s.replace("far.hide_render=True\n manifest.append", "far.hide_render=True\n  if part=='SKIN_LOWER':far['source_weights']=json.dumps(far_weights)\n"+''' if not SEATED:
  armature=bpy.data.armatures.new('Seven cosmetic lower-body joints');leg_rig=bpy.data.objects.new('VISITOR_LEG_RIG',armature);bpy.context.collection.objects.link(leg_rig);leg_rig.parent=root
  bpy.context.view_layer.objects.active=leg_rig;leg_rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bones={}
  centre=(Vector(anchor['LeftUpperLeg'])+Vector(anchor['RightUpperLeg']))*.5
  pelvis=armature.edit_bones.new('PELVIS');pelvis.head=centre;pelvis.tail=centre+Vector((0,0,.15));bones['PELVIS']=pelvis
  for side,letter in [('Left','L'),('Right','R')]:
   for part,source,next_source in [('THIGH',side+'UpperLeg',side+'LowerLeg'),('SHIN',side+'LowerLeg',side+'Foot'),('FOOT',side+'Foot',None)]:
    name=part+'_'+letter;bone=armature.edit_bones.new(name);bone.head=Vector(anchor[source]);bone.tail=Vector(anchor[next_source]) if next_source else bone.head+Vector((0,-.13,-.045));bone.parent=bones['PELVIS' if part=='THIGH' else ('THIGH_'+letter if part=='SHIN' else 'SHIN_'+letter)];bone.use_connect=False;bones[name]=bone
  bpy.ops.object.mode_set(mode='OBJECT')
  for mesh_object in [objects['SKIN_LOWER'],next(o for o in objects['SKIN_LOWER'].children if o.name.startswith('SKIN_LOWER_FAR'))]:
   groups={name:mesh_object.vertex_groups.new(name=name) for name in SKIN_BONES}
   for index,weights in enumerate(json.loads(mesh_object['source_weights'])):
    for name,weight in weights.items():groups[name].add([index],weight,'REPLACE')
   del mesh_object['source_weights'];modifier=mesh_object.modifiers.new('Continuous hero-derived lower body','ARMATURE');modifier.object=leg_rig;modifier.use_deform_preserve_volume=True
 manifest.append''')
s=s.replace("object_types={'MESH','EMPTY'}", "object_types={'MESH','EMPTY','ARMATURE'}")
s=s.replace("Original hero sources untouched; all53 bones removed from exported crowd.", "Original hero sources untouched; seated figures have no rig; visitors use only seven cosmetic lower-body joints.")
p.write_text(s)
print(p)
