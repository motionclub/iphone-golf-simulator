import bpy,pathlib,json,hashlib,numpy as np
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-local-surface-finish'
def dig(x):return hashlib.sha256(repr(x).encode()).hexdigest()
def snap(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path),use_anim=False)
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');out={'bones':[(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row)) for b in rig.data.bones]}
 for name in ('Body','ReferenceFeatures'):
  o=bpy.data.objects[name];me=o.data;basis=np.array([tuple(v.co) for v in me.vertices]);out[name]={'positions':basis,'shapeDeltas':{k.name:np.array([tuple(p.co) for p in k.data])-basis for k in me.shape_keys.key_blocks},'stable':{'topology':dig([(tuple(p.vertices),p.material_index,p.use_smooth) for p in me.polygons]),'weights':dig([[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in me.vertices]),'uv':dig([[tuple(p.uv) for p in l.data] for l in me.uv_layers]),'color':dig([[tuple(p.color) for p in l.data] for l in me.color_attributes])}}
 return out
before=snap(R/'work/reference-rebuild/original-blink-finish/Male_OriginalSeamBlinkFinish1.fbx');after=snap(O/'Male_OriginalSeamLocalSurfaceFinish1.fbx')
result={'gate':'PASS','bonesCount':len(before['bones']),'bonesRestHierarchyExact':before['bones']==after['bones'],'objects':{}}
assert result['bonesRestHierarchyExact'] and result['bonesCount']==53
for name in ('Body','ReferenceFeatures'):
 a,b=before[name],after[name];delta=b['positions']-a['positions'];shapes={n:float(np.max(abs(a['shapeDeltas'][n]-b['shapeDeltas'][n]))) for n in a['shapeDeltas']};result['objects'][name]={'vertices':len(a['positions']),'weightsTopologyUvColorExact':a['stable']==b['stable'],'maxPositionDeltaMetres':float(np.linalg.norm(delta,axis=1).max()),'maxShapeDeltaErrorsMetres':shapes};assert a['stable']==b['stable'];assert max(shapes.values())<1e-6
 if name=='ReferenceFeatures':assert np.max(abs(delta))==0
(O/'fbx-roundtrip-gate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
