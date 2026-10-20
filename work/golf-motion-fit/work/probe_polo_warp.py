import bpy,json
from pathlib import Path
s='Female';o=bpy.data.objects['Golf_Polo'];r=bpy.data.objects['Rig_'+s];r.animation_data.action=bpy.data.actions['Drive_Female_LH'];o.data.shape_keys.animation_data.action=bpy.data.actions['Drive_Female_LH_Golf_Polo_Correctives'];bpy.context.scene.frame_set(408);bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
rows=[]
for edge in o.data.edges:
 a,b=edge.vertices;la=(o.data.vertices[a].co-o.data.vertices[b].co).length;lb=(m.vertices[a].co-m.vertices[b].co).length
 if la>.001 and lb/la>2 and min(o.data.vertices[a].co.z,o.data.vertices[b].co.z)<1.15:
  rows.append((lb,la,[(i,tuple(o.data.vertices[i].co),tuple(m.vertices[i].co),[(o.vertex_groups[g.group].name,g.weight) for g in o.data.vertices[i].groups]) for i in [a,b]]))
print('WARP',json.dumps(sorted(rows,reverse=True)[:25]),flush=True)
