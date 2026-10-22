import sys; sys.path.insert(0,'.')
from metric import *
# low/mid-frequency structure: Pearson r of raw brightness (after removing each image's regional mean/std) in the glute region + vertical profile at the cheek column
tags=sys.argv[1:]
cb=CAM['bald_back']; mpp=cb['metres_per_pixel']
bk=(int(cb['centre_x']-0.14/mpp), int(cb['sole_y']-1.10/mpp), int(cb['centre_x']+0.14/mpp), int(cb['sole_y']-0.72/mpp))
x0,y0,x1,y1=bk; A=PL[y0:y1,x0:x1]
def prof(img, x, zs):
    out=[]
    for z in zs:
        row=int(round(cb['sole_y']-z/mpp)); col=int(round(cb['centre_x']-x/mpp)); out.append(img[row-2:row+3,col-2:col+3].mean())
    return np.array(out)
zs=np.arange(0.74,1.12,0.02)
pl=prof(PL,0.06,zs); print('z      '+' '.join(f'{z:5.2f}' for z in zs)); print('plate  '+' '.join(f'{v:5.0f}' for v in pl))
for t in tags:
    m=np.asarray(Image.open(render(t)/'back.png').convert('L')).astype('float32'); B=m[y0:y1,x0:x1]
    r=np.corrcoef(A.ravel(),B.ravel())[0,1]; p=prof(m,0.06,zs)
    # normalised profile correlation
    rp=np.corrcoef(pl,p)[0,1]
    print(f'{t:6s} '+' '.join(f'{v:5.0f}' for v in p)+f'   raw r {r:+.3f}  column-profile r {rp:+.3f}')
