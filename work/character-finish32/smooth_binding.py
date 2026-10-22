import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');P=np.array([v.co[:] for v in m.vertices]);N=np.array([v.normal[:] for v in m.vertices]);W=np.zeros((len(P),len(o.vertex_groups)))
for v in m.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
kd=KDTree(len(P))
for i,p in enumerate(P):kd.insert(Vector(p),i)
kd.balance();rows=[];A=[]
for i,p in enumerate(P):
 x,y,z=p;fade=min(1,max(0,(abs(x)-.145)/.025))*min(1,max(0,(.35-abs(x))/.025))*min(1,max(0,(z-1.10)/.045))*min(1,max(0,(1.42-z)/.045))
 if fade<=0:continue
 ns=kd.find_range(Vector(p),.032);ids=np.array([j for _,j,d in ns]);dist=np.array([d for _,j,d in ns]);a=np.exp(-.5*(dist/.012)**2);a/=a.sum();rows.append((i,ids,a,fade))
old=W.copy()
for it in range(4):
 nextW=W.copy()
 for i,ids,a,fade in rows:nextW[i]=W[i]*(1-.65*fade)+(W[ids]*a[:,None]).sum(0)*(.65*fade)
 W=nextW
for i,ids,a,fade in rows:
 v=m.vertices[i];keep=np.argsort(W[i])[-4:];vals=W[i,keep];vals/=vals.sum()
 for g in list(v.groups):o.vertex_groups[g.group].remove([i])
 for g,a in zip(keep,vals):o.vertex_groups[int(g)].add([i],float(a),'REPLACE')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_SmoothBind.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
print('SMOOTH_BIND',len(rows),'maxchange',np.abs(W-old).max(),flush=True)
