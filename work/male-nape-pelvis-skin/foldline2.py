import sys; sys.path.insert(0,'.')
from metric import *
def minima(img, view, s1=1.5, s2=6.0, z0=0.70, z1=0.95, xs=np.arange(0.0,0.151,0.015)):
    c=CAM['bald_'+view]; mpp=c['metres_per_pixel']; D=dog(img,s1,s2); out={}
    for x in xs:
        col=int(round(c['centre_x']+(-x if view=='back' else x)/mpp)); r0=int(c['sole_y']-z1/mpp); r1=int(c['sole_y']-z0/mpp); prof=np.array([D[r,col-1:col+2].mean() for r in range(r0,r1)])
        # list local minima deeper than -2.5
        ms=[]
        for k in range(3,len(prof)-3):
            if prof[k]==prof[k-3:k+4].min() and prof[k]<-2.5: ms.append((round((c['sole_y']-(r0+k))*mpp,3), round(float(prof[k]),1)))
        out[round(float(x),3)]=ms
    return out
view=sys.argv[1]; tags=sys.argv[2:]
res={}
for t in ['plate']+tags:
    img=PL if t=='plate' else np.asarray(Image.open(render(t)/(view+'.png')).convert('L')).astype('float32'); res[t]=minima(img,view)
for x in res['plate']:
    print(f'x={x:.3f}')
    for t in res: print(f'   {t:6s}', res[t][x])
