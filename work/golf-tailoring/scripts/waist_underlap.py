import bpy,bmesh
from pathlib import Path
W=Path(__file__).resolve().parents[1];path=W/'export/Golf_Male_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
old=bpy.data.objects.get('Golf_PoloUnderlap')
if old:bpy.data.objects.remove(old,do_unlink=True)
body=bpy.data.objects['Body_M'];rig=bpy.data.objects['Rig_Male'];names={g.index:g.name for g in body.vertex_groups};allowed={'Hips','Spine','Chest','UpperChest','LeftUpperLeg','RightUpperLeg'}
keep={v.index for v in body.data.vertices if .895<v.co.z<1.13 and sum(g.weight for g in v.groups if names[g.group] in allowed)>.85}
faces=[p for p in body.data.polygons if all(i in keep for i in p.vertices)];used=sorted({i for p in faces for i in p.vertices});lookup={j:i for i,j in enumerate(used)}
me=bpy.data.meshes.new('Tucked polo inner facing');me.from_pydata([body.data.vertices[j].co+body.data.vertices[j].normal*.012 for j in used],[],[[lookup[j] for j in p.vertices] for p in faces]);me.update()
o=bpy.data.objects.new('Golf_PoloUnderlap',me);bpy.context.scene.collection.objects.link(o);o.parent=rig;me.materials.append(bpy.data.materials['Golf_Main']);groups={n:o.vertex_groups.new(name=n) for n in names.values()}
for i,j in enumerate(used):
 for g in body.data.vertices[j].groups:groups[names[g.group]].add([i],g.weight,'REPLACE')
for p in me.polygons:p.use_smooth=True
mod=o.modifiers.new('Same match rig','ARMATURE');mod.object=rig
bm=bmesh.new();bm.from_mesh(me)
for z,normal in [(.978,(0,0,1)),(1.025,(0,0,-1))]:
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=normal,clear_inner=True,dist=.000001)
bm.to_mesh(me);bm.free();me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(path));print('POLO_UNDERLAP',len(used),len(faces))
