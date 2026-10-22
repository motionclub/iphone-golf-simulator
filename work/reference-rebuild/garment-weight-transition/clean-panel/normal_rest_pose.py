import pathlib,json,numpy as np
R=pathlib.Path.cwd();s=(R/'work/reference-rebuild/garment-stroke-coverage/author_stroke_envelopes.py').read_text();exec(s[s.index('def arr('):s.index('def author(')])
for mode in ('rest','posed'):
 for sex in ('male','female'):
  b=json.loads((R/f'proof/reference-rebuild/character-cloth14/poses/{sex}_Forehand_1.json').read_text())['parts'][0];rt=np.array(b['rendererToRoot']).reshape(4,4);v=xf(rt,arr(b,'vertices' if mode=='rest' else 'posedVertices',3));t=arr(b,'triangles',3).astype(int);gn,_=geom_normals(v,t);n=arr(b,'normals' if mode=='rest' else 'posedNormals',3)@np.linalg.inv(rt[:3,:3]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);dot=(gn*n).sum(1);r=xf(rt,arr(b,'vertices',3));region=(abs(r[:,0])>.06)&(r[:,1]>1.10)&(r[:,1]<1.43)
  print(mode,sex,'det',np.linalg.det(rt[:3,:3]),'dotRegion',np.quantile(dot[region],[0,.1,.5,.9,1]),'reversed',int((dot[region]<0).sum()),'n',int(region.sum()),flush=True)
