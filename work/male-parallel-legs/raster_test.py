import sys; sys.path.insert(0,'.')
from raster import *
import time
t=time.time()
for tag in sys.argv[1:]:
    V=np.load(f'data/V_{tag}.npy'); r=metrics(V)
    print(tag, 'time %.1fs'%(time.time()-t)); 
    for v,x in r.items(): print('   %-11s total %.3f  leg %.3f  foot %.3f'%(v,x['total'],x['leg'],x['foot']))
