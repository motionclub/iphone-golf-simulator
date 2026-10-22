import sys; sys.path.insert(0,'.')
from edges import *
from leglib import *
VA=np.load('data/V_A40.npy')
print('PROFILE y-extents: plate left / right (world y) vs mesh union of both legs; rows z>=0.07 may include far foot at the front for z<0.15')
for z in np.arange(0.07,0.76,0.03):
    out=[]
    for v in ('left','right'):
        sp=spans(v,z)
        if sp: out.append('%s y[%+.3f,%+.3f]'%(v[:1],sp[0][0],sp[-1][1]) if v=='left' else '%s y[%+.3f,%+.3f]'%(v[:1],sp[0][0],sp[-1][1]))
        else: out.append('--')
    s=ZONE&(np.abs(VA[:,2]-z)<0.006)
    print('z=%.2f'%z,' '.join(out),'| mesh y[%+.3f,%+.3f]'%(VA[s,1].min(),VA[s,1].max()))
