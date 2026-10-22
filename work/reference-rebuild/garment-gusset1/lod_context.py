# Executed in the canonical replay namespace. Preserve exact LOD base geometry,
# and reproduce the existing aligned nearest-source sleeve-shape transfer.
import os
if os.environ.get('GUSSET_LOD')=='1':
 L=R/'work/reference-rebuild/garment-gusset1/lod';L.mkdir(exist_ok=True)
 lod=json.loads((R/'proof/reference-rebuild/underarm-fit2-lod/poses/female_intro.json').read_text())['parts'][1]
 assert lod['bones']==top['bones'],'LOD bone order changed'
 positions=arr(lod,'vertices',3);ln=arr(lod,'normals',3);source=base.copy();ns=normals.copy();mapping=[];errors=[]
 grid={};cell=.006
 for i,v in enumerate(source):grid.setdefault(tuple(np.floor(v/cell).astype(int)),[]).append(i)
 for i,v in enumerate(positions):
  key=np.floor(v/cell).astype(int);best=np.inf;nearest=-1
  for x in range(-2,3):
   for y in range(-2,3):
    for z in range(-2,3):
     ids0=grid.get(tuple(key+[x,y,z]),[])
     if not ids0:continue
     ids0=np.array(ids0);good=(ns[ids0]@ln[i])>=.3;ids0=ids0[good]
     if not len(ids0):continue
     ds=((source[ids0]-v)**2).sum(1);j=ds.argmin()
     if ds[j]<best:best=ds[j];nearest=ids0[j]
  if nearest<0:raise RuntimeError('LOD sleeve mapping miss '+str(i))
  mapping.append(nearest);errors.append(best**.5)
 mapping=np.array(mapping);(L/'mapping-report.json').write_text(json.dumps({'sourceVertices':len(source),'lodVertices':len(positions),'maxMappingDistanceMm':max(errors)*1000,'rendererMatrixError':float(np.max(np.abs(arr(lod,'rendererToRoot',4)-arr(top,'rendererToRoot',4)))),'bindMatrixError':float(np.max(np.abs(np.array(lod['bindposes'])-np.array(top['bindposes']))))},indent=2))
 profile={**profile,'vertexCount':len(positions),'vertices':positions.ravel().tolist(),'normals':ln.ravel().tolist(),'anchors':[{**a,'deltas':arr(a,'deltas',3)[mapping].ravel().tolist(),'normalDeltas':arr(a,'normalDeltas',3)[mapping].ravel().tolist()} for a in profile['anchors']]}
 top=lod;tt=arr(top,'triangles',3).astype(int);base=positions;normals=ln;tr=xf(arr(top,'rendererToRoot',4),base);ti=arr(top,'indices',4).astype(int);tw=arr(top,'weights',4)
