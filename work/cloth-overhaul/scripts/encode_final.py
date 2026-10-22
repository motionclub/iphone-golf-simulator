from pathlib import Path
import subprocess,concurrent.futures
W=Path(__file__).resolve().parents[1];R=W.parents[1];D=R/'ArtDir/screenshots/cloth_overhaul';clips=['ready','forehand','trophy','run','pushups','turntable','shimmer'];jobs=[]
for variant,src in [('before',W/'before_verified'),('after',W/'after_final')]:
 for sex in ['male','female']:
  for clip in clips:
   folder=src/(sex+'_'+clip);expect=180 if clip=='shimmer' else 120
   assert len(list(folder.glob('*.png')))==expect,(folder,expect)
   jobs.append((folder,D/variant/(sex+'_'+clip+'.mp4')))
def encode(job):
 p,out=job;subprocess.run([str(W/'encode'),str(p),str(out)],check=True);return str(out)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for result in pool.map(encode,jobs):print(result,flush=True)
