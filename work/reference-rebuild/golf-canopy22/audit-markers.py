import bpy,json,hashlib
from pathlib import Path
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/reference-rebuild/golf-canopy22'
reports=[]
for n in [16,19,21,22,23]:
 p=R/f'blender/hole_{n}.blend';bpy.ops.wm.open_mainfile(filepath=str(p));markers=[]
 for o in bpy.data.objects:
  if not o.name.startswith('PLANT_'):continue
  bits=o.name.split('_')
  if len(bits)<5:continue
  try:height=int(bits[3])*.01;radius=int(bits[4])*.01
  except ValueError:continue
  markers.append(dict(name=o.name,kind=bits[2],height=height,radius=radius,worldMatrix=[list(row) for row in o.matrix_world]))
 trees=[m for m in markers if m['kind']=='T'];reports.append(dict(hole=n,source=str(p),sourceSHA256=hashlib.sha256(p.read_bytes()).hexdigest(),markerCount=len(markers),treeCount=len(trees),markers=markers))
 print('HOLE',n,'TREES',len(trees),'MARKERS',len(markers),flush=True)
(W/'marker-identity.json').write_text(json.dumps({'scope':'Read-only source snapshot; original transforms preserved by loader-only candidate diff','holes':reports},indent=2)+'\n')
