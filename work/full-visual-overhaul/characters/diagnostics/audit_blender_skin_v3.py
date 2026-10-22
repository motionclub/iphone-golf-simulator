import bpy,pathlib,sys,json
from mathutils import Matrix,Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1];bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update();groups={g.index:g.name for g in body.vertex_groups};A=rig.matrix_world.inverted()@body.matrix_world;B=A.inverted();skin={b.name:B@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@A for b in rig.data.bones};mesh=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();worst=0;at=None
for i,v in enumerate(body.data.vertices):
 m=Matrix(((0,0,0,0),)*4);s=0
 for g in v.groups:
  name=groups[g.group]
  if name in skin:m+=g.weight*skin[name];s+=g.weight
 if s<.001:continue
 p=(m*(1/s))@v.co;e=(p-mesh.vertices[i].co).length
 if e>worst:worst=e;at={'id':i,'p':list(v.co),'cpu':list(p),'bpy':list(mesh.vertices[i].co),'w':{groups[g.group]:g.weight for g in v.groups}}
print('SKINPARITY',worst,at);print('DEFORM',[(b.name,b.use_deform) for b in rig.data.bones if 'Left' in b.name]);print('MOD',[(m.name,m.use_vertex_groups,m.use_bone_envelopes,m.vertex_group) for m in body.modifiers if m.type=='ARMATURE'])
