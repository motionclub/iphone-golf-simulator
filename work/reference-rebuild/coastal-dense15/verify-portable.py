import bpy,json,hashlib,struct
from pathlib import Path
repo=Path(__file__).resolve().parents[3]
def digest(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));result={}
 for name in ['TURF_NEAR','TURF_MID','TURF_FAR']:
  ob=bpy.data.objects[name];m=ob.data;m.calc_loop_triangles();h=hashlib.sha256()
  for vertex in m.vertices:h.update(struct.pack('3f',*vertex.co))
  for face in m.polygons:h.update(struct.pack('I',len(face.vertices)));h.update(struct.pack(str(len(face.vertices))+'I',*face.vertices))
  for row in ob.matrix_world:h.update(struct.pack('4f',*row))
  for layer in m.uv_layers:
   for uv in layer.data:h.update(struct.pack('2f',*uv.uv))
  result[name]={'vertices':len(m.vertices),'triangles':len(m.loop_triangles),'geometryUVTransformSha256':h.hexdigest()}
 return result
original=digest(repo/'ArtDir/golf/source/CoastalTurf.blend');rebuilt=digest(repo/'work/reference-rebuild/coastal-dense15/portable-rebuild/CoastalTurf.blend');assert original==rebuilt
out={'status':'PASS exact canonical geometry/UV/object-transform digest vs portable rebuild','original':original,'rebuild':rebuilt,'binaryFBXIdentity':'Not claimed; export container metadata/timestamps may differ.'}
(repo/'ArtDir/golf/proof/dense-turf15/portable-geometry-proof.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
