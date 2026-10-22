"""CPU only. Compare fresh control/candidate audit.txt; no editor or GPU launch."""
import json,re,sys,numpy as np
from pathlib import Path
control,candidate=map(Path,sys.argv[1:3]);out=Path(sys.argv[3]) if len(sys.argv)>3 else candidate/'wrist-contract-audit.json'
def read(folder):
 d={}
 for line in (folder/'audit.txt').read_text().splitlines():
  m=re.match(r'(\w+) (before|after): (.*)',line)
  if not m:continue
  d.setdefault(m[1],{})[m[2]]={n:np.array([float(v) for v in (p+','+q).split(',')]) for n,p,q in re.findall(r'(\w+) p=\(([^)]+)\) q=\(([^)]+)\)',m[3])}
 return d
A,B=read(control),read(candidate);fails=[];rows=[];drift=0.;club=0.
if set(A)!=set(B):fails.append('Control/candidate labels differ')
for label in sorted(set(A)&set(B)):
 a,b=A[label],B[label]
 if set(a)!={'before','after'} or set(b)!={'before','after'}:fails.append(label+': missing settle stamps');continue
 c=np.max(abs(a['after']['Club']-b['after']['Club']));club=max(club,float(c))
 if c!=0:fails.append(label+': Club serialized world TRS differs')
 for role,data in [('control',a),('candidate',b)]:
  for name in data['after']:
   delta=np.max(abs(data['after'][name]-data['before'][name]));drift=max(drift,float(delta))
   if delta>1e-6:fails.append(label+': '+role+' '+name+' changes while frozen')
 changes={}
 for name in ('LeftLowerArm','RightLowerArm','LeftHand','RightHand'):
  mm=float(np.linalg.norm(b['after'][name][:3]-a['after'][name][:3])*1000/1.0936);changes[name]=mm
  if mm>40.1:fails.append(label+': '+name+' exceeds40mm model displacement (+0.1mm serialized tolerance)')
 rows.append({'label':label,'clubMaxSerializedDelta':float(c),'modelShiftMm':changes})
expected={f'{sex}_{club}_{stage}' for sex in ('male','female') for club in ('Driver','Iron','PitchingWedge','Wedge','Putter') for stage in ('address','top','contact','follow')}
for folder in (control,candidate):
 poses={p.stem for p in (folder/'poses').glob('*.json')}
 if not expected<=poses:fails.append(str(folder)+': missing full landmark poses')
 for label in expected:
  for view in ('front34','back34','grip'):
   if not (folder/(label+'_'+view+'.png')).exists():fails.append(str(folder)+': missing '+label+'_'+view)
 if len(list((folder/'matrices').glob('*.json')))!=310:fails.append(str(folder)+': expected310 dense matrices (2sex*5clubs*31)')
report={'gate':'FAIL' if fails else 'TECHNICAL_CONTRACT_PASS_ART_PENDING','landmarks':40,'auditLabels':len(rows),'maxClubSerializedDelta':club,'maxFrozenTransformDelta':drift,'failures':fails,'samples':rows,'note':'Known golf root world scale1.0936 yards/metre. Checks Club path, frozen pose drift, movement bounds and completeness; does not certify source finger preservation or visual quality. Legacy control may canonicalize fingers differently, so candidate/control local-digit equality is not a valid authoring gate.'}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('samples',)},indent=2));sys.exit(1 if fails else 0)
