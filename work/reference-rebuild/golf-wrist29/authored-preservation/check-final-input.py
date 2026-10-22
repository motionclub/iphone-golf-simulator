import json,importlib.util,numpy as np,re,sys
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29/authored-preservation';spec=importlib.util.spec_from_file_location('fbxread',W/'read-fbx.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
actual=Path(sys.argv[1]) if len(sys.argv)>1 else R/'proof/reference-rebuild/golf-wrist29-continuous3';S=np.diag([-1.,1.,1.]);ticks=46186158000.;rows=[]
def euler(q):
 x,y,z=np.radians(q);cx,sx=np.cos(x),np.sin(x);cy,sy=np.cos(y),np.sin(y);cz,sz=np.cos(z),np.sin(z);return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def rotation_angle(M):
 u,_,v=np.linalg.svd(M);return float(np.degrees(np.arccos(np.clip((np.trace(u@v)-1)/2,-1,1))))
for sex in ('Male','Female'):
 f=mod.Fbx(R/f'Unity/Assets/Resources/Hero/golfer_{"m" if sex=="Male" else "f"}.fbx');objects={n['p'][0]:n for n in f.root('Objects')['c']};connections=[c['p'] for c in f.root('Connections')['c']];models={n['p'][1].split('\0')[0]:i for i,n in objects.items() if n['n']=='Model'};clips=json.loads((R/f'Unity/Assets/Resources/Hero/golfer_{"m" if sex=="Male" else "f"}_clips.json').read_text())['clips']
 def props(node):return {p['p'][0]:p['p'][4:] for n in node['c'] if n['n']=='Properties70' for p in n['c']}
 for path in sorted((actual/'poses').glob(sex.lower()+'_*.json')):
  d=json.loads(path.read_text());label=d['label'];parts=label.split('_');club,stage=parts[1:];clip='Drive' if club=='Driver' else 'Putt';mark=next(c for c in clips if c['name']==clip);time=0 if stage=='address' else mark['top']/mark['fps'] if stage=='top' else mark['impact']/mark['fps'];stack=next(i for i,n in objects.items() if n['n']=='AnimationStack' and n['p'][1].split('\0')[0]==clip);layer=next(c[1] for c in connections if c[:1]==['OO'] and c[2]==stack);nodes={c[1] for c in connections if c[:1]==['OO'] and c[2]==layer}
  def sampled(model,kind,t):
   base=props(objects[model]).get(kind,[0.,0.,0.] if kind!='Lcl Scaling' else [1.,1.,1.]);vals=np.array(base,float);nc=next((c[1] for c in connections if c[:1]==['OP'] and c[2]==model and c[3]==kind and c[1] in nodes),None)
   if nc is not None:
    for c in connections:
     if c[:1]!=['OP'] or c[2]!=nc:continue
     axis='XYZ'.index(c[3][-1]);keys={n['n']:n['p'][0] for n in objects[c[1]]['c']};vals[axis]=np.interp(t,np.array(keys['KeyTime'],float)/ticks,np.array(keys['KeyValueFloat']))
   return vals
  p=next(x for x in d['parts'] if x['name']=='Body');names=p['bones'];world=np.array(p['skinMatrices']).reshape(-1,4,4)@np.linalg.inv(np.array(p['bindposes']).reshape(-1,4,4));errs=[]
  for side in ('Left','Right'):
   for digit in ('Thumb','Index','Middle','Ring','Little'):
    parent=names.index(side+'Hand')
    for joint in ('Proximal','Intermediate','Distal'):
     name=side+digit+joint;i=names.index(name);local=np.linalg.inv(world[parent])@world[i];mid=models[name];expected=S@euler(sampled(mid,'Lcl Rotation',time))@S;actualScale=np.linalg.norm(local[:3,:3],axis=0);rotation=local[:3,:3]/actualScale;positionError=np.linalg.norm(local[:3,3]-S@sampled(mid,'Lcl Translation',time))*1000;rotError=rotation_angle(rotation@expected.T);scaleError=np.max(abs(actualScale-sampled(mid,'Lcl Scaling',time)));errs.append({'bone':name,'rotationErrorDegrees':rotError,'positionErrorMm':float(positionError),'scaleError':float(scaleError)});parent=i
  row={'label':label,'inputFBXClip':clip,'time':time,'maxRotationErrorDegrees':max(e['rotationErrorDegrees'] for e in errs),'maxPositionErrorMm':max(e['positionErrorMm'] for e in errs),'maxScaleError':max(e['scaleError'] for e in errs),'joints':errs};rows.append(row);print(label,'rotation',row['maxRotationErrorDegrees'],'positionMM',row['maxPositionErrorMm'],'scale',row['maxScaleError'])
report={'gate':'ACTUAL_AUTHORED_DIGITS_PASS' if len(rows)==12 and max(r['maxRotationErrorDegrees'] for r in rows)<.01 and max(r['maxPositionErrorMm'] for r in rows)<.01 else 'FAIL','poses':len(rows),'joints':len(rows)*30,'input':'exact active golfer_m/f.fbx AnimationCurve samples; named source clip landmark times; FBX local XYZ rotation mapped by Unity importer X reflection, independently verified against raw address control','actual':'final Body skinMatrices*inverseBind inverse; derive each digit local relative to its actual parent after capture settlement','maximumRotationErrorDegrees':max(r['maxRotationErrorDegrees'] for r in rows),'maximumPositionErrorMm':max(r['maxPositionErrorMm'] for r in rows),'maximumScaleError':max(r['maxScaleError'] for r in rows),'rows':rows,'note':'Direct actual vs input clip digit TRS. This is not a wrist-shape, contact or appearance pass.'};(W/'continuous3-authored-digit-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('GATE',report['gate'])
