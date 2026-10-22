import sys; sys.path.insert(0,'.')
from metric import *
def fold(img, view, s1=1.5, s2=6.0, z0=0.745, z1=0.84):
    c=CAM['bald_'+view]; mpp=c['metres_per_pixel']; D=dog(img,s1,s2); out=[]
    for x in np.arange(0.0,0.151,0.015):
        col=int(round(c['centre_x']+(-x if view=='back' else x)/mpp)); rows=range(int(c['sole_y']-z1/mpp),int(c['sole_y']-z0/mpp)); prof=np.array([D[r,col-1:col+2].mean() for r in rows])
        k=int(np.argmin(prof)); out.append((x, c['sole_y']-(list(rows)[k]), prof[k]))
    return [(x, (c['sole_y']-r)*mpp, v) for x,r,v in [(a,c['sole_y']-b,v) for a,b,v in out]]
tags=sys.argv[1:]
print('fold line (z of darkest band-pass minimum in z .745-.84) vs x, back view (z m / depth of min)')
rows={}
for t in ['plate']+tags:
    if t=='plate': img=PL
    else:
        d=render(t); img=np.asarray(Image.open(d/'back.png').convert('L')).astype('float32')
    rows[t]=fold(img,'back')
print('   x   '+'  '.join(f'{t:>14s}' for t in rows))
for i in range(11):
    print(f'{rows["plate"][i][0]:.3f}  '+'  '.join(f'{rows[t][i][1]:.3f} ({rows[t][i][2]:+5.1f})' for t in rows))
