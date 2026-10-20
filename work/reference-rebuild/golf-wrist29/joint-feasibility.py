exec(open('work/reference-rebuild/golf-wrist29/analyze.py').read().split('report={}')[0])
def turn(axis,a):
 a=np.radians(a);K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);return np.eye(3)+np.sin(a)*K+(1-np.cos(a))*(K@K)
rows=[]
for sex in ('Male','Female'):
 d=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text());rig=d['rig'];names=rig['bones'];raw=(W/f'{sex}.rig.raw').read_bytes()
 def F(o,n):return np.frombuffer(raw,'<f4',n,o)
 clubaxes={}
 for cp in rig['parts']:
  if not cp['part'].startswith('Club_'):continue
  v=F(cp['bindPositionOffset'],cp['vertexCount']*3).reshape(-1,3);bind=F(cp['inverseBindOffset'],len(cp['bones'])*16).reshape(-1,4,4);ci=cp['bones'].index(names.index('Club'));vs=v@bind[ci,:3,:3].T+bind[ci,:3,3];end=vs[np.argmax(np.linalg.norm(vs,axis=1))];axis=np.zeros(3);j=np.argmax(abs(end));axis[j]=np.sign(end[j]);clubaxes[cp['part']]=axis
 for ci in rig['clips']:
  if not ci['id'].startswith('golf'):continue
  local=clubaxes[{'golfDrive':'Club_Driver','golfIron':'Club_Iron','golfHalf':'Club_Iron','golfChip':'Club_Wedge','golfPutt':'Club_Putter'}[ci['id']]]
  tr=F(ci['offset'],ci['frames']*rig['trackCount']*10).reshape(ci['frames'],rig['trackCount'],10);times=np.array(ci.get('times',np.linspace(0,ci['length'],ci['frames'])));land=next(x for x in json.loads((R/f'Unity/Assets/Resources/Hero/golfer_{"f" if sex=="Female" else "m"}_clips.json').read_text())['clips'] if x['name']==ci['name'])
  for stage,time in [('address',0),('top',land['top']/land['fps']),('contact',ci['contact']),('follow',ci['length']*.92)]:
   frame=int(np.argmin(abs(times-time)));t=tr[frame];C=t[names.index('Club')];shaft=qmat(C[3:7])@(local*C[7:10]);shaft/=np.linalg.norm(shaft);origin=C[:3];row={'sex':sex,'clip':ci['id'],'stage':stage,'sides':{}}
   for side in ('Left','Right'):
    shoulder=t[names.index(side+'UpperArm'),:3];elbow=t[names.index(side+'LowerArm'),:3];wrist=t[names.index(side+'Hand'),:3];palm=t[names.index(side+'MiddleProximal'),:3]-wrist;palm/=np.linalg.norm(palm);a=np.linalg.norm(elbow-shoulder);b=np.linalg.norm(wrist-elbow)
    def angle(H,E,P):return float(np.degrees(np.arccos(np.clip((H-E)@P/np.linalg.norm(H-E),-1,1))))
    oldangle=angle(wrist,elbow,palm);best={'roll':0,'angle':oldangle,'wrist':wrist,'elbow':elbow,'cost':oldangle*oldangle}
    for theta in (range(-45,46) if oldangle>35 else [0]):
     T=turn(shaft,theta);H=origin+T@(wrist-origin)
     if np.linalg.norm(H-wrist)>.04:continue
     axis=H-shoulder;dist=np.linalg.norm(axis);axis/=dist
     if dist>=a+b-.00001 or dist<=abs(a-b)+.00001:continue
     along=(a*a-b*b+dist*dist)/(2*dist);radius=np.sqrt(max(0,a*a-along*along));centre=shoulder+axis*along;pole=elbow-centre;pole-=axis*(pole@axis)
     if np.linalg.norm(pole)<1e-6:continue
     E=centre+pole/np.linalg.norm(pole)*radius;de=np.linalg.norm(E-elbow)
     if de>.04:continue
     A=angle(H,E,T@palm);cost=A*A+.12*theta*theta+50000*de*de
     if cost<best['cost']:best=dict(roll=theta,angle=A,wrist=H,elbow=E,cost=cost)
    u=float(np.clip((oldangle-35)/15,0,1));roll=best['roll']*u*u*(3-2*u)
    if abs(roll)>1e-4:
     T=turn(shaft,roll);H=origin+T@(wrist-origin);axis=H-shoulder;dist=np.linalg.norm(axis);axis/=dist;along=(a*a-b*b+dist*dist)/(2*dist);radius=np.sqrt(max(0,a*a-along*along));centre=shoulder+axis*along;pole=elbow-centre;pole-=axis*(pole@axis);E=centre+pole/np.linalg.norm(pole)*radius
     if np.linalg.norm(E-elbow)<=.04:best.update(roll=roll,angle=angle(H,E,T@palm),wrist=H,elbow=E)
     else:best.update(roll=0,angle=oldangle,wrist=wrist,elbow=elbow)
    row['sides'][side]={'originalAngle':oldangle,'candidateAngle':best['angle'],'rollDegrees':best['roll'],'elbowShiftMm':float(np.linalg.norm(best['elbow']-elbow)*1000),'wristShiftMm':float(np.linalg.norm(best['wrist']-wrist)*1000)}
   rows.append(row)
(W/'joint-grip-feasibility.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(r['sex'],r['clip'],r['stage'],[(s,round(v['originalAngle']),round(v['candidateAngle']),v['rollDegrees'],round(v['elbowShiftMm']),round(v['wristShiftMm'])) for s,v in r['sides'].items()])
