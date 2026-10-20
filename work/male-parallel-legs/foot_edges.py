import sys; sys.path.insert(0,'.')
from edges import *
from leglib import *
VA=np.load('data/V_A40.npy')
print('FOOT x-extents of the +x foot (outer=max, inner=min) per view; mesh from vertices')
for z in np.arange(0.005,0.15,0.01):
    row=[]
    for v in ('bald_front','sheet_front','bald_back','sheet_back'):
        sp=[s for s in spans(v,z) if s[1]>0.05]
        sp=[s for s in sp if s[0]>0.0] if v in('bald_front','sheet_front','bald_back','sheet_back') else sp
        row.append('[%.3f,%.3f]'%(sp[-1][0],sp[-1][1]) if sp else '   --   ')
    s=LEFT&(np.abs(VA[:,2]-z)<0.006)
    print('z=%.3f'%z,' '.join(row),'| mesh [%.3f,%.3f]'%(VA[s,0].min(),VA[s,0].max()) if s.sum() else '')
print('PROFILE y-extents (front=toe tip -y, back=heel) from left/right plates (u: left u=y, right u=-y) vs mesh (both feet same y)')
for z in np.arange(0.005,0.07,0.01):
    out=[]
    for v in ('left','right'):
        sp=spans(v,z); 
        if sp:
            a=sp[0][0]; b=sp[-1][1]
            if v=='left': out.append('left y[%.3f,%.3f]'%(a,b))
            else: out.append('right y[%.3f,%.3f]'%(-b,-a))
    s=ZONE&(np.abs(VA[:,2]-z)<0.006)
    print('z=%.3f'%z,' '.join(out),'| mesh y[%.3f,%.3f]'%(VA[s,1].min(),VA[s,1].max()))
