"""Root-owned serial Unity export. Explicit work output, accepted original source."""
from pathlib import Path
import argparse,json,os,subprocess
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2]
p=argparse.ArgumentParser();p.add_argument('--editor',required=True);p.add_argument('--profile',choices=['tennis','tennis-distance','golf','legacy-control']);args=p.parse_args()
config=json.loads((TASK/'export-configs.json').read_text())
for id in [args.profile] if args.profile else config['serial_order']:
 job=config['profiles'][id]
 for name in ['MH_LOCKER_OUT','MH_LOCKER_GOLDEN','MH_LOCKER_REPORT']:
  assert Path(job['environment'][name]).is_relative_to(TASK),'Output escaped work task'
 command=[args.editor,'-batchmode','-nographics','-quit','-projectPath',config['projectPath'],'-executeMethod',job['method'],'-logFile',job['logFile']]
 result=subprocess.run(command,cwd=REPO,env=dict(os.environ,**job['environment']))
 if result.returncode:raise SystemExit(result.returncode)
 log=Path(job['logFile']).read_text(errors='replace')
 assert 'Exception:' not in log and 'error CS' not in log,'Unity source/export failure; inspect '+job['logFile']
 print(id+' export completed',flush=True)
