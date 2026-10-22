import json,importlib.util,numpy as np,re
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/authored-preservation';s=importlib.util.spec_from_file_location('fbxread',W/'read-fbx.py');mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod);S=np.diag([-1.,1.,1.]);ticks=46186158000.
def euler(q):
 x,y,z=np.radians(q);cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z);return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def qm(q):
 q=q/np.linalg.norm(q);x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def angle(M):return float(np.degrees(np.arccos(np.clip((np.trace(M)-1)/2,-1,1))))
def audits(folder):
 rows={}
 for line in (folder/'audit.txt').read_text().splitlines():
  if ' after: ' not in line:continue
  label=line.split(' after: ')[0];rows[label]={n:np.array([float(v) for v in(p+','+q).split(',')]) for n,p,q in re.findall(r'(\w+) p=\(([^)]+)\) q=\(([^)]+)\)',line)}
 return rows
A=audits(R/'proof/reference-rebuild/golf-wrist29-continuous3');C=audits(R/'proof/reference-rebuild/golf-wrist29-tiny-control');rows=[]
for sex in ('Male','Female'):
 f=mod.Fbx(R/f'Unity/Assets/Resources/Hero/golfer_{"m" if sex=="Male" else "f"}.fbx');objects={n['p'][0]:n for n in f.root('Objects')['c']};connections=[c['p'] for c in f.root('Connections')['c']];models={n['p'][1].split('\0')[0]:i for i,n in objects.items() if n['n']=='Model'};clips=json.loads((R/f'Unity/Assets/Resources/Hero/golfer_{"m" if sex=="Male" else "f"}_clips.json').read_text())['clips'];mid=models['Club'];parent=next(c[2] for c in connections if c[:2]==['OO',mid] and objects[c[2]]['n']=='Model')
 def props(node):return {p['p'][0]:p['p'][4:] for n in node['c'] if n['n']=='Properties70' for p in n['c']}
 rigRot=S@euler(props(objects[parent])['Lcl Rotation'])@S
 for label,bones in A.items():
  if not label.startswith(sex.lower()+'_'):continue
  _,club,stage=label.split('_');clip='Drive' if club=='Driver' else 'Putt';mark=next(c for c in clips if c['name']==clip);time=0 if stage=='address' else mark['top']/mark['fps'] if stage=='top' else mark['impact']/mark['fps'];stack=next(i for i,n in objects.items() if n['n']=='AnimationStack' and n['p'][1].split('\0')[0]==clip);layer=next(c[1] for c in connections if c[:1]==['OO'] and c[2]==stack);nodes={c[1] for c in connections if c[:1]==['OO'] and c[2]==layer}
  def sample(kind):
   vals=np.array(props(objects[mid])[kind],float);nc=next(c[1] for c in connections if c[:1]==['OP'] and c[2]==mid and c[3]==kind and c[1] in nodes)
   for c in connections:
    if c[:1]!=['OP'] or c[2]!=nc:continue
    a='XYZ'.index(c[3][-1]);keys={n['n']:n['p'][0] for n in objects[c[1]]['c']};vals[a]=np.interp(time,np.array(keys['KeyTime'],float)/ticks,np.array(keys['KeyValueFloat']))
   return vals
  pos=np.array([-.75,0,0])+float(np.float32(1.0936))*(rigRot@(S@sample('Lcl Translation')));rot=rigRot@S@euler(sample('Lcl Rotation'))@S;v=bones['Club'];row={'label':label,'sourcePositionErrorMm':float(np.linalg.norm(v[:3]-pos)*1000),'sourceRotationErrorDegrees':angle(qm(v[3:])@rot.T)}
  if label in C:row['matchingTinyControlMaxSerializedDelta']=float(np.max(abs(v-C[label]['Club'])))
  rows.append(row);print(row)
report={'gate':'CLUB_SOURCE_MATCH_PASS' if max(r['sourcePositionErrorMm'] for r in rows)<.01 and max(r['sourceRotationErrorDegrees'] for r in rows)<.01 else 'FAIL_OR_EXISTING_CLEARANCE_DIFFERENCE','poses':len(rows),'rows':rows,'maximumPositionErrorMm':max(r['sourcePositionErrorMm'] for r in rows),'maximumRotationErrorDegrees':max(r['sourceRotationErrorDegrees'] for r in rows),'note':'Direct active FBX Club AnimationCurves composed with Rig FBX root local rotation, importer X reflection and production Stand/root yaw cancellation +world position(-.75,0,0), float32 scale1.0936. Matching tiny controls additionally compare serialized exact Club world p/q.'};(W/'continuous3-club-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('GATE',report['gate'])
