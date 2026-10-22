exec(open('work/reference-rebuild/golf-wrist29/analyze.py').read().split('report={}')[0])
import re
path=R/'proof/reference-rebuild/golf-wrist29-tiny-candidate/audit.txt'
for line in path.read_text().splitlines():
 if ' before: ' not in line:continue
 label=line.split(' before: ')[0];d={}
 for name,pos,q in re.findall(r'(\w+) p=\(([^)]+)\) q=\(([^)]+)\)',line):d[name]=(np.array([float(a) for a in pos.split(',')]),np.array([float(a) for a in q.split(',')]))
 C,Cq=d['Club'];print(label)
 for localAxis in np.eye(3):
  shaft=qmat(Cq)@localAxis;shaft/=np.linalg.norm(shaft)
  for side in ('Left','Right'):
   shoulder=d[side+'UpperArm'][0];elbow=d[side+'LowerArm'][0];wrist=d[side+'Hand'][0];palm=d[side+'MiddleProximal'][0]-wrist;palm/=np.linalg.norm(palm);a=np.linalg.norm(elbow-shoulder);b=np.linalg.norm(wrist-elbow);old=float(np.degrees(np.arccos(np.clip((wrist-elbow)@palm/b,-1,1))));best=(old*old,0,old,0)
   for deg in range(-45,46):
    th=np.radians(deg);K=np.array([[0,-shaft[2],shaft[1]],[shaft[2],0,-shaft[0]],[-shaft[1],shaft[0],0]]);T=np.eye(3)+np.sin(th)*K+(1-np.cos(th))*(K@K);H=C+T@(wrist-C)
    if np.linalg.norm(H-wrist)>.04*1.0936:continue
    axis=H-shoulder;dist=np.linalg.norm(axis);axis/=dist
    if dist>=a+b-.00001 or dist<=abs(a-b)+.00001:continue
    along=(a*a-b*b+dist*dist)/(2*dist);rad=np.sqrt(max(0,a*a-along*along));centre=shoulder+axis*along;pole=elbow-centre;pole-=axis*(pole@axis)
    if np.linalg.norm(pole)<1e-5:continue
    E=centre+pole/np.linalg.norm(pole)*rad;de=np.linalg.norm(E-elbow)
    if de>.04*1.0936:continue
    A=float(np.degrees(np.arccos(np.clip((H-E)@(T@palm)/b,-1,1))));cost=A*A+.12*deg*deg+50000*de*de/(1.0936**2)
    if cost<best[0]:best=(cost,deg,A,de*1000)
   print('axis',localAxis.tolist(),side,'orig',round(old,2),'best',best[1:])
