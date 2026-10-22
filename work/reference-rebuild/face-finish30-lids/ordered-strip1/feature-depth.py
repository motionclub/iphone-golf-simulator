import bpy,numpy as np,json
from pathlib import Path
O=Path.cwd()/'work/reference-rebuild/face-finish30-lids/ordered-strip1';report={}
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_Face30OrderedLids.blend'));f=bpy.data.objects['ReferenceFeatures'];p=np.array([v.co[:]for v in f.data.vertices]);sh={k.name:np.array([v.co[:]for v in k.data])for k in f.data.shape_keys.key_blocks};r={}
 for mi,m in enumerate(f.data.materials):
  ids=np.unique([i for q in f.data.polygons if q.material_index==mi for i in q.vertices]);r[m.name]={'min':p[ids].min(0).tolist(),'max':p[ids].max(0).tolist(),'halfY':(sh['Hero_Blink_Half'][ids,1]-p[ids,1]).min().item(),'fullY':(sh['Hero_Blink'][ids,1]-p[ids,1]).max().item()}
 report[sex]=r
(O/'FEATURE_DEPTH.json').write_text(json.dumps(report,indent=2));print(report)
