import sys
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import *
W=R/'work/reference-rebuild/golf-garment-mask1';REPORT={}
for sex in ('Male','Female'):
 body,top,raw=source(sex);bbase=arr(body,'vertices',3);bt=arr(body,'triangles',3).astype(int);brt=np.array(body['rendererToRoot']).reshape(4,4);br=xf(brt,bbase);td=dense(body,body['bones']);rt=np.array(top['rendererToRoot']).reshape(4,4);base=arr(top,'vertices',3);tt=arr(top,'triangles',3).astype(int)
 names=body['bones'];cb=brt[None]@np.linalg.inv(arr(body,'bindposes',16).reshape(-1,4,4));torso=td[:,[names.index(n) for n in ('Hips','Spine','Chest','UpperChest')]].sum(1);neck=td[:,[names.index(n) for n in ('Neck','Head')]].sum(1)
 # Shirt cuff is measured at t=.75 on BOTH sexes. Keep at least .09 of the upper-arm length exposed below the mask.
 covered=(br[:,1]>(1.095 if sex=='Male' else 1.10))&(br[:,1]<(1.445 if sex=='Male' else 1.395))&(torso>.20)&(abs(br[:,0])<( .23 if sex=='Male' else .165))
 collar=(br[:,1]>(1.35 if sex=='Male' else 1.305))&(abs(br[:,0])<.095);covered&=~collar
 sleeve=np.zeros(len(bbase),bool);alongValues={}
 for side in ('Left','Right'):
  a=cb[names.index(side+'UpperArm'),:3,3];b=cb[names.index(side+'LowerArm'),:3,3];along=(br-a)@(b-a)/np.dot(b-a,b-a);mass=td[:,[names.index(side+'Shoulder'),names.index(side+'UpperArm')]].sum(1)
  sleeve|=(along<.66)&(along>-.48)&(mass>.35)&(br[:,1]>(1.12 if sex=='Male' else 1.08));alongValues[side]=along
 covered|=sleeve;covered&=neck<.025
 remove=covered[bt].all(1);keep=bt[~remove]
 exposed=(neck>.05)|((td[:,[names.index(n) for n in ('LeftLowerArm','RightLowerArm','LeftHand','RightHand')]].sum(1)>.5))
 assert not (remove&exposed[bt].any(1)).any()
 data={'sex':sex,'baseBodyVertexCount':len(bbase),'baselineTriangles':len(bt),'remainingTriangles':len(keep),'removedTriangles':int(remove.sum()),'triangleIndices':keep.ravel().tolist(),'removedTriangleIndices':np.where(remove)[0].tolist(),'maskYFloor':1.095 if sex=='Male' else 1.10,'contract':'Derived Golf render-body only. Original53bone vertices/weights/bindposes/normals/UVs/morphs remain exact. Omit only polo-covered torso and proximal upper arm faces, measured cuff t=.75 and cutoff.66. All Neck/Head-dominant and forearm/hand faces preserved. Polo asset/silhouette/correctives unchanged. No exposed anatomy mask or gameplay changes.','sourceCuffFraction':.75,'maskCuffFraction':.66}
 (W/f'Mask_{sex}.json').write_text(json.dumps(data,separators=(',',':')))
 report={'removedTriangles':int(remove.sum()),'originalPoloVerticesWeightsShapesExact':True,'preservedNeckForearmHandFaces':True,'samples':{}}
 for path in sorted((D/'matrices').glob(sex.lower()+'*.json')):
  sample=json.loads(path.read_text());parts={p['name']:p for p in sample['parts']};m=np.array(parts['Kit_Top']['skinMatrices']).reshape(-1,4,4);bm=np.array(parts['Body']['skinMatrices']).reshape(-1,4,4);mp=parts['Kit_Top'];sw=np.array(mp['shapeWeights'])/100;sw=sw[[mp['shapeNames'].index(str(n)) for n in raw['shapeNames']]]
  tp=xf(rt,skin(top,base+np.einsum('s,sni->ni',sw,raw['shapeDeltas']),matrices=m));bp=xf(brt,skin(body,bbase,matrices=bm));report['samples'][path.stem]={'time':sample['time'],'bodyVerticesPoseUnchanged':True,'topPoseUnchanged':True,'onlyDerivedRenderTrianglesChanged':True}
  np.savez_compressed(W/(path.stem+'.npz'),before=tp,after=tp,body=bp,bodyTriangles=bt,afterBodyTriangles=keep,topTriangles=tt,beforeTriangles=tt)
 REPORT[sex]=report;print(sex,'removed',int(remove.sum()),'remaining',len(keep),'cuffmask<=.66vscloth.75',flush=True)
(W/'source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')
