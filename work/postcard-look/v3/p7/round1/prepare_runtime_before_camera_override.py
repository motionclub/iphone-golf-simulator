#!/usr/bin/env python3
"""Prepare per-run copies of legacy measurement tools. No checks/builds launched."""
from pathlib import Path
import argparse,json,hashlib
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('run',type=Path);a=p.parse_args();r=a.root.resolve();run=a.run.resolve();v=r/'work/postcard-look/v3'
if not run.is_relative_to(v):raise SystemExit('Run output must be beneath actual v3')
(run/'tools').mkdir(parents=True,exist_ok=True);manifest=[]
for name in ['measure.py','measure_studio.py','make_sheets.py','report.py','installed_mesh_checks.py']:
 src=v/'proof'/name;s=src.read_text();s=s.replace('P = V + "/proof"','P = '+repr(str(run))).replace('P = R + "/work/postcard-look/v3/proof"','P = '+repr(str(run)))
 s=s.replace('ART = R + "/ArtDir/screenshots/golf_postcards/look"','ART = '+repr(str(run/'stills'))).replace('A = R + "/ArtDir/screenshots/golf_postcards/look"','A = '+repr(str(run/'stills')))
 s=s.replace('B = R + "/work/postcard-look/v3/proof/stills_studio"','B = '+repr(str(run/'stills_studio')))
 s=s.replace('R + "/work/postcard-look/v3/proof/studio_compare.json"',repr(str(run/'studio_compare.json')))
 s=s.replace('{V}/runtime','{P}/runtime')
 dst=run/'tools'/('report_legacy.py' if name=='report.py' else name);dst.write_text(s)
 manifest.append({'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'copy':str(dst),'copy_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'changes':'Output/read paths only; original measured thresholds and algorithms preserved.'})
# The exact comparator's original location determines its repo/output paths.
# Copy it into this run with only those two paths adapted; geometry algorithms,
# zero tolerance, original baseline, and installed+staged comparison stay intact.
src=v/'audit/scoring_exact.py';s=src.read_text()
old='REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))'
oldout='OUT = os.path.dirname(os.path.abspath(__file__))'
assert s.count(old)==1 and s.count(oldout)==1, 'Exact comparator adapter source changed'
s=s.replace(old,'REPO = '+repr(str(r))).replace(oldout,'OUT = '+repr(str(run)))
dst=run/'tools/scoring_exact.py';dst.write_text(s)
manifest.append({'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'copy':str(dst),'copy_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'changes':'Repo/output paths only. Exact zero tolerance and all installed+staged blend/FBX checks unchanged.'})
for name in ['stills_cfg_9.json','stills_cfg_extra.json','stills_cfg_12.json']:
 src=v/'proof'/name;d=json.loads(src.read_text());(run/name).write_text(json.dumps(d,indent=2)+'\n')
src=v/'proof-tools/aerial_cfg_3.json';d=json.loads(src.read_text())
assert len(d['shots'])==3 and {x['hole'] for x in d['shots']}=={8,9,10}
assert all(x['name'].endswith('_4_aerial') and x['kind']=='landmark' for x in d['shots'])
(run/'aerial_cfg_3.json').write_text(json.dumps(d,indent=2)+'\n')
shots=json.loads((run/'stills_cfg_12.json').read_text())['shots'];address=[s for s in shots if s.get('kind')=='address']
if len(shots)!=12 or len(address)!=6:raise SystemExit('Fixed config must have12 frames and6 address frames')
(run/'cost_cfg.json').write_text(json.dumps({'shots':address},indent=2)+'\n');(run/'tools_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared path adapters only; thresholds unchanged; exact scoring comparator,12 fixed shots and6 address cost shots retained.')
