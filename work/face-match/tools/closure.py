from pathlib import Path
import numpy as np
from collections import Counter
from PIL import Image,ImageDraw
root=Path('work/face-match/20-geometric-normals/raw')
for sex in ['male','female']:
 a=np.genfromtxt(root/f'{sex}_head.csv',delimiter=',',names=True);p=np.array([a[k] for k in ['x','y','z']]).T
 c=np.genfromtxt(root/f'{sex}_closed.csv',delimiter=',',names=True);q=np.array([c[k] for k in ['x','y','z']]).T
 unique,ids,inv=np.unique(np.round(p,6),axis=0,return_index=True,return_inverse=True)
 t=np.fromstring((root/f'{sex}_head_0.txt').read_text(),sep=',',dtype=int).reshape(-1,3)
 edges=Counter(tuple(sorted(e)) for tri in inv[t] for e in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])])
 bd=np.array([e for e,n in edges.items() if n==1]);e=unique[bd]
 sel=(e[:,:,2].mean(axis=1)>-.028)&(np.abs(e[:,:,0]).max(axis=1)<.085)&(np.abs(e[:,:,1]).max(axis=1)<.032)
 im=Image.new('RGB',(1000,600),'white');d=ImageDraw.Draw(im)
 for line,closed in zip(e[sel],q[ids[bd[sel]]]):
  d.line([(500+v[0]*5500,180-v[1]*5500) for v in line],fill='gray',width=2)
  d.line([(500+v[0]*5500,380-v[1]*5500) for v in closed],fill='red' if line[:,1].mean()>0 else 'blue',width=2)
 im.save(root/f'{sex}_closure.png')
 print(sex,'maxOpenBoundaryDisplacement',np.linalg.norm(q[ids[bd[sel]]]-p[ids[bd[sel]]],axis=-1).max())
