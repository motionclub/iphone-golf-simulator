"""Compare Unity audit exports. No geometry or gameplay source changes are permitted."""
import json,sys
from pathlib import Path
before=Path(sys.argv[1]);after=Path(sys.argv[2]);out=Path(sys.argv[3])
results=[]
for p in sorted(after.glob('hole*_audit.json')):
 original=before/p.name
 if not original.exists():
  results.append({'hole':p.name,'gate':'UNVERIFIED','reason':'No matching before audit'});continue
 a=json.loads(original.read_text());b=json.loads(p.read_text())
 geometry=lambda d:sorted((x['name'],x['hash'],x['vertices'],x['triangles']) for x in d.get('ground',[]))
 checks={'obstacle_count':a['obstacleCount']==b['obstacleCount'],'obstacle_hash':a['obstacleHash']==b['obstacleHash'],'ground_mesh_hashes':geometry(a)==geometry(b),'collider_count':a['colliders']==b['colliders']}
 results.append({'hole':b['hole'],'gate':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'camera_triangles_before':a.get('cameraMeshTriangles'),'camera_triangles_after':b.get('cameraMeshTriangles'),'camera_material_passes_before':a.get('cameraMaterialPasses'),'camera_material_passes_after':b.get('cameraMaterialPasses')})
out.write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if any(r['gate']=='FAIL' for r in results):sys.exit(1)
