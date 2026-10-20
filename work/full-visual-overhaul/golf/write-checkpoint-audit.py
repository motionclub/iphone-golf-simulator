"""Collect source hashes, independent geometry and actual Metal evidence without running Unity."""
from pathlib import Path
import json,re,hashlib
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');proof=root/'proof/full-visual-overhaul/golf'
log=(root/'work/full-visual-overhaul/golf-pass-7.log').read_text(errors='replace');budget=[]
for n in [12,19,21]:
 audit=json.loads((root/f'proof/full-visual-overhaul/golf-pass-7/hole{n}_audit.json').read_text())
 plants=re.search(fr'\[GolfResortDress\] hole {n}: (\d+) botanical assets, (\d+) triangles in (\d+) bounded batches',log)
 outcrops=re.search(fr'\[GolfResortDress\] hole {n}: (\d+) sparse',log)
 record={'hole':n,'checkpoint':7,'camera_frustum_geometry_triangles':audit['cameraMeshTriangles'],'camera_material_passes_geometry_only':audit['cameraMaterialPasses'],'dressing':{'asset_instances':int(plants[1]),'triangles_entire_hole':int(plants[2]),'bounded_batches_entire_hole':int(plants[3]),'outcrop_modules':int(outcrops[1])},'cliff':{k:audit[k] for k in ['cliffAddedTriangles','cliffMovedVertices','cliffMaximumDisplacement']},'physics':'PASS','geometry_counts_scope':'Frustum mesh/material estimate, not published frame cost; audit drawCalls/triangles are excluded because camera renders can accumulate stale Editor statistics.'}
 cost=root/f'proof/full-visual-overhaul/frame-costs-2/hole{n}_tee.frame_costs.json'
 if cost.exists():
  data=json.loads(cost.read_text());record['published_metal_frame']={k:data.get(k) for k in ['status','drawCallGate','drawCalls','triangles','setPass','scope','cameraPosition','fov']}
 else:record['published_metal_frame']='PENDING root capture'
 budget.append(record)
(proof/'budget-pass-7.json').write_text(json.dumps(budget,indent=2))
source=json.loads((proof/'source-catalog.json').read_text());holecs=(root/'Unity/Assets/Scripts/Course/Hole.cs').read_text();names={int(n):name for n,name in re.findall(r'Number\s*=\s*(\d+),\s*Par\s*=\s*\d+,\s*Name\s*=\s*"([^"]+)"',holecs)}
def filedata(p):return {'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
rows=[]
for n in [1,2,3,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]:
 native=n not in [1,2,3];volcanic=n in [10,16,21,22,23];biome='volcanic' if volcanic else {17:'alpine',18:'desert',19:'jungle',20:'pastoral',14:'woodland'}.get(n,'meadow' if not native else 'coastal')
 row={'hole':n,'name':names.get(n,'Meadow '+str(n) if not native else 'Authored course'),'biome':biome,'environment_runtime':'GolfCourseLook + GolfResortDress + GolfCourseAtmosphere','source_is_authority_for':['terrain','ball physics','hazards','tee','pin','obstacles'],'visual_gate':'PENDING full catalog capture','physics_gate':'PASS through pilot7' if n in [12,19,21] else 'PENDING full catalog baseline'}
 if native:
  row['original_blend']=filedata(root/f'blender/hole_{n:02}.blend');row['original_fbx']=filedata(root/f'Unity/Assets/Resources/Course/hole_{n:02}.fbx');row['authored_marker_types']=source[str(n)]['types']
 else:row['procedural_source']='Unity/Assets/Scripts/Course/HoleView.cs BuildGeometry; original gameplay preserved'
 candidate=root/f'Unity/Assets/Resources/Course/Resort/Finish_{n:02}.fbx'
 if candidate.exists():row['separate_finish_candidate']=filedata(candidate)
 rows.append(row)
(proof/'catalog-coverage-source.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'catalog_rows':len(rows),'pilot_budgets':budget},indent=2))
