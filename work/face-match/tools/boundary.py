from pathlib import Path
import numpy as np
from collections import Counter
from PIL import Image, ImageDraw
root=Path('work/face-match/17-closure/raw')
for sex in ['male','female']:
 a=np.genfromtxt(root/f'{sex}_head.csv',delimiter=',',names=True);p=np.array([a[k] for k in ['x','y','z']]).T
 _,inv=np.unique(np.round(p,6),axis=0,return_inverse=True)
 t=np.fromstring((root/f'{sex}_head_0.txt').read_text(),sep=',',dtype=int).reshape(-1,3)
 edges=Counter(tuple(sorted(e)) for tri in inv[t] for e in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])])
 unique=np.unique(np.round(p,6),axis=0)
 bd=np.array([e for e,n in edges.items() if n==1]);e=unique[bd]
 sel=(e[:,:,2].mean(axis=1)>-.025)&(np.abs(e[:,:,0]).max(axis=1)<.1)&(np.abs(e[:,:,1]).max(axis=1)<.05)
 print(sex,'boundary',sum(sel),e[sel].min(axis=(0,1)),e[sel].max(axis=(0,1)))
 im=Image.new('RGB',(1000,500),'white');d=ImageDraw.Draw(im)
 for line in e[sel]:d.line([(500+v[0]*4500,250-v[1]*4500) for v in line],fill='black',width=2)
 im.save(root/f'{sex}_boundary.png')
 np.savetxt(root/f'{sex}_boundary.csv',e[sel].reshape(-1,6),delimiter=',')
