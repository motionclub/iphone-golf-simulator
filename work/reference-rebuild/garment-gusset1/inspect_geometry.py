from pathlib import Path
S=Path.cwd()/'work/reference-rebuild/garment-weight-transition/mask3/author_local_cloth_frontcull.py'
__file__=str(S);exec(S.read_text().split('regions=np.array')[0])
Z=R/'work/reference-rebuild/garment-gusset1'
bp,tp=replay('female_Forehand_1');mp=next(p for p in json.loads((D/'matrices/female_Forehand_1.json').read_text())['parts'] if p['name']==top['name']);sm=arr(mp,'skinMatrices',16).reshape(-1,4,4);rt=arr(mp,'rendererToRoot',4)
dense=np.zeros((len(tr),len(top['bones'])))
for j in range(4):dense[np.arange(len(tr)),ti[:,j]]+=tw[:,j]
rows=[]
for f in [11424,9123,5086]:
 ids=tt[f];v=base[ids].mean(0);w=dense[ids].mean(0);linear=tp[ids].mean(0);q=xf(rt,(np.einsum('kij,j->ki',sm[:,:3,:3],v)+sm[:,:3,3])*w[:,None]).sum(0) if False else xf(rt,((np.einsum('kij,j->ki',sm[:,:3,:3],v)+sm[:,:3,3])*w[:,None]).sum(0)[None])[0]
 rows.append({'face':f,'ids':ids.tolist(),'rest':tr[ids].tolist(),'posed':tp[ids].tolist(),'maxRestEdgeMm':float(max(np.linalg.norm(tr[ids[j]]-tr[ids[(j+1)%3]]) for j in range(3))*1000),'maxPosedEdgeMm':float(max(np.linalg.norm(tp[ids[j]]-tp[ids[(j+1)%3]]) for j in range(3))*1000),'subdivisionCentroidDifferenceMm':((q-linear)*1000).tolist(),'towardFrontCameraMm':float((q-linear)@(-fw)*1000)})
(Z/'initial-geometry.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
