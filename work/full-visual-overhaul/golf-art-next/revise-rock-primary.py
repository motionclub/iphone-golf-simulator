from pathlib import Path
p=Path('work/full-visual-overhaul/golf-art-next/author-primary-forms.py');s=p.read_text();a=s.index('for variant in range(3):');b=s.index('# Overlapping curved broad leaves',a)
s=s[:a]+'''import bmesh
for variant in range(3):
 rng=random.Random(45000+variant)
 parts=[]
 def fracture_chunk(name,center,scale):
  verts=[]
  # A wall slab has four broad faces, fractured corners and a sloping crest.
  # Its ledges interrupt on one side; no complete horizontal ring.
  outline=[(-.62,-.32),(-.46,-.49),(.38,-.48),(.64,-.25),(.57,.36),(.30,.48),(-.44,.44),(-.65,.18)]
  for upper in [False,True]:
   for j,(x,y) in enumerate(outline):
    z=(.85+rng.random()*.15) if upper else 0
    x+=(rng.random()-.5)*.09+(variant-1)*z*.09
    y+=(rng.random()-.5)*.07+z*.06
    verts.append(tuple(Vector(center)+Vector((x*scale[0],y*scale[1],z*scale[2]))))
  # Selective shoulders create large oblique fractures in the outward plane.
  for x,y,z in [(-.38,-.53,.33),(.34,-.51,.57),(-.67,.10,.58),(.63,.20,.37)]:
   verts.append(tuple(Vector(center)+Vector((x*scale[0],y*scale[1],z*scale[2]))))
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[]);bm=bmesh.new();bm.from_mesh(me)
  bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
  bmesh.ops.dissolve_limit(bm,angle_limit=.12,verts=list(bm.verts),edges=list(bm.edges));bm.to_mesh(me);bm.free();me.update();me.materials.append(mats[6])
  ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
  bevel=ob.modifiers.new('Bounded worn corner bevel','BEVEL');bevel.width=.022;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.24;bevel.harden_normals=True
  normal=ob.modifiers.new('Broad planes with smooth arrises','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=60
  bpy.context.view_layer.objects.active=ob;ob.select_set(True)
  for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
  ob.select_set(False);parts.append(ob)
 fracture_chunk('BLUFF_'+str(variant),(0,0,0),(1,1,1))
 fracture_chunk('Offset lower geological shoulder',(.37,-.08,.015),(.62,.79,.46+rng.random()*.12))
 fracture_chunk('Interrupted upper fracture',(-.38,.06,.44+rng.random()*.11),(.58,.74,.32))
 for ob in bpy.context.selected_objects:ob.select_set(False)
 for ob in parts:ob.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=parts[0];ob.name='BLUFF_'+str(variant)
 # Use the same seven-slot palette contract as the foliage kit.
 ob.data.materials.clear()
 for m in mats:ob.data.materials.append(m)
 for f in ob.data.polygons:f.material_index=6
 col=ob.data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for c in col.data:c.color=(0,.28,0,1)
''' +s[b:];p.write_text(s)
