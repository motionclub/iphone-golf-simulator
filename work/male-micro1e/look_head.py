import sys; sys.path.insert(0,'.')
from lib import *
load(); clay_setup()
T=(0,-0.04,1.55)
for name,az,el in [('front',0,0),('q3',35,5),('side',90,0),('q3b',-35,5),('under',20,-30),('top',0,80)]:
    shot(f'r/look_head_{name}.png',T,az,el,0.42,(800,800))
