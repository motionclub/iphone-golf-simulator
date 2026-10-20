from pathlib import Path
import os,sys,time,subprocess,signal,json
P=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=P/'work/serve-walk-arm';U='/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity'
mode,clone,stage=sys.argv[1:4];shard=int(sys.argv[4]) if mode=='matrix' and len(sys.argv)>4 else 0;cases=[]
if mode=='matrix':
 n=0
 for role in ['player','opponent']:
  for sex in ['male','female']:
   for side in ['deuce','ad']:
    for control in [0,1]:
     if n%3==shard:cases.append((f'{role}-{sex}-rh-{side}-'+('control' if control else 'walk'),role,sex,side,control,0))
     n+=1
elif mode in ['film','plant']:
 cases=[(f'{role}-{sex}-rh-deuce',role,sex,'deuce',0,int(mode=='film')) for role in ['player','opponent'] for sex in ['male','female']]
elif mode=='case':
 name,role,sex,side,control=sys.argv[4].split(',');cases=[(name,role,sex,side,int(control),0)]
elif mode=='input':cases=[(f'{sex}-rh-{side}','player',sex,side,0,1) for sex in ['male','female'] for side in ['deuce','ad']]
def active():
 out=[]
 for l in subprocess.check_output(['ps','-axo','pid=,args='],text=True).splitlines():
  if U+' -batchmode -projectPath '+str(W/clone)+' -executeMethod' in l:
   out.append((int(l.split()[0]),l))
 return out
# Adopt only an existing proof for this exact clone and stage; leave any other process alone.
for pid,args in active():
 if '/logs_r2/'+stage not in args and not (mode=='input' and '/logs_r2/input-r2-v30-' in args):raise RuntimeError('Clone has a different active run')
 # Existing film/plant log names omit rh-deuce; completion must match sex/role from filename.
 if any(p==pid for p,_ in active()):
  proof=None
  for name,role,sex,side,*_ in cases:
   match=(f'{stage}-{role}-{sex}.log' in args if mode in ['film','plant'] else f'input-r2-v30-{sex}-{side}.log' in args if mode=='input' else f'{stage}-{name}.log' in args)
   if match:proof=W/stage/name/'completed.json';break
  if not proof or not proof.exists():
   while any(p==pid for p,_ in active()) and not (proof and proof.exists()):time.sleep(2)
  if any(p==pid for p,_ in active()):os.kill(pid,signal.SIGTERM);print('Closed completed adopted proof',pid,flush=True)
 while any(p==pid for p,_ in active()):time.sleep(1)
for name,role,sex,side,control,images in cases:
 out=W/stage/name;done=out/'completed.json'
 if done.exists():print('Retained completed',name,flush=True);continue
 env=os.environ.copy();env.update(SW_IMAGES=str(images),SW_ROLE=role,SW_FEMALE=str(int(sex=='female')),SW_SIDE=side,SW_CONTROL_ONLY=str(control),SW_OUT=str(out))
 if mode=='input':env.update(SW_INPUT_PATH='adapter',SW_DURATION='9')
 if mode=='plant':env['SW_PLANT_SNAPSHOT']='1'
 log=W/'logs_r2'/f'{stage}-{name}.log'
 for attempt in range(3):
  proc=subprocess.Popen([U,'-batchmode','-projectPath',str(W/clone),'-executeMethod','GolfArcade.EditorTools.ServeWalkFilm.Run','-logFile',str(log)],env=env)
  while proc.poll() is None and not done.exists():time.sleep(2)
  if done.exists():break
  text=log.read_text(errors='replace') if log.exists() else ''
  if 'Could not establish a connection with the Unity Package Manager local server process' not in text:break
  archive=log.parent/(log.stem+f'.UPM_STARTUP_FAILURE_{attempt+1}.log')
  if archive.exists():archive=log.parent/(log.stem+f'.UPM_STARTUP_FAILURE_{attempt+1}_{time.time_ns()}.log')
  archive.write_text(text)
  print('Retrying local package-manager startup',name,flush=True);time.sleep(2)
 if not done.exists():raise RuntimeError(f'Failed {name}: {proc.returncode}; {log}')
 try:proc.wait(timeout=10)
 except subprocess.TimeoutExpired:
  proc.terminate()
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
  print('Closed after completed proof',name,flush=True)
 print('Completed',name,flush=True)
