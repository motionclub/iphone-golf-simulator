from pathlib import Path
import subprocess,hashlib,json
root=Path(__file__).parent

def change(s,name):
 if name=='TennisFx':
  pairs=[('if (velocity != default) p.velocity = velocity;','if (velocity != default) p.velocity = velocity * GolfArcade.EnvironmentArt.EnvironmentFx.MotionScale;'),('ps.Emit(p, count);','ps.Emit(p, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleCount(count));'),('Burst(streak, at, 1, new Color(c.r, c.g, c.b, .95f)','Burst(streak, at, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i), new Color(c.r, c.g, c.b, .95f)'),('Burst(confetti, at + Vector3.up * 1.6f, 1, c, -1, v);','Burst(confetti, at + Vector3.up * 1.6f, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i), c, -1, v);')]
  for a,b in pairs:
   assert s.count(a)==1,(name,a,s.count(a));s=s.replace(a,b)
 else:
  start=s.index('        public void Touchdown(');a,b=s[:start],s[start:]
  assert b.count('Emit(p, 1);')==3 and b.count('}, 1);')==3
  b=b.replace('Emit(p, 1);','Emit(p, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));').replace('}, 1);','}, GolfArcade.EnvironmentArt.EnvironmentFx.ParticleAt(i));');s=a+b
 return s
report=[]
for name,part in [('TennisFx','Tennis'),('ShotEffects','Game')]:
 p=Path('Unity/Assets/Scripts')/part/(name+'.cs')
 old=(root/'reduced-motion-original'/(name+'.cs')).read_text()
 assert change(old,name)==p.read_text(),'Unexpected additional worktree changes: '+str(p)
 indexed=subprocess.check_output(['git','show',':'+str(p)],text=True)
 backup=root/'reduced-motion-original'/(name+'.index.cs');assert not backup.exists(),'Already staged once'
 backup.write_text(indexed);updated=change(indexed,name)
 oid=subprocess.check_output(['git','hash-object','-w','--stdin'],input=updated,text=True).strip()
 subprocess.run(['git','update-index','--cacheinfo','100644',oid,str(p)],check=True)
 report.append({'path':str(p),'indexBeforeSha256':hashlib.sha256(indexed.encode()).hexdigest(),'indexAfterOid':oid,'preservedUnstagedEdits':True})
(root/'reduced-motion-stage-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Staged only the reduced-motion additions; previous unstaged FX edits remain unstaged.')
