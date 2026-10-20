"""Golf-specific construction on the immutable current hero, with local weight fields.
Run on a completed animation master, not the source/rollback file.
"""
import bpy,bmesh,ast,sys,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
W=Path(__file__).resolve().parents[1];R=W.parents[1];SEX=sys.argv[-1];FEMALE=SEX=='Female'
rig=bpy.data.objects['Rig_'+SEX];body=bpy.data.objects['Body_'+('F' if FEMALE else 'M')];sc=bpy.context.scene
def fingerprint(o):return hashlib.sha256(repr(([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
before={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Body_','Face_'))}
rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
bone_names={b.name for b in rig.data.bones};body_groups={g.index:g.name for g in body.vertex_groups};made=[]
kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance()
def golf_material(kind):
 name='Golf_'+kind;m=bpy.data.materials.get(name)
 if not m:m=bpy.data.materials.new(name)
 m.use_nodes=True
 color={'Main':(.85,.85,.85),'Bottom':(.006,.007,.008),'Trim':(.003,.003,.003),'Glove':(.85,.85,.85),'Sole':(.006,.006,.007),'Buckle':(.48,.50,.51)}[kind]
 m.diffuse_color=(*color,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=.75 if kind!='Buckle' else .35
 return m
mats={kind:golf_material(kind) for kind in ['Main','Bottom','Trim','Glove','Sole','Buckle']}
# Reuse the draft's body-lineage lower shell and real seams, while replacing its
# silhouette / waistband / weights. Nothing executes the old draft build.
tree=ast.parse((R/'work/golf-look/scripts/build_golf_draft.py').read_text())
helpers={'activate','apply','bind','finish','mesh','tube','lower_shell','copied','cube','front_y'}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in helpers:
  if node.name=='front_y':node.args.defaults=[ast.Constant(None),ast.Constant(0)]
  exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<lineage construction>','exec'))

# The body carries mixed pelvis/torso weights at the groin. Height and the
# rest-pose leg envelope select the complete shell; a bone threshold omits it.
def lower_shell(name,hem,waist,ratio=.5,ease=.018):
 keep={v.index for v in body.data.vertices if .04<v.co.z<waist+.075 and abs(v.co.x)<.33 and sum(g.weight for g in v.groups if any(t in body_groups[g.group] for t in ['Arm','Shoulder','Hand','Thumb','Index','Middle','Ring','Little']))<.55}
 polys=[p for p in body.data.polygons if all(i in keep for i in p.vertices)]
 used=sorted({i for p in polys for i in p.vertices});remap={i:j for j,i in enumerate(used)}
 def offset(v):
  if name!='Golf_Trousers':return ease
  crotch=math.exp(-(abs(v.co.x)/.070)**4)*smooth((v.co.z-.60)/.08)*(1-smooth((v.co.z-.94)/.05))
  return min(ease*(1-crotch)+.003*crotch,ease*(1-smooth((v.co.z-.90)/.07))+.006*smooth((v.co.z-.90)/.07))
 o=mesh(name,[tuple(body.data.vertices[i].co+body.data.vertices[i].normal*offset(body.data.vertices[i])) for i in used],[tuple(remap[i] for i in p.vertices) for p in polys],mats['Bottom'],source_indices=used)
 bm=bmesh.new();bm.from_mesh(o.data)
 for z,normal in [(hem,(0,0,1)),(waist,(0,0,-1))]:
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=normal,clear_inner=True,dist=.00001)
 bm.to_mesh(o.data);bm.free()
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 dec=o.modifiers.new('Golf shell budget','DECIMATE');dec.ratio=ratio;apply(o,dec)
 rows=[]
 for v in o.data.vertices:
  row={o.vertex_groups[g.group].name:g.weight for g in v.groups if o.vertex_groups[g.group].name in ['Hips','Spine','Chest','UpperChest','LeftUpperLeg','RightUpperLeg','LeftLowerLeg','RightLowerLeg','LeftFoot','RightFoot']}
  if not row:row=waist_field(v.co)
  rows.append(row)
 set_weights(o,rows)
 return o

def weights(o,index):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[index].groups if o.vertex_groups[g.group].name in bone_names}
waistKD=KDTree(sum(1 for v in body.data.vertices if .88<v.co.z<1.055 and sum(g.weight for g in v.groups if body_groups[g.group] in ['Hips','Spine','Chest'])>.55))
for v in body.data.vertices:
 if .88<v.co.z<1.055 and sum(g.weight for g in v.groups if body_groups[g.group] in ['Hips','Spine','Chest'])>.55:waistKD.insert(v.co,v.index)
waistKD.balance()
def waist_field(p):
 out={}
 for _,i,d in waistKD.find_n(p,1):
  for g in body.data.vertices[i].groups:
   name=body_groups[g.group]
   if name in ['Hips','Spine','Chest','UpperChest','LeftUpperLeg','RightUpperLeg']:out[name]=out.get(name,0)+g.weight/max(d,.001)**2
 total=sum(out.values());return {n:v/total for n,v in out.items()}
def set_weights(o,rows):
 for vg in list(o.vertex_groups):o.vertex_groups.remove(vg)
 groups={n:o.vertex_groups.new(name=n) for n in bone_names}
 for i,row in enumerate(rows):
  row=dict(sorted(((n,w) for n,w in row.items() if w>1e-6),key=lambda p:p[1],reverse=True)[:4]);total=sum(row.values())
  if total<=0:raise RuntimeError('Unweighted '+o.name)
  for n,w in row.items():groups[n].add([i],w/total,'REPLACE')
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def attach(o):
 o.parent=rig;o.matrix_world=Matrix.Identity(4)
 for m in o.modifiers:
  if m.type=='ARMATURE':m.object=rig
 if not any(m.type=='ARMATURE' for m in o.modifiers):o.modifiers.new('Hero region weights','ARMATURE').object=rig
 o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 if o not in made:made.append(o)

delete=['Golf_Polo','Golf_Trousers','Golf_PleatedSkort','Golf_InnerShorts','Golf_Belt']
for o in list(bpy.data.objects):
 if o.name in delete or o.name.startswith(('Golf_PoloReference_', 'Golf_Hair_', 'Golf_BeltLoop_','Golf_Buckle_','Golf_Pocket','Golf_Shoe_','Golf_Sock_','Golf_Top','Golf_SaddlePanel_','Golf_Nub_')):bpy.data.objects.remove(o,do_unlink=True)

# Low and high approved tennis construction is copied, never edited in place.
with bpy.data.libraries.load(str(W/f'inputs/{SEX}_Approved.blend'),link=False) as (src,dst):
 dst.objects=[n for n in src.objects if n in ['Kit_Top','Kit_Shoe_L','Kit_Shoe_R','Kit_Sock_L','Kit_Sock_R'] or n in ['Kit_Top_High','Kit_Shoe_L_High','Kit_Shoe_R_High']]
for o in dst.objects:
 if o is not None:
  sc.collection.objects.link(o)
  name=o.name.split('.')[0];o.name='Golf_'+name[4:]
  if name.endswith('_High'):
   o.hide_render=True;o.hide_set(True);continue
  attach(o)
  if 'Shoe' in o.name:
   # Preserve real panels/eyelets/laces. Their high construction gets re-baked.
   dec=o.modifiers.new('Golf mobile shoe budget','DECIMATE');dec.ratio=.61 if FEMALE else .67;apply(o,dec)
  if 'Sock' in o.name and not FEMALE:
   bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,.17),plane_no=(0,0,-1),clear_inner=True,dist=1e-6);bm.to_mesh(o.data);bm.free()

polo=next(o for o in made if o.name=='Golf_Top');polo.name='Golf_Polo'
made.remove(polo)
exec(compile((W/'scripts/rebuild_polo_shell.py').read_text(),'rebuild_polo_shell.py','exec'),{})
polo=bpy.data.objects['Golf_Polo'];attach(polo)
rows=[]
for v in polo.data.vertices:
 # A consistent four-bone field prevents influence truncation from switching
 # an arm weight to a leg weight across a short fabric edge.
 row={}
 side='Left' if v.co.x>0 else 'Right'
 for n,w in weights(polo,v.index).items():
  target=(side+'UpperArm') if ('Arm' in n and n.startswith(side)) else 'UpperChest' if n in ['Chest','UpperChest','Neck','LeftShoulder','RightShoulder'] else 'Spine' if n=='Spine' else 'Hips'
  row[target]=row.get(target,0)+w
 armMass=sum(w for n,w in weights(polo,v.index).items() if 'Arm' in n or 'Shoulder' in n)
 t=smooth((1.055-v.co.z)/.095)*(1-smooth((armMass-.1)/.4))
 if t:
  wf={}
  for n,w in waist_field(v.co).items():
   target='UpperChest' if n in ['Chest','UpperChest'] else 'Spine' if n=='Spine' else 'Hips'
   wf[target]=wf.get(target,0)+w
  row={n:row.get(n,0)*(1-t)+wf.get(n,0)*t for n in set(row)|set(wf)}
 rows.append(row)
# Smooth the garment's own torso/arm weight field across neighboring vertices.
# The locked body's sharp armpit weight gradient is unsuitable for a fabric panel.
adj=[[] for v in polo.data.vertices]
for edge in polo.data.edges:
 a,b=edge.vertices;adj[a].append(b);adj[b].append(a)
for iteration in range(160):
 updated=[]
 for i,row in enumerate(rows):
  if not adj[i] or polo.data.vertices[i].co.z<1.035:updated.append(row);continue
  average={}
  for j in adj[i]:
   for n,w in rows[j].items():average[n]=average.get(n,0)+w/len(adj[i])
  updated.append({n:.5*row.get(n,0)+.5*average.get(n,0) for n in set(row)|set(average)})
 rows=updated
# Finish the local tuck with the same pelvis field as the adjacent waistband.
# Sleeve cuffs retain their region weights even when they rest near the waist.
for i,row in enumerate(rows):
 v=polo.data.vertices[i];armMass=sum(w for n,w in weights(polo,i).items() if 'Arm' in n or 'Shoulder' in n)
 t=smooth((1.020-v.co.z)/.040)*(1-smooth((armMass-.1)/.3))
 if t:
  wf=waist_field(v.co);rows[i]={n:row.get(n,0)*(1-t)+wf.get(n,0)*t for n in set(row)|set(wf)}
set_weights(polo,rows)

waist=.985 if FEMALE else .976
if not FEMALE:
 bottom=lower_shell('Golf_Trousers',.116,waist,ratio=.55,ease=.020);finish(bottom,mats['Bottom'],thickness=.0022,keep_weights=True)
 rows=[]
 for v in bottom.data.vertices:
  w=weights(bottom,v.index);t=smooth((v.co.z-.875)/.075)
  if t:
   wf=waist_field(v.co);w={n:w.get(n,0)*(1-t)+wf.get(n,0)*t for n in set(w)|set(wf)}
  rows.append(w)
 set_weights(bottom,rows)
 # Real pocket bags and lips copied from approved construction proportions.
 for side in [-1,1]:
  pts=[]
  for j in range(16):
   q=Vector((side*(.11+.095*j/15),0,.945-.105*j/15));q.y=front_y(q.z,bottom,x=q.x)-.001;pts.append(q)
  tube('Golf_PocketWelts_'+str(side),pts,.0012,mats['Bottom'],allowed=['Hips','Spine','LeftUpperLeg','RightUpperLeg']) if False else tube('Golf_PocketWelts_'+str(side),pts,.0012,mats['Bottom'])
else:
 knee=float((rig.data.bones['LeftLowerLeg'].head_local.z+rig.data.bones['RightLowerLeg'].head_local.z)/2)
 # Knee joint centre + kneecap upper radius + 25 mm hem clearance.
 hem=knee+.045;ns=144;nr=17;verts=[];faces=[]
 eligible=[v for v in body.data.vertices if hem-.03<v.co.z<waist+.035 and abs(v.co.x)<.32 and sum(g.weight for g in v.groups if body_groups[g.group] in ['Hips','Spine','LeftUpperLeg','RightUpperLeg'])>.55]
 cloud=np.array([tuple(v.co) for v in eligible])
 for j,z in enumerate(np.linspace(waist,hem,nr)):
  t=j/(nr-1);near=cloud[np.abs(cloud[:,2]-z)<.020]
  if len(near)<15:near=cloud[np.argsort(abs(cloud[:,2]-z))[:100]]
  cy=float((near[:,1].min()+near[:,1].max())/2)
  for i in range(ns):
   a=2*math.pi*i/ns;dir=np.array([math.cos(a),math.sin(a)])
   # Convex pelvis/thigh envelope in the standing rest pose. Clearance at the
   # actual waist is 4 mm; only the lower skirt has movement and pleat allowance.
   centered=near[:,:2]-[0,cy];radial=np.linalg.norm(centered,axis=1);along=centered@dir;across=abs(centered[:,0]*dir[1]-centered[:,1]*dir[0])
   angular=(along>0)&(across/np.maximum(radial,1e-9)<math.sin(math.radians(4)))
   radius=max(float(radial[angular].max()) if angular.any() else float(along.max()),.02)
   # Below the pelvis the cloth spans the two thighs. The convex silhouette
   # prevents the old radial sampler from following the inner-leg gap.
   rx=float(abs(centered[:,0]).max());ry=float(abs(centered[:,1]).max())
   ellipse=1/math.sqrt((dir[0]/max(rx,.02))**2+(dir[1]/max(ry,.02))**2)
   bridge=smooth((.86-z)/.12);radius=radius*(1-bridge)+ellipse*bridge
   r=radius+.006+.020*smooth(t/.5)+.008*t
   pleat=.007*smooth(t/.25)*(1-math.cos(a*18))*.5
   verts.append((dir[0]*(r+pleat),cy+dir[1]*(r+pleat),float(z)))
 for j in range(nr-1):
  for i in range(ns):faces.append((j*ns+i,(j+1)*ns+i,(j+1)*ns+(i+1)%ns,j*ns+(i+1)%ns))
 bottom=mesh('Golf_PleatedSkort',verts,faces,mats['Bottom'],thickness=.002)
 rows=[]
 for v in bottom.data.vertices:
  t=smooth((waist-.075-v.co.z)/(waist-.075-hem));wf=waist_field(Vector((v.co.x,v.co.y,max(v.co.z,.92))))
  left=smooth((v.co.x+.055)/.11);leg=.56*t
  row={n:w*(1-leg) for n,w in wf.items()};row['LeftUpperLeg']=leg*left;row['RightUpperLeg']=leg*(1-left);rows.append(row)
 set_weights(bottom,rows)
 inner=lower_shell('Golf_InnerShorts',hem+.065,waist,ratio=.40,ease=.006);finish(inner,mats['Bottom'],thickness=.0015,keep_weights=True)

# Belt/loops use exactly the same adjacent waistband weight field.
ns=144;verts=[];faces=[];waistRows=[]
for z in [waist-.036,waist+.003]:
 near=np.array([tuple(v.co) for v in body.data.vertices if abs(v.co.z-z)<.015 and sum(g.weight for g in v.groups if body_groups[g.group] in ['Hips','Spine','Chest'])>.6]);cy=float((near[:,1].min()+near[:,1].max())/2);centered=near[:,:2]-[0,cy]
 for i in range(ns):
  a=2*math.pi*i/ns;direction=np.array([math.cos(a),math.sin(a)]);radial=np.linalg.norm(centered,axis=1);along=centered@direction;across=abs(centered[:,0]*direction[1]-centered[:,1]*direction[0]);angular=(along>0)&(across/np.maximum(radial,1e-9)<math.sin(math.radians(4)))
  radius=float(radial[angular].max()) if angular.any() else float(along.max());xy=direction*(radius+.009)+[0,cy];p=Vector((xy[0],xy[1],z));verts.append(tuple(p));waistRows.append(waist_field(p))
for i in range(ns):faces.append((i,(i+1)%ns,(i+1)%ns+ns,i+ns))
belt=mesh('Golf_Belt',verts,faces,mats['Trim'],thickness=.002);set_weights(belt,[waist_field(v.co) for v in belt.data.vertices])
for j,i in enumerate([3,34,70,105,128]):
 p=Vector(verts[i]);tube('Golf_BeltLoop_'+str(j),[tuple(p+Vector((0,0,-.006))),tuple(p+Vector((0,0,.043)))],.003,mats['Bottom'])
yb=min(v[1] for v in verts)-.004;zb=waist-.018
for name,c,size in [('Top',(0,yb,zb+.012),(.034,.004,.003)),('Bottom',(0,yb,zb-.012),(.034,.004,.003)),('Left',(-.016,yb,zb),(.003,.004,.026)),('Right',(.016,yb,zb),(.003,.004,.026)),('Tongue',(0,yb,zb),(.0025,.004,.025))]:cube('Golf_Buckle_'+name,c,size,mats['Buckle'],bevel=.0008)
for o in made:
 if o.name.startswith(('Golf_Hair_', 'Golf_BeltLoop_','Golf_Buckle_','Golf_Pocket')):set_weights(o,[waist_field(v.co) for v in o.data.vertices])

# Local garment corrections. Four positive coefficients distinguish each side.
correctives=['GolfHipTwistLeft','GolfHipTwistRight','GolfThighLiftLeft','GolfThighLiftRight']
for o in made:
 if not (o==polo or o==bottom or o.name.startswith(('Golf_Belt','Golf_Buckle','Golf_InnerShorts'))):continue
 o.shape_key_add(name='Basis')
 for name in correctives:
  shape=o.shape_key_add(name=name,from_mix=False)
  for point,base in zip(shape.data,o.data.shape_keys.key_blocks['Basis'].data):point.co=base.co
  sgn=1 if name.endswith('Left') else -1
  for v in o.data.vertices:
   p=shape.data[v.index].co
   if 'HipTwist' in name:
    amount=.0025*math.exp(-((v.co.z-(waist-.015))/.060)**2)*smooth((sgn*v.co.x+.04)/.08)
    radial=Vector((v.co.x,v.co.y+.04,0))
    if radial.length:p+=radial.normalized()*amount
   elif o==bottom and FEMALE:
    side=smooth((sgn*v.co.x+.06)/.12);lower=smooth((waist-.08-v.co.z)/.20);front=smooth((-v.co.y+.06)/.18)
    p.y-=.070*side*lower*front;p.z+=.008*side*lower*front
   elif not FEMALE and o==bottom:
    side=smooth((sgn*v.co.x+.03)/.06);amount=.007*side*math.exp(-((v.co.z-.76)/.11)**2)
    p.y-=amount*smooth((-v.co.y+.04)/.12)

# Fit head accessories radially to actual head/hair; attachment stays rigid Head.
headCloud=np.array([tuple(v.co) for v in body.data.vertices if sum(g.weight for g in v.groups if body_groups[g.group]=='Head')>.8])
hairSource=bpy.data.objects.get('Hair_F') if FEMALE else None
hair=None
if hairSource is not None:
 # A separate compatible visibility variant keeps the original mesh reversible.
 from mathutils.bvhtree import BVHTree
 points=[v.co.copy() for v in body.data.vertices]
 eligible={v.index for v in body.data.vertices if sum(g.weight for g in v.groups if body_groups[g.group]=='Head')>.8}
 polygons=[list(p.vertices) for p in body.data.polygons if all(i in eligible for i in p.vertices)]
 tree=BVHTree.FromPolygons(points,polygons)
 hair=hairSource.copy();hair.data=hairSource.data.copy();sc.collection.objects.link(hair);hair.name='Golf_Hair_Visor';hair.parent=rig;hair.parent_type='OBJECT';hair.parent_bone='';hair.matrix_parent_inverse=Matrix.Identity(4);hair.matrix_basis=Matrix.Identity(4)
 for v in hair.data.vertices:
  nearest,normal,_,distance=tree.find_nearest(v.co)
  signed=(v.co-nearest).dot(normal)
  if signed<.008:v.co+=normal*(.008-signed)
 for modifier in list(hair.modifiers):hair.modifiers.remove(modifier)
 set_weights(hair,[{'Head':1} for _ in hair.data.vertices]);attach(hair)
 hairSource.hide_render=True;hairSource.hide_viewport=True;hairSource['GolfVisibilityVariant']='original-preserved'
 hair['GolfVisibilityVariant']='visor-compatible'
 if hair is not None:headCloud=np.concatenate([headCloud,np.array([tuple(v.co) for v in hair.data.vertices])])
exec(compile((W/'scripts/add_hair_underlay.py').read_text(),'add_hair_underlay.py','exec'),{})
if FEMALE:attach(bpy.data.objects['Golf_Hair_Underlay'])
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith(('Golf_Cap','Golf_Visor','Golf_CurvedBrim','Golf_BrimStitch')):continue
 for v in o.data.vertices:
  p=v.co;near=headCloud[abs(headCloud[:,2]-p.z)<.012]
  if not len(near):continue
  center=np.array([0,-.035]);direction=np.array([p.x,p.y])-center;length=np.linalg.norm(direction)
  if length<.005:continue
  direction/=length;required=float(((near[:,:2]-center)@direction).max())+.008
  if length<required:p.x,p.y=center+direction*required
 set_weights(o,[{'Head':1.0} for _ in o.data.vertices]);attach(o)

for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Golf_Glove_'):
  attach(o);o.data.materials.clear();o.data.materials.append(mats['Glove']);o.hide_render=o.name=='Golf_Glove_Right'

exec(compile((W/'scripts/body_coverage.py').read_text(),'body_coverage.py','exec'),{'__name__':'__main__','__file__':str(W/'scripts/body_coverage.py')})
# Re-unwrap the new golf geometry; all material roles remain semantic/recolorable.
stats=[]
for o in made:
 if o.type!='MESH':continue
 activate(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 o.data.calc_loop_triangles();P=np.array([tuple(v.co) for v in o.data.vertices]);UV=np.array([tuple(u.uv) for u in o.data.uv_layers.active.data]);N=np.array([tuple(n.vector) for n in o.data.corner_normals]);TR=np.array([tuple(t.vertices) for t in o.data.loop_triangles]);TL=np.array([tuple(t.loops) for t in o.data.loop_triangles]);MI=np.array([t.material_index for t in o.data.loop_triangles])
 np.savez_compressed(W/f'data/{SEX}_{o.name}.npz',P=P,uv=UV,normal=N,tri=TR,triloops=TL,material=MI,materials=np.array([m.name for m in o.data.materials]))
 influences=max((len([g for g in v.groups if g.weight>1e-6]) for v in o.data.vertices),default=0);error=max((abs(sum(g.weight for g in v.groups)-1) for v in o.data.vertices),default=0)
 stats.append(dict(piece=o.name,triangles=len(TR),maxInfluences=influences,weightError=error))
assert before=={name:fingerprint(bpy.data.objects[name]) for name in before},'Locked body changed'
rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions[f'Drive_{SEX}_RH'];sc.frame_set(0)
(W/f'data/garments_{SEX}.json').write_text(json.dumps(dict(bodyUnchanged=True,waist=waist,hem=hem if FEMALE else .116,correctives=correctives,pieces=stats,triangles=sum(x['triangles'] for x in stats if not bpy.data.objects[x['piece']].hide_render),storedVariantTriangles=sum(x['triangles'] for x in stats)),indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Golf_{SEX}_Dressed.blend'),compress=True)
print('GARMENTS_COMPLETE',SEX,sum(x['triangles'] for x in stats),flush=True)
