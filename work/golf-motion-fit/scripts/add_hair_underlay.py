import bpy,sys
from mathutils import Matrix
s=sys.argv[-1]
if s=='Female':
 r=bpy.data.objects['Rig_Female'];b=bpy.data.objects['Body_F'];hair=bpy.data.objects['Golf_Hair_Visor'];keep={v.index for v in b.data.vertices if v.co.z>1.555}
 polys=[p for p in b.data.polygons if all(i in keep for i in p.vertices)];used=sorted({i for p in polys for i in p.vertices});remap={i:j for j,i in enumerate(used)}
 m=bpy.data.meshes.new('FittedScalpHair');m.from_pydata([b.data.vertices[i].co+b.data.vertices[i].normal*.009 for i in used],[],[tuple(remap[i] for i in p.vertices) for p in polys]);m.update();o=bpy.data.objects.new('Golf_Hair_Underlay',m);bpy.context.scene.collection.objects.link(o)
 for mat in hair.data.materials:m.materials.append(mat)
 for p in m.polygons:p.use_smooth=True
 vg=o.vertex_groups.new(name='Head');vg.add(list(range(len(m.vertices))),1,'REPLACE');o.parent=r;o.matrix_world=Matrix.Identity(4);o.modifiers.new('Head','ARMATURE').object=r
 print('HAIR_UNDERLAY',len(m.vertices),flush=True)
