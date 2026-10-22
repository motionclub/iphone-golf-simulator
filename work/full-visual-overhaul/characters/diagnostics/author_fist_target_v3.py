import bpy,bmesh,pathlib,sys,math,json
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update();rest=[v.co.copy() for v in body.data.vertices];groups={g.index:g.name for g in body.vertex_groups};bodyToRig=rig.matrix_world.inverted()@body.matrix_world;rigToBody=bodyToRig.inverted();skin={b.name:rigToBody@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@bodyToRig for b in rig.data.bones}
if not body.data.shape_keys:body.shape_key_add(name='Basis',from_mix=False)
report={}
def sphere(point,radius,parts):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=point);o=bpy.context.object;o.scale=radius;parts.append(o)
def capsule(a,b,radius,parts):
 d=b-a;bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=radius,radius2=radius*.95,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized());parts.append(o);sphere(a,(radius,)*3,parts);sphere(b,(radius*.95,)*3,parts)
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@bodyToRig;P=rig.pose.bones[side+'Hand'].matrix.inverted();toBody=rigToBody@rig.pose.bones[side+'Hand'].matrix;parts=[]
 mcps=[P@rig.pose.bones[side+d+'Proximal'].head for d in ('Index','Middle','Ring','Little')];cx=sum(p.x for p in mcps)/4;top=sum(p.y for p in mcps)/4;width=(max(p.x for p in mcps)-min(p.x for p in mcps))/2+(.011 if sex=='Male' else .010)
 sphere(Vector((cx,(.04+top)*.5,0)),(width,(top-.04)*.60,.016 if sex=='Male' else .0145),parts)
 # The fist's palm front is filled and rounded; overlapping phalanges are united
 # into one continuous volume rather than leaving hidden internal cap triangles.
 for index,d in enumerate(('Index','Middle','Ring','Little','Thumb')):
  ns=[side+d+j for j in ('Proximal','Intermediate','Distal')];points=[P@rig.pose.bones[n].head for n in ns]+[P@rig.pose.bones[ns[-1]].tail];radius=([.0075,.008,.007,.0056,.0100] if sex=='Male' else [.005,.0052,.005,.0045,.0085])[index]
  for k,(a,b) in enumerate(zip(points,points[1:])):capsule(a,b,radius*(1-k*.08),parts)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();target=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);world=target.matrix_world.copy()
 for v in target.data.vertices:v.co=world@v.co
 target.matrix_world=Matrix.Identity(4);rem=target.modifiers.new('Fist volume union','REMESH');rem.mode='VOXEL';rem.voxel_size=.001;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name);smooth=target.modifiers.new('Soft closed knuckles','SMOOTH');smooth.factor=.45;smooth.iterations=5;bpy.ops.object.modifier_apply(modifier=smooth.name)
 bv=BVHTree.FromPolygons([v.co for v in target.data.vertices],[list(p.vertices) for p in target.data.polygons],all_triangles=False);key=body.shape_key_add(name='Hero_Fist_'+side,from_mix=False);count=0;maximum=0
 for i,v in enumerate(body.data.vertices):
  weights={groups[g.group]:g.weight for g in v.groups if g.weight>.000001};sideWeight=sum(w for n,w in weights.items() if n==side+'Hand' or n.startswith(side) and any(d in n for d in ('Thumb','Index','Middle','Ring','Little')));ph=H@rest[i]
  if sideWeight<.8 or ph.y<.041:continue
  m=Matrix(((0,0,0,0),)*4)
  for n,w in weights.items():
   if n in skin:m+=w*skin[n]
  if abs(m.determinant())<.00001:continue
  actual=m@rest[i];point=P@bodyToRig@actual;hit=bv.find_nearest(point)
  if hit[0] is None:continue
  weight=max(0,min(1,(ph.y-.041)/.010));desired=toBody@point.lerp(hit[0],weight);key.data[i].co=m.inverted()@desired;count+=1;maximum=max(maximum,(actual-desired).length)
 key.value=1;target.name='Editable_'+side+'_ClosedFistTarget';target.hide_render=True;target.hide_viewport=True;report[side]={'vertices':count,'maxPosedCorrectionMetres':maximum}
 # Move editable target from Hand coordinates into the same body coordinate space.
 target.matrix_world=body.matrix_world@toBody
bpy.context.view_layer.update();out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));(R/f'proof/full-visual-overhaul/characters/fist-target-v3-{sex}.json').write_text(json.dumps(report,indent=2));print('FIST_TARGET_V3',sex,report,flush=True)
