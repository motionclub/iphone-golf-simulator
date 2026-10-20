import bpy,sys,json,numpy as np
from pathlib import Path
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];o=bpy.data.objects['Golf_Polo'];rest=np.array([v.co[:] for v in o.data.vertices]);edges=np.array([e.vertices[:] for e in o.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);valid=length>.003
best=(0,None);sc=bpy.context.scene
for tr in rig.animation_data.nla_tracks:tr.mute=True
manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text())
for c in manifest['clips']:
 rig.animation_data.action=bpy.data.actions[c['id']];o.data.shape_keys.animation_data.action=bpy.data.actions.get(c['id']+'_Golf_Polo_Correctives')
 for tr in o.data.shape_keys.animation_data.nla_tracks:tr.mute=True
 for t in np.linspace(0,c['duration'],9):
  sc.frame_set(int(t*120),subframe=float(t*120-int(t*120)));bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=np.array([v.co[:] for v in m.vertices]);ratio=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1)/np.maximum(length,1e-8);assert np.isfinite(posed).all(),c['id'];ratio[~valid]=0;i=int(ratio.argmax())
  if ratio[i]>best[0]:
   ids=edges[i];best=(float(ratio[i]),dict(id=c['id'],time=float(t),length=float(length[i]),points=[dict(index=int(j),rest=rest[j].tolist(),posed=posed[j].tolist(),weights={o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[j].groups}) for j in ids]));print('WORST',sex,json.dumps(best),flush=True)
  ev.to_mesh_clear()
(W/f'data/polo_region_{sex}.json').write_text(json.dumps(dict(maxStretch=best[0],detail=best[1]),indent=2));print('REGION_CHECK_COMPLETE',sex,flush=True)
