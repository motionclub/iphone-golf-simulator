import sys; sys.path.insert(0,'.')
from metric import *
# mid-band shading (DoG sigma 4px/14px ~ 1.1cm/4cm) of the glute region in the back view and the two back 3/4 panels
tags=sys.argv[1:]
def reg(img, box, s1, s2, off=None):
    x0,y0,x1,y1=box; D=dog(img,s1,s2)
    return D[y0:y1,x0:x1] if off is None else D[y0-off[1]:y1-off[1], x0-off[0]:x1-off[0]]
cb=CAM['bald_back']; mpp=cb['metres_per_pixel']
bk=(int(cb['centre_x']-0.16/mpp), int(cb['sole_y']-1.00/mpp), int(cb['centre_x']+0.16/mpp), int(cb['sole_y']-0.72/mpp))
out={}
for s1,s2 in ((3.0,10.0),(5.0,16.0)):
    A=reg(PL,bk,s1,s2); res={}
    for t in tags:
        d=render(t); m=np.asarray(Image.open(d/'back.png').convert('L')).astype('float32'); B=reg(m,bk,s1,s2)
        res[t]=(float(np.corrcoef(A.ravel(),B.ravel())[0,1]), float(B.std()/A.std()))
    print(f'back glute+lumbar  DoG {s1}/{s2}: '+'  '.join(f'{t}: r {r:+.3f} sr {sr:.2f}' for t,(r,sr) in res.items()))
