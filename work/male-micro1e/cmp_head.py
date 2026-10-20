"""Render head views matching plate panels. usage: blender -b --python cmp_head.py -- coords.npy outprefix"""
import sys; sys.path.insert(0,'.')
from lib import *
argv=sys.argv[sys.argv.index('--')+1:]
coords=argv[0] if argv and argv[0]!='base' else None
pre=argv[1] if len(argv)>1 else 'r/cmp'
load(coords); clay_setup()
k=0.0013043874429196725
# panel geometry (1x px): front panel x22..432, left panel x440..834, y 66..352
zc=1.7046599388122559-((66+352)/2-76)*k
ycl=0.065+((440+834)/2-712)*k
W1=410; H1=286; Wl=394
# front: camera at -Y (az=0): image-right=+X; plate front panel has face center x=227.5 -> x=0
shot(f'{pre}_front.png',(0,-0.04,zc),0,0,W1*k,(W1*3,H1*3))
# left profile: az=90 (camera +X, image right=+Y, face to left)
shot(f'{pre}_left.png',(0,ycl,zc),90,0,Wl*k,(Wl*3,H1*3))
# 3/4 views (approximate): plate 3/4 front left/right panels
shot(f'{pre}_q3R.png',(0,-0.03,zc),-38,0,Wl*k,(Wl*3,H1*3))
shot(f'{pre}_q3L.png',(0,-0.03,zc),38,0,W1*k,(W1*3,H1*3))
