import os,sys,json,math
import bpy,numpy as np
from mathutils import Vector
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'));sys.path.insert(0,os.path.join(repo,'blender/scripts'))
import postcard_look_verify as V
import hole08_design as des
C=V.Ctx(8,des,des.__file__,{})
rows=[]
for name,path in [('v2','work/postcard-look/v2/hole08/stage/hole_08.blend'),('attempt1','work/postcard-look/v3/hole08/stage/hole_08.blend')]:
 bpy.ops.wm.open_mainfile(filepath=os.path.join(repo,path),load_ui=False);S=V.Snap('blend',C);obs={n:o for n,o in S.meshes.items() if n.startswith('DRESS_ARCH')}
 idx=V.TriIndex(S,list(obs.values()));P=idx.V;c=P[:,:2].mean(0);ev,evec=np.linalg.eigh(np.cov((P[:,:2]-c).T))
 out={'name':name,'exact_opening':V.arch_opening(S,obs),'objects':list(obs),'eigenvalues':ev.tolist(),'axis_results':[]}
 for span_axis in (evec[:,1],evec[:,0]):
  t_axis=np.array([-span_axis[1],span_axis[0]]);u=(P[:,:2]-c)@span_axis;v=(P[:,:2]-c)@t_axis;z0,z1=float(P[:,2].min()),float(P[:,2].max());us=np.arange(float(u.min())+.125,float(u.max()),.25);zs=np.arange(z0+.125,z1,.25);free=np.zeros((len(us),len(zs)),bool);r0,r1=float(v.min())-2,float(v.max())+2
  for i,uu in enumerate(us):
   for j,zz in enumerate(zs):
    o=c+span_axis*uu+t_axis*r0;free[i,j]=idx.bvh.ray_cast(Vector((o[0],o[1],zz)),Vector((t_axis[0],t_axis[1],0)),r1-r0)[0] is None
  wins=[]
  for i in range(len(us)-6):
   col=bool(free[i:i+6,2:10].all());above=bool((~free[i:i+6,10:]).any(axis=1).all()) if 10<len(zs) else False;left=bool((~free[max(0,i-16):i,2:10]).any()) if i else False;right=bool((~free[i+6:i+22,2:10]).any()) if i+6<len(us) else False
   if col:wins.append({'i':i,'u_m':float(us[i]),'above':above,'left':left,'right':right})
  out['axis_results'].append({'span_axis':span_axis.tolist(),'axis_heading_deg':math.degrees(math.atan2(span_axis[1],span_axis[0])),'u_span_m':float(np.ptp(u)),'v_span_m':float(np.ptp(v)),'z0':z0,'z1':z1,'columns_with_bottom_clear_height':[float(us[i]) for i in range(len(us)) if free[i,2:10].all()],'candidate_windows':wins})
 rows.append(out)
json.dump(rows,open(os.path.join(os.path.dirname(__file__),'arch_profile_diagnosis.json'),'w'),indent=2);print(json.dumps(rows,indent=2))
