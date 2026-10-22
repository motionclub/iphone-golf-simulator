exec(open('work/reference-rebuild/golf-wrist29/analyze.py').read().split('report={}')[0])
out=[]
for sex in ('Male','Female'):
 d=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text());rig=d['rig'];names=rig['bones'];raw=(W/f'{sex}.rig.raw').read_bytes()
 for ci in rig['clips']:
  if not ci['id'].startswith('golf'):continue
  t=np.frombuffer(raw,'<f4',ci['frames']*rig['trackCount']*10,ci['offset']).reshape(ci['frames'],rig['trackCount'],10)
  times=np.array(ci.get('times',np.linspace(0,ci['length'],ci['frames'])));land=json.loads((R/f'Unity/Assets/Resources/Hero/golfer_{"f" if sex=="Female" else "m"}_clips.json').read_text())['clips'];land=next(x for x in land if x['name']==ci['name'])
  for stage,time in [('address',0),('top',land['top']/land['fps']),('contact',ci['contact']),('follow',ci['length']*.92)]:
   frame=int(np.argmin(abs(times-time)));tracks=t[frame];row={'sex':sex,'clip':ci['id'],'stage':stage,'time':float(times[frame]),'sides':{}}
   for side in ('Left','Right'):
    root=tracks[names.index(side+'UpperArm'),:3];elbow=tracks[names.index(side+'LowerArm'),:3];hand=tracks[names.index(side+'Hand'),:3];middle=tracks[names.index(side+'MiddleProximal'),:3];palm=(middle-hand);palm/=np.linalg.norm(palm);a=np.linalg.norm(elbow-root);b=np.linalg.norm(hand-elbow);axis=(hand-root);dist=np.linalg.norm(axis);axis/=dist;along=(a*a-b*b+dist*dist)/(2*dist);radius=np.sqrt(max(0,a*a-along*along));centre=root+axis*along;old=(elbow-centre);old/=np.linalg.norm(old);ideal=-palm+axis*np.dot(palm,axis);ideal/=np.linalg.norm(ideal);best=centre+ideal*radius
    angle=lambda E:float(np.degrees(np.arccos(np.clip(np.dot((hand-E)/np.linalg.norm(hand-E),palm),-1,1))))
    original=angle(elbow);lo=0.;hi=1.;turn=np.arccos(np.clip(old@ideal,-1,1))
    def lerp(u):
     if turn<1e-6:return old
     if abs(np.sin(turn))<1e-6:return ideal
     return (np.sin((1-u)*turn)*old+np.sin(u*turn)*ideal)/np.sin(turn)
    if original<=45:new=elbow
    else:
     for _ in range(24):
      mid=(lo+hi)/2;ang=angle(centre+lerp(mid)*radius)
      if ang>45:lo=mid
      else:hi=mid
     new=centre+lerp(hi)*radius
    row['sides'][side]={'originalAngle':original,'minimumAngle':angle(best),'candidateAngle':angle(new),'elbowDisplacementMm':float(np.linalg.norm(new-elbow)*1000),'circleTurnDegrees':float(np.degrees(turn)),'oldElbow':elbow.tolist(),'newElbow':new.tolist(),'hand':hand.tolist(),'shoulder':root.tolist()}
   out.append(row)
(W/'fixed-grip-feasibility.json').write_text(json.dumps(out,indent=2)+'\n')
for s in out:
 print(s['sex'],s['clip'],s['stage'],[(k,round(v['originalAngle']),round(v['minimumAngle']),round(v['candidateAngle']),round(v['elbowDisplacementMm'])) for k,v in s['sides'].items()])
