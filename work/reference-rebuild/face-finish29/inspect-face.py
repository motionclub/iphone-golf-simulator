import bpy,numpy as np,pathlib,json
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish29';result={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend'));ob=bpy.data.objects['Body'];me=ob.data
 groups={}
 for g in ob.vertex_groups:
  if any(s in g.name.lower() for s in ('seam','mouth','lip','ala','nostril')):
   ids=[v.index for v in me.vertices if any(a.group==g.index and a.weight>.25 for a in v.groups)];v=np.array([tuple(me.vertices[i].co) for i in ids]);uv=[tuple(l.uv) for f in me.polygons for l in [me.uv_layers.active.data[f.loop_start+j] for j,i in enumerate(f.vertices) if i in set(ids)]]
   groups[g.name]={'ids':ids,'coordinates':v.tolist(),'min':v.min(0).tolist(),'max':v.max(0).tolist(),'uvMin':np.array(uv).min(0).tolist(),'uvMax':np.array(uv).max(0).tolist()}
 result[sex]={'groups':groups,'materialNames':[m.name for m in me.materials],'shapeKeys':[k.name for k in me.shape_keys.key_blocks],'bodyVertices':len(me.vertices),'vertexColors':[a.name for a in me.color_attributes]}
 print(sex,{k:{q:v[q] for q in ('min','max','uvMin','uvMax')} for k,v in groups.items()},flush=True)
(O/'source-inspection.json').write_text(json.dumps(result,indent=2)+'\n')
