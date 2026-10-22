"""Compare paired Unity control/candidate invariants; usage: python script.py CONTROL CANDIDATE."""
import sys,json,pathlib,numpy as np
A,B=map(pathlib.Path,sys.argv[1:3]);rows=[];failed=[]
for p in sorted(A.glob('*.json')):
 q=B/p.name
 if not q.exists():failed.append('Missing candidate '+p.name);continue
 a=json.loads(p.read_text());b=json.loads(q.read_text());aa={r['name']:np.array(r['matrix']).reshape(4,4) for r in a['preserved']};bb={r['name']:np.array(r['matrix']).reshape(4,4) for r in b['preserved']};maxpos=maxangle=maxmatrix=0.;worst=''
 if aa.keys()!=bb.keys():failed.append('Transform set mismatch '+p.name);continue
 for n in aa:
  m=aa[n];k=bb[n];pos=float(np.linalg.norm(m[:3,3]-k[:3,3]));u,_,v=np.linalg.svd(m[:3,:3]);ma=u@v;u,_,v=np.linalg.svd(k[:3,:3]);ka=u@v;angle=float(np.degrees(np.arccos(np.clip((np.trace(ma.T@ka)-1)*.5,-1,1))));error=float(np.max(abs(m-k)))
  if pos>maxpos:maxpos=pos;worst=n
  maxangle=max(maxangle,angle);maxmatrix=max(maxmatrix,error)
 contacterror=float(np.linalg.norm(np.array(a['authoredContactLocal'])-b['authoredContactLocal']));timeerror=abs(a['contactTime']-b['contactTime']);row={'label':a['label'],'time':a['sampleTime'],'maxPreservedPositionMetres':maxpos,'maxPreservedAngleDegrees':maxangle,'maxPreservedMatrixElementError':maxmatrix,'worstPosition':worst,'authoredContactLocalErrorMetres':contacterror,'contactTimeErrorSeconds':timeerror,'preservedTransformCount':len(aa),'pass':maxpos<1e-5 and maxangle<.001 and maxmatrix<1e-5 and contacterror<1e-7 and timeerror==0};rows.append(row)
 if not row['pass']:failed.append(a['label'])
report={'gate':'PASS' if rows and not failed else 'FAIL','samples':len(rows),'failures':failed,'rows':rows};print(json.dumps(report,indent=2));sys.exit(bool(failed or not rows))
