import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Baseline.blend'))
o=bpy.data.objects['Kit_Top'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
row=json.loads((w/'source-inspection.json').read_text())[0]
for i,g in enumerate(row['components'][:12]):
 weights={}
 for v in g['ids']:
  for m in o.data.vertices[v].groups:weights[o.vertex_groups[m.group].name]=weights.get(o.vertex_groups[m.group].name,0)+m.weight/len(g['ids'])
 print('COMP',i,sorted(weights.items(),key=lambda x:-x[1])[:8])
body=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0]
for name in ['Hips','Spine','Chest','LeftUpperArm','LeftLowerArm','Neck']:
 i=body['bones'].index(name);mat=Matrix([body['bindposes'][i*16+j*4:i*16+j*4+4] for j in range(4)]).inverted();bone=rig.data.bones[name];print('BONE',name,'body',list(mat.translation),'rig',list(rig.matrix_world@bone.head_local))
