import numpy as np, sys
sys.path.insert(0,'.')
import hand_assemble as HA, hand_topo as T
d=np.load('baseline/mesh.npz'); co=d['co']; F=np.load('faces.npy')
verts,faces,info=HA.assemble(co,F,smooth_iters=10)
print(info)
print('verts',len(verts),'faces',len(faces),'tris-equivalent',sum(1 if len(f)==3 else 2 for f in faces))
print('manifold:',T.check_manifold(faces))
np.save('r/asm_verts.npy',verts)
import pickle; pickle.dump(faces,open('r/asm_faces.pkl','wb'))
