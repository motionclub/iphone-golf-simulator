"""Root-owned serial Unity export. Explicit work output, accepted original source."""
from pathlib import Path
import argparse,json,os,subprocess,hashlib,time
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2]
p=argparse.ArgumentParser();p.add_argument('--editor',required=True);p.add_argument('--profile',choices=['tennis','tennis-distance','golf']);args=p.parse_args()
config=json.loads((TASK/'export-configs.json').read_text());contract=json.loads((TASK/'accepted-contract.json').read_text())
for source,digest in contract['source_files'].items():assert hashlib.sha256((REPO/source).read_bytes()).hexdigest()==digest,'Frozen source hash changed: '+source
assert hashlib.sha256((REPO/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader').read_bytes()).hexdigest()==contract['unity_palette_shader_sha256'],'Palette shader changed; regenerate exact contract after root accepts final palette'
for id in [args.profile] if args.profile else config['serial_order']:
 job=config['profiles'][id]
 for name in ['MH_LOCKER_OUT','MH_LOCKER_GOLDEN','MH_LOCKER_REPORT']:
  assert Path(job['environment'][name]).is_relative_to(TASK),'Output escaped work task'
 command=[args.editor,'-batchmode','-nographics','-quit','-projectPath',config['projectPath'],'-executeMethod',job['method'],'-logFile',job['logFile']]
 started=time.time();result=subprocess.run(command,cwd=REPO,env=dict(os.environ,**job['environment']))
 if result.returncode:raise SystemExit(result.returncode)
 log=Path(job['logFile']).read_text(errors='replace')
 assert 'Exception:' not in log and 'error CS' not in log,'Unity source/export failure; inspect '+job['logFile']
 identity={'profile':id,'startedUnix':started,'endedUnix':time.time(),'environment':job['environment'],'source_files':contract['source_files'],'unityPaletteShaderSha256':contract['unity_palette_shader_sha256']}
 (TASK/(id+'-export-identity.json')).write_text(json.dumps(identity,indent=2)+'\n')
 print(id+' export completed',flush=True)
