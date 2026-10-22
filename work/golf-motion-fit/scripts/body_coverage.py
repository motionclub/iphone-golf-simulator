"""Reversible render coverage. Original vertices, polygons, weights and rig stay intact."""
import bpy,sys
import numpy as np
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def coverage(body,rig,female,hem):
 covered=[]
 for v in body.data.vertices:
  w={body.vertex_groups[g.group].name:g.weight for g in v.groups};p=v.co
  exposed=sum(w.get(s+d,0) for s in ['Left','Right'] for d in ['Hand','LowerArm'])>.6
  torso=sum(w.get(n,0) for n in ['Hips','Spine','Chest','UpperChest','Neck'])>.45
  upperleg=sum(w.get(n,0) for n in ['Hips','LeftUpperLeg','RightUpperLeg','LeftLowerLeg','RightLowerLeg'])>.4
  hide=(torso and .933<p.z<1.425 and not exposed) or (upperleg and (.116 if not female else hem-.012)<p.z<.989 and not exposed)
  for side in ['Left','Right']:
   if w.get(side+'UpperArm',0)+w.get(side+'Shoulder',0)>.5:
    a=rig.data.bones[side+'UpperArm'].head_local;b=rig.data.bones[side+'LowerArm'].head_local
    if (p-(a+(b-a)*.68)).dot((b-a).normalized())<.004:hide=True
  covered.append(hide)
 faces=[all(covered[i] for i in p.vertices) for p in body.data.polygons]
 return faces
if __name__=='__main__':
 sex=sys.argv[-1];female=sex=='Female';r=bpy.data.objects['Rig_'+sex];b=bpy.data.objects['Body_'+('F' if female else 'M')];hem=(r.data.bones['LeftLowerLeg'].head_local.z+r.data.bones['RightLowerLeg'].head_local.z)/2+.045
 faces=coverage(b,r,female,hem)
 attr=b.data.attributes.get('golf_covered') or b.data.attributes.new('golf_covered','BOOLEAN','FACE');attr.data.foreach_set('value',faces)
 for mod in list(b.modifiers):
  if mod.name=='Golf outfit coverage':b.modifiers.remove(mod)
 nodes=bpy.data.node_groups.new('GolfCoveredSkin_'+sex,'GeometryNodeTree');nodes.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');nodes.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 src=nodes.nodes.new('NodeGroupInput');dst=nodes.nodes.new('NodeGroupOutput');read=nodes.nodes.new('GeometryNodeInputNamedAttribute');read.data_type='BOOLEAN';read.inputs['Name'].default_value='golf_covered';delete=nodes.nodes.new('GeometryNodeDeleteGeometry');delete.domain='FACE';delete.mode='ALL'
 nodes.links.new(src.outputs['Geometry'],delete.inputs['Geometry']);nodes.links.new(read.outputs['Attribute'],delete.inputs['Selection']);nodes.links.new(delete.outputs['Geometry'],dst.inputs['Geometry'])
 mod=b.modifiers.new('Golf outfit coverage','NODES');mod.node_group=nodes;b['GolfCoverage']='Reversible modifier; base vertices/polygons/weights preserved.'
 print('BODY_COVERAGE',sex,sum(faces),len(faces),flush=True)
