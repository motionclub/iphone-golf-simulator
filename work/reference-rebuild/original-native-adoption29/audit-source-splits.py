import bpy,pathlib,json,collections,hashlib,numpy as np
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/original-native-adoption29';results={}
def snap(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));body=bpy.data.objects['Body'];m=body.data
 normals=np.array([tuple(n.vector) for n in m.corner_normals]);uv=np.array([tuple(u.uv) for u in m.uv_layers[0].data]);corners=np.array([l.vertex_index for l in m.loops]);verts=np.array([tuple(v.co) for v in m.vertices]);sets=collections.defaultdict(set)
 for i,vertex in enumerate(corners):sets[int(vertex)].add((tuple(normals[i]),tuple(uv[i])))
 return {'vertices':verts,'corners':corners,'polygons':[(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],'weights':[[(g.group,g.weight) for g in v.groups] for v in m.vertices],'shapes':{k.name:np.array([tuple(p.co) for p in k.data])-verts for k in m.shape_keys.key_blocks},'normal':normals,'uv':uv,'sets':sets,'expanded':sum(len(v) for v in sets.values()),'unusedVertices':len(m.vertices)-len(sets)}
for sex in ('Male','Female'):
 a=snap(R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend');b=snap(R/f'work/reference-rebuild/face-finish29/smooth-mouth1/{sex}_OriginalFaceFinish29Smooth1.blend')
 assert a['polygons']==b['polygons'] and a['weights']==b['weights'] and np.array_equal(a['corners'],b['corners']);assert np.array_equal(a['vertices'][:,[0,2]],b['vertices'][:,[0,2]])
 for shape in a['shapes']:assert np.max(abs(a['shapes'][shape]-b['shapes'][shape]))<1e-7
 changes=[]
 for vertex in a['sets']:
  av,bv=a['sets'][vertex],b['sets'][vertex]
  if len(av)!=len(bv):changes.append({'sourceVertex':vertex,'restXYZ':a['vertices'][vertex].tolist(),'oldCornerVariants':len(av),'newCornerVariants':len(bv),'oldNormalVariants':len({x[0] for x in av}),'newNormalVariants':len({x[0] for x in bv}),'oldUvVariants':len({x[1] for x in av}),'newUvVariants':len({x[1] for x in bv})})
 results[sex]={'oldExpandedCornerCount':a['expanded'],'newExpandedCornerCount':b['expanded'],'delta':b['expanded']-a['expanded'],'originalSourceVertices':len(a['vertices']),'sourceTopologyWeightsShapesExact':True,'unusedSourceVerticesBeforeAfter':[a['unusedVertices'],b['unusedVertices']],'splitChanges':changes}
(O/'source-split-proof.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
