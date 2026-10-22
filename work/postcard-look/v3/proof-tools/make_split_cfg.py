#!/usr/bin/env python3
"""Copy the exact frozen baseline shoreline to proof config; never invent two rings."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args();r=a.root.resolve();source=r/'work/postcard-look/v3/audit/split_frozen_boundary.json';d=json.loads(source.read_text());loops=d['actual_baseline_top_loops']
if len(loops)!=1:raise SystemExit('Expected audited frozen single C-shaped outer ring; review changed topology')
for file,field in [('source_design','source_design_sha256'),('baseline_blend','baseline_blend_sha256')]:
 if hashlib.sha256((r/d[file]).read_bytes()).hexdigest()!=d[field]:raise SystemExit('Frozen source SHA mismatch: '+d[file])
loop=loops[0];edges=loop['directed_edges'];joins=[e['index'] for e in edges if e['group']=='joins'];parts=[]
for group in ('ridge','fairway'):
 parts.append({'name':group+'_shore_with_shared_north_south_joins','edgeStarts':sorted([e['index'] for e in edges if e['group']==group]+joins)})
covered=set().union(*(set(x['edgeStarts']) for x in parts))
if covered!=set(range(len(loop['points_unity_world_xz_yd']))):raise SystemExit('Unclassified source edge; cannot silently drop denominator')
cfg={'playY':d['play_top_world_y_yd'],'waterY':d['sea_base_world_y_yd'],'cliffNearPixels':2,'surfBaseNearPixels':6,'frozenShoreXZ':[v for xy in loop['points_unity_world_xz_yd'] for v in xy],'parts':parts,'frozenBoundarySource':str(source),'frozenBoundarySha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sharedJoinOriginalEdges':joins,'note':'One closed frozen outer ring. Both semantic groups include the explicitly shared joins; no virtual closing edges. Two independent island polygons are unavailable. Actual top/cliff masks remain whole-ground masks.'}
out=(a.out or r/'work/postcard-look/v3/proof/split_outline_cfg.json').resolve()
if not out.is_relative_to(r/'work/postcard-look/v3'):raise SystemExit('Output must be beneath v3')
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(cfg,indent=2)+'\n');print(out);print('Frozen boundary edges:',len(edges),'ridge+joins:',len(parts[0]['edgeStarts']),'fairway+joins:',len(parts[1]['edgeStarts']),'shared joins:',len(joins))
