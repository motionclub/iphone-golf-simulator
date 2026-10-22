import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
w=Path('work/character-female33');bpy.ops.wm.open_mainfile(filepath='work/character-finish32/Male_Polo_CuffRebuilt.blend');o=bpy.data.objects['Kit_Top'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');P=np.array([v.co for v in o.data.vertices]);VN=np.array([v.normal for v in o.data.vertices]);F=[list(f.vertices) for f in o.data.polygons];FN=np.array([f.normal for f in o.data.polygons]);cent=np.array([P[f].mean(0) for f in F]);weight=np.array([[sum(g.weight for g in v.groups if o.vertex_groups[g.group].name==side+'UpperArm') for side in ['Left','Right']] for v in o.data.vertices]);mass=np.array([weight[f].mean(0) for f in F]);rad=cent.copy();rad[:,1]+=.015;rad[:,2]=0
for k,side in enumerate(['Left','Right']):
 a=np.array(rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local);axis=np.array(rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local)-a;axis/=np.linalg.norm(axis);rr=cent-a-((cent-a)@axis)[:,None]*axis;alpha=np.clip(mass[:,k]/.30,0,1);rad=rad*(1-alpha[:,None])+rr*alpha[:,None]
rad/=np.maximum(np.linalg.norm(rad,axis=1)[:,None],1e-8);dot=(rad*FN).sum(1);remove=(dot<-.35)&(abs(cent[:,0])>.13)&(cent[:,2]>1.04)&(cent[:,2]<1.4)&(mass.max(1)<.97)
# Leave the collar, placket and turned cuff rings intact.
kill={tuple(sorted(F[i])) for i in np.flatnonzero(remove)}
bpy.ops.wm.open_mainfile(filepath=str(w/'Female_Polo_CuffFit.blend'));o=bpy.data.objects['Kit_Top'];tree=KDTree(len(o.data.vertices))
for v in o.data.vertices:tree.insert(Vector((-v.co.x,v.co.y,v.co.z)),v.index)
tree.balance();d=json.loads((w/'cuff-fit-source/poses/female_intro.json').read_text());t=next(p for p in d['parts'] if p['name']=='Kit_Top');U=np.array(t['vertices']).reshape(-1,3);mapping=[]
for p in U:
 q,i,dist=tree.find(Vector(p));assert dist<1e-5;mapping.append(i)
tri=np.array(t['triangles']).reshape(-1,3);removeIds=[i for i,f in enumerate(tri) if tuple(sorted(mapping[v] for v in f)) in kill];(w/'lining-triangles.json').write_text(json.dumps({'removeTriangles':removeIds}));print('REMOVE',len(removeIds),'of',len(tri))

np.savez_compressed(w/'male-template-correspondence.npz',P=P[mapping],N=VN[mapping])
