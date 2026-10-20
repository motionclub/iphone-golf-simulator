"""Summarize completed root-owned actual captures; never substitute source estimates."""
from pathlib import Path
import json,sys
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
checkpoint=int(sys.argv[1]);photos=root/sys.argv[2];costs=root/sys.argv[3]
proof=root/'proof/full-visual-overhaul/golf';holes=[1,2,3,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23]
physics=[];frames=[];missing=[]
for n in holes:
 p=photos/f'hole{n:02}_dressing_physics.json'
 if not p.exists():missing.append(str(p));continue
 d=json.loads(p.read_text());physics.append({'hole':n,'gate':d['gate'],'colliders':len(d['before']['colliders']),'report':str(p.relative_to(root))})
 p=costs/f'hole{n:02}_tee.frame_costs.json'
 if not p.exists():missing.append(str(p));continue
 d=json.loads(p.read_text());frames.append({'hole':n,'status':d['status'],'drawCallGate':d['drawCallGate'],'drawCalls':d['drawCalls'],'setPass':d['setPass'],'triangles':d['triangles'],'scope':d['scope'],'report':str(p.relative_to(root))})
if missing:raise SystemExit('Incomplete actual catalog; no report promoted. Missing: '+', '.join(missing))
pg='PASS' if all(x['gate']=='PASS' for x in physics) else 'FAIL';cg='PASS' if all(x['status']=='PASS' and x['drawCallGate']=='PASS' for x in frames) else 'FAIL'
(proof/f'catalog-runtime-physics-pass{checkpoint}.json').write_text(json.dumps({'checkpoint':checkpoint,'scope':'Actual synchronous Unity editor dressing parity; canonical HEAD source/hash evidence separate','expected_holes':19,'captured_holes':len(physics),'gate':pg,'holes':physics},indent=2)+'\n')
(proof/f'catalog-frame-costs-pass{checkpoint}.json').write_text(json.dumps({'checkpoint':checkpoint,'expected_holes':19,'measured_holes':len(frames),'gate':cg,'scope':'Actual completed sole automatic Game-camera frames on editor Metal; no device frame-time inference','holes':frames},indent=2)+'\n')
print(json.dumps({'checkpoint':checkpoint,'physics':pg,'costs':cg,'max_draws':max(x['drawCalls'] for x in frames),'max_triangles':max(x['triangles'] for x in frames),'holes':19}))
