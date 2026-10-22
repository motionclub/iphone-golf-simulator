"""Repair only draft lower garments; preserve all locked hero data."""
import bpy,bmesh,ast,sys,json,math,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
W=Path(__file__).resolve().parents[1];SEX=sys.argv[-1];FEMALE=SEX=='Female'
rig=bpy.data.objects['Rig_'+SEX];body=bpy.data.objects['Body_F' if FEMALE else 'Body_M'];sc=bpy.context.scene
p=Path(bpy.data.filepath);bk=W/'rollback/lower_sourcebind_r20'/p.name;bk.parent.mkdir(exist_ok=True)
if not bk.exists():shutil.copy2(p,bk)
rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance();bone_names={b.name for b in rig.data.bones};body_groups={g.index:g.name for g in body.vertex_groups};made=[]
mats={k:bpy.data.materials['Golf_'+k] for k in ['Main','Bottom','Trim','Glove','Sole','Buckle']}
# Reuse the existing draft construction helpers without running its build.
tree=ast.parse((W/'scripts/build_golf_draft.py').read_text())
helpers={'activate','apply','bind','finish','mesh','tube','lower_shell','front_y'}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in helpers:
  if node.name=='front_y':node.args.defaults=[ast.Constant(None),ast.Constant(0)]
  if node.name=='lower_shell':
   text=ast.unparse(node)
   insert="bind_attr = o.data.attributes.new('GolfSourceBind', 'FLOAT_VECTOR', 'POINT')\n    for j, i in enumerate(used):\n        bind_attr.data[j].vector = body.data.vertices[i].co\n    bm = bmesh.new()"
   text=text.replace('bm = bmesh.new()',insert,1)
   exec(text)
  else:
   exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<draft helpers>','exec'))
oldnames=['Golf_PleatedSkort','Golf_InnerShorts'] if FEMALE else ['Golf_Trousers']
for o in list(bpy.data.objects):
 if o.name in oldnames or o.name.startswith(('Golf_PocketBag_','Golf_PocketLip_','Golf_PocketRecess_')):bpy.data.objects.remove(o,do_unlink=True)
if FEMALE:
 sys.path.insert(0,str(W/'scripts'));from garment_fit import hip_envelope,support_ring
 # A short flared shell attached to Hips avoids the thigh-weight crease that
 # collapsed the previous skirt. The full eight-pose envelope controls clearance.
 cloud,env=hip_envelope(rig,body,W/'export/Golf_Female_SwingProof.blend')
 ns=64;zs=[.995,.970,.945,.920,.895,.870,.845,.820,.795];verts=[];faces=[];rows=[]
 for j,z in enumerate(zs):
  t=j/(len(zs)-1);points,count=support_ring(cloud,z,ns=ns,margin=.008+.005*t)
  # A small actual return fold inside the safe envelope; its base margin covers it.
  depth=.004*t*t
  for i,xy in enumerate(points):
   q=Vector((float(xy[0]),float(xy[1]),0));q-=q.normalized()*depth*(i%4 in [2,3]);verts.append((q.x,q.y,z))
  rows.append(dict(z=z,width=float(points[:,0].max()-points[:,0].min()),depth=float(points[:,1].max()-points[:,1].min()),samples=count))
 for j in range(len(zs)-1):
  for i in range(ns):faces.append(((j+1)*ns+i,(j+1)*ns+(i+1)%ns,j*ns+(i+1)%ns,j*ns+i))
 bottom=mesh('Golf_PleatedSkort',verts,faces,mats['Bottom'],'Hips',.002)
 inner=lower_shell('Golf_InnerShorts',.817,.995,ratio=.45,ease=.016);finish(inner,mats['Bottom'],thickness=.002,keep_weights=True)
 env.update(rings=rows,status='candidate short Hips shell; eight-pose collision and eye checks required')
 (W/'data/skirt_envelope_Female.json').write_text(json.dumps(env,indent=2)+'\n')
else:
 bottom=lower_shell('Golf_Trousers',.115,1.010,ratio=1.0,ease=.023)
 for v in bottom.data.vertices:
  if v.co.z<.145:
   t=max(0,min(1,(.145-v.co.z)/.03));v.co.z=(1-t)*v.co.z+t*(.118-.004*max(0,min(1,-v.co.y/.15)))
  if .145<v.co.z<.87:
   side='Left' if v.co.x>0 else 'Right';bone=rig.data.bones[side+('UpperLeg' if v.co.z>.48 else 'LowerLeg')]
   t=max(0,min(1,(v.co.z-bone.tail_local.z)/(bone.head_local.z-bone.tail_local.z)));x=bone.tail_local.x*(1-t)+bone.head_local.x*t
   if abs(v.co.x-x)<.015 and v.co.y<-.015:v.co.y-=.0022*(1-abs(v.co.x-x)/.015)
 finish(bottom,mats['Bottom'],thickness=.0022,keep_weights=True)
 # A fine recessed-looking opening with matching cloth lips. The continuous
 # shell beneath it closes the previous pose-dependent holes in the pocket bag.
 for side in [-1,1]:
  a=Vector((side*.115,0,.936));b=Vector((side*.212,0,.830));points=[]
  for j in range(16):
   q=a.lerp(b,j/15);q.y=front_y(q.z,bottom,x=q.x)-.0006;points.append(q)
  tube('Golf_PocketRecess_'+str(side),points,.0011,mats['Trim'])
  tube('Golf_PocketLip_'+str(side),[q+Vector((side*.0016,0,.001)) for q in points],.0005,mats['Bottom'])
 # Shoe proportions were already repaired in the preceding pass; no repeated
 # relative scaling or decimation of those work assets is applied here.
 for o in list(bpy.data.objects):
  if o.name.startswith('Golf_Nub_') and not o.get('golf_nub_budget'):
   for mod in list(o.modifiers):o.modifiers.remove(mod)
   dec=o.modifiers.new('Nub budget','DECIMATE');dec.ratio=.28;apply(o,dec)
   side='LeftFoot' if '_L_' in o.name else 'RightFoot';bind(o,rigid=side);o['golf_nub_budget']=True

for o in made:
 o.hide_render=False;activate(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions['ReadyIdle']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(p))
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Golf_') and not o.hide_render:
  o.data.calc_loop_triangles();rows.append(dict(name=o.name,tris=len(o.data.loop_triangles)))
(W/f'data/lower_lineage_{SEX}.json').write_text(json.dumps(dict(pieces=rows,visible_kit_tris=sum(x['tris'] for x in rows),status='candidate; not certified'),indent=2)+'\n')
print('LOWER LINEAGE',SEX,sum(x['tris'] for x in rows),flush=True)
