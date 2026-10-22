import sys, numpy as np
from PIL import Image
A=sys.argv[1]+'/'; M='../male-silhouette/'
for v in ['bald_front','bald_back']:
    t=np.array(Image.open(M+v+'_target.png').convert('L'))>127
    r=np.array(Image.open(A+v+'.png').split()[3])>127
    d=t^r; u=t|r
    print(v,'total',d.sum(),u.sum(),f'{100*d.sum()/u.sum():.3f}%')
    ys,xs=np.nonzero(u); cx=(xs.min()+xs.max())/2; print(' bbox x',xs.min(),xs.max(),'cx',cx)
    for name,(x0,x1) in {'imgL':(xs.min(),cx-70),'imgR':(cx+70,xs.max())}.items():
        m=np.zeros_like(d); m[:400,int(x0):int(x1)]=True
        print(' ',name,'diff',(d&m).sum(),'union',(u&m).sum(),f'{100*(d&m).sum()/(u&m).sum():.2f}%','ref-only',((t&~r)&m).sum(),'mdl-only',((r&~t)&m).sum())
