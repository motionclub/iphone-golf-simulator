"""Read-only local bind anatomy and transform diagnostics."""
import bpy,json,sys
from pathlib import Path
from collections import Counter
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1]
body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M'];rig=bpy.data.objects['Rig_'+sex]
names={g.index:g.name for g in body.vertex_groups};lower={i for i,n in names.items() if any(k in n for k in ['UpperLeg','LowerLeg','Hips','Spine'])}
hips=[v for v in body.data.vertices if .78<v.co.z<.98 and abs(v.co.x)<.30]
rejected=[v for v in hips if sum(g.weight for g in v.groups if g.group in lower)<=.35]
bad=Counter(names[max(v.groups,key=lambda g:g.weight).group] for v in rejected if v.groups)
out=dict(armature_modes={o.name:[{'object':m.object.name if m.object else None,'preserve_volume':m.use_deform_preserve_volume,'use_vertex_groups':m.use_vertex_groups} for m in o.modifiers if m.type=='ARMATURE'] for o in bpy.data.objects if o.type=='MESH' and (o==body or o.name.startswith('Golf_'))},sex=sex,body_world=list(map(list,body.matrix_world)),rig_world=list(map(list,rig.matrix_world)),body_parent=body.parent.name if body.parent else None,body_parent_inverse=list(map(list,body.matrix_parent_inverse)),hip_vertices=len(hips),rejected_lower_vertices=len(rejected),rejected_dominant_groups=dict(bad),examples=[dict(index=v.index,co=list(v.co),weights={names[g.group]:g.weight for g in v.groups}) for v in rejected[:20]])
(W/f'data/skinning_modes_{sex}.json').write_text(json.dumps(out,indent=2)+'\n');print(out,flush=True)
