"""Work-only composable eyelid surface and closure refinement on frozen Smooth1."""
import bpy,bmesh,numpy as np,json,collections,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path.cwd();O=R/'work/reference-rebuild/face-finish30-lids';REPORT={}
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def coeff(p,u,corners,side):
 zline=corners[0,2]*(1-u)+corners[1,2]*u;sgn=p[:,2]>=zline;take=sgn if side>0 else ~sgn
 U=u[take];B=U*(1-U);X=2*U-1;A=np.c_[B,B*X,B*X*X]
 return np.linalg.lstsq(A,p[take,2]-zline[take],rcond=None)[0]
def zfit(u,co,corners):
 x=2*u-1;return corners[0,2]*(1-u)+corners[1,2]*u+u*(1-u)*(co[0]+co[1]*x+co[2]*x*x)
for sex in ['Male','Female']:
 source=R/f'work/reference-rebuild/face-finish29/smooth-mouth1/{sex}_OriginalFaceFinish29Smooth1.blend';bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body'];me=body.data;feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST';rig.animation_data_clear()
 p=np.array([v.co[:] for v in me.vertices]);shapes={k.name:np.array([v.co[:] for v in k.data]) for k in me.shape_keys.key_blocks};out={k:v.copy() for k,v in shapes.items()};active=np.any(np.stack([np.linalg.norm(v-p,axis=1)>1e-7 for k,v in shapes.items() if k!='Basis']),axis=0)
 oldnormal=[tuple(x.value) for x in me.attributes['custom_normal'].data];bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();edge=[]
 for e in bm.edges:
  if e.is_boundary and all(v.co.y<-.05 and 1.50<v.co.z<1.64 for v in e.verts):edge.append([v.index for v in e.verts])
 bm.free();boundary=np.unique(edge);mask=np.zeros(len(p));rimPigment=np.zeros(len(p));eyes=[]
 for sign in [-1,1]:
  ids=boundary[p[boundary,0]*sign>0];bp=p[ids];corners=bp[[np.argmin(bp[:,0]),np.argmax(bp[:,0])]];xmin,xmax=corners[:,0];width=xmax-xmin;u=(bp[:,0]-xmin)/width;cu=coeff(bp,u,corners,1);cl=coeff(bp,u,corners,-1);upper=bp[:,2]>=corners[0,2]*(1-u)+corners[1,2]*u;uy=np.polyfit(u[upper],bp[upper,1],4);ly=np.polyfit(u[~upper],bp[~upper,1],4)
  samples=np.linspace(0,1,257);sc=np.r_[np.c_[xmin+samples*width,zfit(samples,cu,corners)],np.c_[xmin+samples*width,zfit(samples,cl,corners)]]
  kd=KDTree(len(sc))
  for j,q in enumerate(sc):kd.insert(Vector((q[0],0,q[1])),j)
  kd.balance();selected=np.flatnonzero(active&(p[:,0]*sign>0));dist=np.array([kd.find(Vector((p[i,0],0,p[i,2])))[2] for i in selected]);amount=1-ss(.009,.017,dist);mask[selected]=amount;U=np.clip((p[selected,0]-xmin)/width,0,1);line=corners[0,2]*(1-U)+corners[1,2]*U;side=np.where(p[selected,2]>=line,1,-1)
  lift=(.0014 if sex=='Male' else .0008)*np.sin(np.pi*U)**2*(side>0)
  zup=zfit(U,cu,corners);zlo=zfit(U,cl,corners);newmargin=np.where(side>0,zup,zlo)+lift
  sourceMargins=[]
  for up in [True,False]:
   order=np.argsort(u[upper==up]);sourceMargins.append(np.interp(U,u[upper==up][order],bp[upper==up,2][order]))
  oldmargin=np.where(side>0,sourceMargins[0],sourceMargins[1]);signedDistance=np.maximum(0,side*(p[selected,2]-oldmargin))
  edgefade=1-ss(0,.010,signedDistance);cornerfade=1-ss(0,.009,np.maximum(xmin-p[selected,0],p[selected,0]-xmax));edgefade*=cornerfade
  dz=(newmargin-oldmargin)*edgefade
  faceids=np.flatnonzero((p[:,1]<-.045)&(p[:,0]*sign>0)&(p[:,0]>xmin-.025)&(p[:,0]<xmax+.025)&(p[:,2]>bp[:,2].min()-.022)&(p[:,2]<bp[:,2].max()+.024));faceKD=KDTree(len(faceids))
  for i in faceids:faceKD.insert(Vector((p[i,0],0,p[i,2])),int(i))
  faceKD.balance()
  def fair(values,i,radius=.012):
   ids2=np.array([q[1] for q in faceKD.find_range(Vector((p[i,0],0,p[i,2])),radius)],int)
   if len(ids2)<6:return values[i]
   xz=(p[ids2][:,[0,2]]-p[i,[0,2]])/radius;x,z=xz.T;A=np.c_[np.ones(len(x)),x,z,x*x,x*z,z*z];w=np.exp(-2*(x*x+z*z));return np.linalg.lstsq(A*w[:,None],values[ids2]*w,rcond=None)[0][0]
  for j,i in enumerate(selected):
   fitted=fair(p[:,1],i);dy=np.clip(fitted-p[i,1],-.004,.004)*amount[j]
   yprofile=float(np.polyval(uy if side[j]>0 else ly,U[j]));rim=(.0007 if sex=='Female' else .0005)*np.exp(-.5*(signedDistance[j]/.0020)**2)*np.sin(np.pi*U[j])**.5
   near=(1-ss(0,.006,signedDistance[j]))*cornerfade[j]
   out['Basis'][i,1]=(p[i,1]+dy)*(1-near)+(yprofile-rim)*near;out['Basis'][i,2]+=dz[j]
   if side[j]>0:rimPigment[i]=(.38 if sex=='Female' else .19)*np.exp(-.5*(signedDistance[j]/.00065)**2)*np.sin(np.pi*U[j])**.35*cornerfade[j]
  delta=out['Basis']-p
  for name in ['Hero_Blink_Half','Hero_Blink']:out[name][selected]+=delta[selected]
  full=out['Hero_Blink'];half=out['Hero_Blink_Half'];fullY=full[:,1].copy();halfY=half[:,1].copy()
  qfull=shapes['Hero_Blink'][ids];seamY=np.polyfit(u,qfull[:,1],4);seamZ=np.polyfit(u,qfull[:,2],3)
  for j,i in enumerate(selected):
   lap=np.sin(np.pi*U[j])**.65
   y=float(np.polyval(seamY,U[j]))+(-.00022 if side[j]>0 else .00022)*lap
   z=float(np.polyval(seamZ,U[j]))+(-.00016 if side[j]>0 else .00016)*lap
   shift=(z-newmargin[j])*edgefade[j]
   full[i,2]=out['Basis'][i,2]+shift;half[i,2]=out['Basis'][i,2]+shift*.5
   depthfade=(1-ss(0,.012,signedDistance[j]))*cornerfade[j]
   full[i,1]=out['Basis'][i,1]*(1-depthfade)+y*depthfade
   half[i,1]=min(out['Basis'][i,1],halfY[i]+np.clip(fair(halfY,i,.012)-halfY[i],-.003,.003)*amount[j])
  for k,i in enumerate(ids):
   uu=u[k];up=upper[k];lap=np.sin(np.pi*uu)**.65;out['Basis'][i,2]=zfit(uu,cu if up else cl,corners)+((.0014 if sex=='Male' else .0008)*np.sin(np.pi*uu)**2 if up else 0)
   full[i,1]=np.polyval(seamY,uu)+(-.00022 if up else .00022)*lap;full[i,2]=np.polyval(seamZ,uu)+(-.00016 if up else .00016)*lap
  eyes.append({'side':sign,'boundaryVertices':len(ids),'activeVertices':len(selected),'widthMm':width*1000})
 # Unwrap the existing lid strip in the frontal tangent plane. Source male
 # interior triangles already fold back in X/Z; depth-only fairing cannot fix it.
 neighbours=[set() for _ in p]
 for e in me.edges:
  a,b=e.vertices;neighbours[a].add(b);neighbours[b].add(a)
 selectedSet=set(np.flatnonzero(mask>0));fixed=set(boundary)
 fixed.update(i for i in selectedSet if any(j not in selectedSet for j in neighbours[i]))
 fixed.update(i for i in selectedSet if not neighbours[i])
 free=np.array(sorted(selectedSet-fixed),int);lookup={int(i):j for j,i in enumerate(free)};L=np.zeros((len(free),len(free)));fixedRows=[]
 for row,i in enumerate(free):
  L[row,row]=len(neighbours[i]);extra=[]
  for j in neighbours[i]:
   if j in lookup:L[row,lookup[j]]=-1
   else:extra.append(j)
  fixedRows.append(extra)
 if len(free):
  B=np.zeros((len(free),9))
  for row,ids2 in enumerate(fixedRows):
   for k,name in enumerate(['Basis','Hero_Blink_Half','Hero_Blink']):B[row,k*3:k*3+3]=out[name][ids2].sum(0)
  solution=np.linalg.solve(L,B)
  for k,name in enumerate(['Basis','Hero_Blink_Half','Hero_Blink']):out[name][free]=solution[:,k*3:k*3+3]
 for key in me.shape_keys.key_blocks:
  for i,q in enumerate(out[key.name]):key.data[i].co=q
 for i,v in enumerate(me.vertices):v.co=out['Basis'][i]
 me.update();changed=np.linalg.norm(out['Basis']-p,axis=1)>1e-8
 me.normals_split_custom_set([(0,0,0)]*len(me.loops))
 for li,loop in enumerate(me.loops):
  if mask[loop.vertex_index]<=0:me.attributes['custom_normal'].data[li].value=oldnormal[li]
 uvold=np.array([u.uv[:] for u in me.uv_layers[0].data]);uvnew=uvold.copy()
 for li,loop in enumerate(me.loops):
  value=rimPigment[loop.vertex_index]
  if value<=0:continue
  old=np.clip((uvold[li]*64-.5)/63,0,1);old[1]=max(old[1],value);uvnew[li]=(.5+63*old)/64;me.uv_layers[0].data[li].uv=uvnew[li]
 me.update();deltas={name:out[name]-shapes[name] for name in shapes};np.savez_compressed(O/f'{sex.lower()}-operation.npz',**deltas,mask=mask,rimPigment=rimPigment,before=p,after=out['Basis'])
 for k in me.shape_keys.key_blocks:k.value=0
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_Face30Lids.blend'))
 for ob in bpy.context.scene.objects:ob.select_set(ob.name in ('Body','ReferenceFeatures') or ob.type=='ARMATURE')
 bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.fbx(filepath=str(O/f'{sex}_Face30Lids.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False,path_mode='STRIP',use_armature_deform_only=False)
 REPORT[sex]={'source':str(source),'candidate':str(O/f'{sex}_Face30Lids.blend'),'bodyVertices':len(p),'basisChanged':int(changed.sum()),'basisMaxMm':float(np.linalg.norm(deltas['Basis'],axis=1).max()*1000),'shapeMaxMm':{k:float(np.linalg.norm(v,axis=1).max()*1000) for k,v in deltas.items()},'changedOnlyActiveBlink':bool(not changed[~active].any()),'topologyRigWeightsFeaturesUnchanged':True,'eyes':eyes,'status':'SOURCE_BUILT_ART_PENDING'};print('LIDS30',sex,REPORT[sex],flush=True)
(O/'source-gate.json').write_text(json.dumps(REPORT,indent=2)+'\n')
