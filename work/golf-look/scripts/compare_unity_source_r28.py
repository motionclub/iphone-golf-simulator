import sys,ctypes,json,itertools,numpy as np
from pathlib import Path
w=Path(__file__).resolve().parents[1];sys.path.insert(0,str(w/'python-deps'));import cv2
class cKDTree:
 def __init__(self,data):self.tree=cv2.flann_Index(np.ascontiguousarray(data.astype(np.float32)),dict(algorithm=1,trees=4))
 def query(self,data):
  idx,d=self.tree.knnSearch(np.ascontiguousarray(data.astype(np.float32)),1,params=dict(checks=256));return np.sqrt(d[:,0]),idx[:,0]

man=json.loads((w/'locker/assets/GolfHero_Male.json').read_text());c=(w/'locker/assets/GolfHero_Male.lzfse').read_bytes();lib=ctypes.CDLL('/usr/lib/libcompression.dylib');fn=lib.compression_decode_buffer;fn.restype=ctypes.c_size_t;fn.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_int];out=ctypes.create_string_buffer(40_000_000);n=fn(out,len(out),c,len(c),None,0x801);assert n>0;blob=out.raw[:n]
def v(p,key='positionOffset'):return np.frombuffer(blob,dtype='<f4',count=p['vertexCount']*3,offset=p[key]).reshape(-1,3).copy()
bp=next(p for p in man['parts'] if p['kind']=='body');B=v(bp);B0=v(bp,'bindPositionOffset');p=next(p for p in man['parts'] if p['name']=='Kit_Bottom');P=v(p)
s=np.load(w/'data/ready_geometry_source_r28.npz');tree=cKDTree(s['B0']);best=None
for perm in itertools.permutations(range(3)):
 for sign in itertools.product([-1,1],repeat=3):
  q=B0[:,perm]*sign;d,idx=tree.query(q[::50]);err=d.mean()
  if best is None or err<best[0]:best=(err,perm,sign)
_,perm,sign=best;_,idx=tree.query(B0[:,perm]*sign);X=s['B'][idx];Y=B;xc=X.mean(0);yc=Y.mean(0);u,sv,vt=np.linalg.svd((X-xc).T@(Y-yc));r=u@vt;t=yc-xc@r;E=np.linalg.norm(X@r+t-Y,axis=1);print('bodyRest',best,'posemm',np.percentile(E*1000,[0,50,95,99,100]),'det',np.linalg.det(r),flush=True)
Q=s['P']@r+t;d,_=cKDTree(Q).query(P);print('pantsNativeToSourceNearestmm',np.percentile(d*1000,[0,50,95,99,100]),flush=True)
np.savez_compressed(w/'data/unity_source_ready_compare_r28.npz',B=B,B0=B0,P=P,Q=Q,rotation=r,translation=t,bodyError=E,nativePartDistances=d,PT=np.concatenate([np.frombuffer(blob,dtype='<i4',count=q['indexCount'],offset=q['indexOffset']).reshape(-1,3) for q in p['submeshes']]),BT=np.concatenate([np.frombuffer(blob,dtype='<i4',count=q['indexCount'],offset=q['indexOffset']).reshape(-1,3) for q in bp['submeshes']]))
