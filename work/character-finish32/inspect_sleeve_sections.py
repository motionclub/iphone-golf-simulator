import bpy,numpy as np,json
from pathlib import Path
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');P=np.array([v.co for v in o.data.vertices]);rows=[]
for side in ['Left','Right']:
 a=np.array(rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local);d=np.array(rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local)-a;d/=np.linalg.norm(d);s=(P-a)@d;rad=P-a-s[:,None]*d;radius=np.linalg.norm(rad,axis=1);use=(P[:,0]*a[0]>0)&(abs(P[:,0])>.17)&(P[:,2]>1.15);sel=np.flatnonzero(use);mass=np.array([sum(g.weight for g in v.groups if o.vertex_groups[g.group].name==side+'UpperArm') for v in o.data.vertices]);print(side,'a',a,'d',d,'s',np.quantile(s[use],[0,.1,.5,.9,.95,.98,1]),flush=True)
 for lo,hi in [(0,.04),(.04,.08),(.08,.12),(.12,.16),(.16,.20),(.20,.24)]:
  q=use&(s>=lo)&(s<hi);print('section',lo,hi,'n',sum(q),'rad',np.quantile(radius[q],[0,.1,.5,.9,1]) if any(q) else [],'mass',np.quantile(mass[q],[0,.1,.5,.9,1]) if any(q) else [],flush=True)
 np.savez(w/('sleeve-'+side+'.npz'),P=P,a=a,d=d,s=s,radius=radius,mass=mass)
