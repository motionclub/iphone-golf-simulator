import bpy,math,numpy as np,json
from pathlib import Path
from mathutils import Vector
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');P=np.array([v.co for v in m.vertices]);Q=P.copy();rows=[]
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
for side in ['Left','Right']:
 a=np.array(rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local);axis=np.array(rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local)-a;axis/=np.linalg.norm(axis);s=(P-a)@axis;rad=P-a-s[:,None]*axis;r=np.linalg.norm(rad,axis=1);rn=rad/np.maximum(r[:,None],1e-8);mass=np.array([sum(g.weight for g in v.groups if o.vertex_groups[g.group].name==side+'UpperArm') for v in m.vertices]);sideMask=(P[:,0]*a[0]>0)&(abs(P[:,0])>.165)
 # Modest radial ease at the deltoid; keep the torso and collar untouched.
 ease=.006*smooth(.25,.65,mass)*smooth(-.035,.005,s)*(1-smooth(.08,.14,s))*sideMask;Q+=rn*ease[:,None]
 # Preserve the existing turned fabric thickness but make its cuff termination coherent.
 e1=np.cross(axis,[0,1,0]);e1/=np.linalg.norm(e1);e2=np.cross(axis,e1);theta=np.arctan2(rad@e2,rad@e1);rim=sideMask&(mass>.55)&(s>.095)&(r<.10);end=[]
 for angle in np.linspace(-math.pi,math.pi,96,endpoint=False):
  near=rim&(abs(np.angle(np.exp(1j*(theta-angle))))<.10);end.append(float(np.max(s[near])) if any(near) else .136)
 end=np.array(end)
 for _ in range(5):end=(np.roll(end,1)+2*end+np.roll(end,-1))/4
 idx=(theta+math.pi)/(2*math.pi)*96;j=np.floor(idx).astype(int)%96;f=idx-np.floor(idx);maximum=end[j]*(1-f)+end[(j+1)%96]*f
 cuff=smooth(.095,.13,s)*smooth(.45,.8,mass)*sideMask*(r<.11);shift=(.138-maximum)*cuff;Q+=axis*shift[:,None]
 # The turned cuff follows the upper arm as one ring; no body bindings change.
 rigid=smooth(.07,.115,s)*smooth(.35,.75,mass)*sideMask*(r<.115)
 for i in np.flatnonzero(rigid>0):
  i=int(i);v=m.vertices[i];ww={o.vertex_groups[g.group].name:g.weight*(1-rigid[i]) for g in v.groups};ww[side+'UpperArm']=ww.get(side+'UpperArm',0)+rigid[i];ww=sorted(ww.items(),key=lambda x:-x[1])[:4];total=sum(x[1] for x in ww)
  for g in list(v.groups):o.vertex_groups[g.group].remove([i])
  for name,val in ww:o.vertex_groups[name].add([i],float(val/total),'REPLACE')
 rows.append({'side':side,'easeVertices':int(sum(ease>0)),'cuffVertices':int(sum(cuff>0)),'rigidVertices':int(sum(rigid>0)),'maxEaseMm':float(ease.max()*1000),'maxCuffShiftMm':float(abs(shift).max()*1000)})
for v,q in zip(m.vertices,Q):v.co=q
m.update();bpy.context.view_layer.objects.active=o;o.select_set(True)
if m.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_SleeveFinish.blend'));bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'sleeve-finish-source.json').write_text(json.dumps(rows,indent=2));print(rows,flush=True)
j=json.loads((w/'matrix-mass-runtime-queue.json').read_text());j[0]['name']='character-finish32-sleeve-finish-source';e=j[0]['env'];e['VISUAL_CHARACTER_OUT']=str(w.resolve()/'sleeve-finish-source');e.pop('VISUAL_TAILORED_MATRIX_PROFILE',None);e['VISUAL_CHARACTER_CLOTH_MATRIX_ONLY']='1';e['VISUAL_CHARACTER_CLOTH_CLIPS']='Serve';e['VISUAL_CHARACTER_CLOTH_SAMPLES']='3';(w/'sleeve-finish-source-queue.json').write_text(json.dumps(j,indent=2))
