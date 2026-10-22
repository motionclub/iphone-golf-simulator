import sys; sys.path.insert(0,'.')
from common import *
tag=sys.argv[1]; V1=np.load(f'data/V_{tag}.npy'); d=(V1-V0)*1000
i=np.argsort(-np.abs(d[:,1]))[:12]
for k in i: print(k, 'x %.3f y %.3f z %.3f'%tuple(V0[k]), 'dy %.1f dx %.1f'%(d[k,1],d[k,0]))
print('count |dy|>30mm:', int((np.abs(d[:,1])>30).sum()), ' >20:', int((np.abs(d[:,1])>20).sum()))
