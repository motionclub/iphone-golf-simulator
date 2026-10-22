import sys; sys.path.insert(0,'.')
from relcorr import *
from PIL import Image
import numpy as np
c = CAM['bald_front']; mpp = c['metres_per_pixel']; xs = [-0.13,-0.11,-0.09,-0.07,0.07,0.09,0.11,0.13]; zs = np.arange(1.10,1.34,0.005)
def prof(img):
    a = np.asarray(img.convert('L')).astype('float32'); out=[]
    for z in zs:
        row=int(round(c['sole_y']-z/mpp)); out.append(np.mean([a[row-1:row+2,int(round(c['centre_x']+x/mpp))-1:int(round(c['centre_x']+x/mpp))+2].mean() for x in xs]))
    return np.array(out)
for t in sys.argv[1:]:
    for kind, path in (('skin', f'r/{t}/front.png'), ('clay', f'r/{t}c/front.png')):
        try: v = prof(Image.open(path))
        except Exception as e: continue
        up = v[(zs>1.21)&(zs<1.30)].max(); lo = v[(zs>1.12)&(zs<1.22)].min()
        print(f'{t:8s} {kind}: crest-crease drop {up-lo:5.1f} lum  mean {v.mean():6.1f}  normalized {(up-lo)/v.mean():.3f}  crease z {zs[(zs>1.12)&(zs<1.22)][np.argmin(v[(zs>1.12)&(zs<1.22)])]:.3f}')
