"""Read-only source test of the Unity material-projection recipe against Eye13 UVs."""
import bpy,json,pathlib,math
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/character-material-adoption1';out={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-refinement/{sex}_OriginalSeamEyeMaterial.blend'))
 me=bpy.data.objects['ReferenceFeatures'].data;uv=me.uv_layers['OriginalEyeLocal'];me.calc_loop_triangles();points=[v.co for v in me.vertices];regions={}
 for kind in ('Iris','Sclera'):
  for side in (-1,1):
   ps=[p for p in me.polygons if kind in me.materials[p.material_index].name and sum(points[i].x for i in p.vertices)*side>0];pid={p.index for p in ps};ids={i for p in ps for i in p.vertices};c=sum((points[i] for i in ids),Vector())/len(ids)
   normal=sum(((points[t.vertices[1]]-points[t.vertices[0]]).cross(points[t.vertices[2]]-points[t.vertices[0]]) for t in me.loop_triangles if t.polygon_index in pid),Vector()).normalized()
   if normal.y>0:normal=-normal
   up=Vector((0,0,1));up=(up-normal*up.dot(normal)).normalized();right=up.cross(normal).normalized();width=max(abs((points[i]-c).dot(right)) for i in ids);height=max(abs((points[i]-c).dot(up)) for i in ids)
   if kind=='Iris':width=height=max(width,height)
   errors=[]
   for p in ps:
    for li in p.loop_indices:
     d=points[me.loops[li].vertex_index]-c;a=Vector((.5+.5*d.dot(right)/width,.5+.5*d.dot(up)/height));errors.append((a-uv.data[li].uv).length)
   regions[f'{kind}_{side}']={'vertices':len(ids),'halfExtent':[width,height],'maxUvDifference':max(errors),'meanUvDifference':sum(errors)/len(errors)}
 out[sex]=regions
assert max(r['maxUvDifference'] for v in out.values() for r in v.values())<.002/128,out
(O/'eye-projection-source-gate.json').write_text(json.dumps({'gate':'PASS','toleranceTexelsAt128':.002,'sourceEye13UvMaxDifference':max(r['maxUvDifference'] for v in out.values() for r in v.values()),'regions':out,'limits':'Read-only source equivalence only; Unity FBX import transforms/vertex splits require actual capture.'},indent=2)+'\n')
print('EYE_PROJECTION_SOURCE_GATE PASS',out)
