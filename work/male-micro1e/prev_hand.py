import sys,time; sys.path.insert(0,'.')
import numpy as np
import hand_sdf as H
from wire import write_png
t=time.time()
views={
 'palm':  ((0,-1,0),(0,0,-1)),     # camera on +n side looking along -n ; up = -w (fingers down)
 'back':  ((0,1,0),(0,0,-1)),
 'side_a':((-1,0,0),(0,0,-1)),     # looking along -a' (from front/thumb side)
 'side_b':((1,0,0),(0,0,-1)),
}
tiles=[]
for k,(vd,up) in views.items():
    img=H.raymarch(vd,up,size=(300,420),center=(0,-0.016,0.075),extent=0.25)
    tiles.append(img)
W=sum(t.shape[1] for t in tiles); Hh=tiles[0].shape[0]
out=np.concatenate(tiles,axis=1)
write_png('r/handsdf_preview.png',out); print('done',time.time()-t)
