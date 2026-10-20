import bpy,bmesh,numpy as np,math,json
from mathutils import Vector
from pathlib import Path
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_SleeveFinish.blend'));o=bpy.data.objects['Kit_Top'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');bm=bmesh.new();bm.from_mesh(o.data);deform=bm.verts.layers.deform.active;uv=bm.loops.layers.uv.active;rows=[]
def bridge(A,B):
 # Both loops sorted about the same angular seam. Zipper retains every old boundary vertex.
 i=j=0;na=len(A);nb=len(B)
 while i<na or j<nb:
  av=A[i%na];bv=B[j%nb];an=A[(i+1)%na];bn=B[(j+1)%nb];ta=A[(i+1)%na][0]+(2*math.pi if i+1>=na else 0);tb=B[(j+1)%nb][0]+(2*math.pi if j+1>=nb else 0)
  if i>=na or (j<nb and tb<ta):verts=[av[1],bv[1],bn[1]];j+=1
  else:verts=[av[1],bv[1],an[1]];i+=1
  face=bm.faces.new(verts);face.material_index=0;face.smooth=True
  angles=[coord[v][0] for v in verts]
  if max(angles)-min(angles)>math.pi:angles=[a+2*math.pi if a<0 else a for a in angles]
  for loop,angle in zip(face.loops,angles):loop[uv].uv=(angle*.08,coord[loop.vert][1]*3)
coord={}
for side in ['Left','Right']:
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;axis=(rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local-a).normalized();cut=a+axis*.115;e1=axis.cross(Vector((0,1,0))).normalized();e2=axis.cross(e1);group=o.vertex_groups[side+'UpperArm'].index
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=cut,plane_no=axis,clear_inner=False,clear_outer=False)
 delete=[v for v in bm.verts if v.co.x*a.x>0 and abs(v.co.x)>.205 and v.co.z>1.10 and (v.co-cut).dot(axis)>1e-6];bmesh.ops.delete(bm,geom=delete,context='VERTS');edges=[e for e in bm.edges if e.is_boundary and all(abs((v.co-cut).dot(axis))<2e-5 and abs(v.co.x)>.205 and v.co.x*a.x>0 and v.co.z>1.10 for v in e.verts)];adj={}
 for e in edges:
  x,y=e.verts;adj.setdefault(x,set()).add(y);adj.setdefault(y,set()).add(x)
 if any(len(v)!=2 for v in adj.values()):raise ValueError('Cuff boundary is not closed')
 seen=set();loops=[]
 for v in adj:
  if v in seen:continue
  q=[v];seen.add(v);ids=[]
  while q:
   z=q.pop();ids.append(z)
   for n in adj[z]:
    if n not in seen:seen.add(n);q.append(n)
  loops.append(ids)
 if len(loops)!=2:raise ValueError('Expected outer and inner cuff boundary')
 loops.sort(key=lambda loop:-np.mean([(v.co-cut).length for v in loop]));outer=loops[0];angles=np.array([math.atan2((v.co-cut).dot(e2),(v.co-cut).dot(e1)) for v in outer]);radius=np.array([(v.co-cut).length for v in outer])
 def basis(t):return np.stack([np.ones_like(t)]+[fn(k*t) for k in range(1,5) for fn in [np.cos,np.sin]],axis=-1)
 fit=np.linalg.lstsq(basis(angles),radius,rcond=None)[0]
 ends=[]
 for layer,loop in enumerate(loops):
  ordered=[]
  for v in loop:
   d=v.co-cut;angle=math.atan2(d.dot(e2),d.dot(e1));ordered.append((angle,v));coord[v]=(angle,.115);v[deform].clear();v[deform][group]=1
  ordered.sort(key=lambda pair:pair[0]);previous=ordered
  for s,offset in ([(.122,.0008),(.133,.0011),(.138,0)] if layer==0 else [(.122,-.0032),(.133,-.0032),(.138,-.0020)]):
   ring=[]
   for theta in np.linspace(-math.pi,math.pi,96,endpoint=False):
    r=float(basis(np.array(theta))@fit)+offset;v=bm.verts.new(a+axis*s+(e1*math.cos(theta)+e2*math.sin(theta))*r);v[deform][group]=1;coord[v]=(float(theta),s);ring.append((float(theta),v))
   bridge(previous,ring);previous=ring
  ends.append(previous)
 bridge(ends[0],ends[1]);rows.append({'side':side,'oldBoundaryLoops':[len(x) for x in loops],'newRingSamples':96,'cuffWidthMm':23,'meanRadiusMm':float(fit[0]*1000)})
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update();bpy.context.view_layer.objects.active=o;o.select_set(True)
if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_CuffRebuilt.blend'));bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'cuff-rebuilt-source.json').write_text(json.dumps(rows,indent=2));print(rows,flush=True)
j=json.loads((w/'sleeve-finish-source-queue.json').read_text());j[0]['name']='character-finish32-cuff-rebuilt-source';j[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'cuff-rebuilt-source');(w/'cuff-rebuilt-source-queue.json').write_text(json.dumps(j,indent=2))
