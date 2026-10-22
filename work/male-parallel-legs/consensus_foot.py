import sys; sys.path.insert(0,'.')
from edges import *
from leglib import *
V=np.load(sys.argv[1])
print(' z    inner: bf    sf    bb    sb | mesh      outer: bf    sf    bb    sb | mesh')
for z in np.arange(0.01,0.16,0.01):
    row=[]
    ins=[];outs=[]
    for v in ('bald_front','sheet_front','bald_back','sheet_back'):
        sp=[s for s in spans(v,z) if s[0]>=0.0 and s[1]>0.05]
        if sp: ins.append(sp[0][0]); outs.append(sp[0][1])
        else: ins.append(np.nan); outs.append(np.nan)
    s=LEFT&(np.abs(V[:,2]-z)<0.006); s2=RIGHT&(np.abs(V[:,2]-z)<0.006)
    mi=0.5*(V[s,0].min()+(-V[s2,0].max())); mo=0.5*(V[s,0].max()+(-V[s2,0].min()))
    print('%.2f   '%z,' '.join('%.3f'%x for x in ins),'| %.3f   '%mi,' '.join('%.3f'%x for x in outs),'| %.3f'%mo)
