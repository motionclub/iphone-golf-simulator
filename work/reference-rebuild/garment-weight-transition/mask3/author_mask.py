from pathlib import Path
exec((Path(__file__).parent/'common.py').read_text())
import hashlib
# Complete only mixed torso/arm faces at the existing torso-mask boundary.
# Keep the same collar/waist/head guards on EVERY corner; require at least one
# torso-classified corner. These are straddlers of the weight threshold, not a
# farther axial sleeve mask. No high-arm-influence-only triangle is added.
torso=(rest[:,1]>1.11)&(rest[:,1]<1.354)&(arm<.45)&(head<.035)
guard=(rest[:,1]>1.11)&(rest[:,1]<1.354)&(head<.035)
added=keep&guard[bt].all(1)&torso[bt].any(1);remove=~keep|added;newfaces=np.where(added)[0];removed=np.where(remove)[0]
O=W/'runtime-profiles';O.mkdir(exist_ok=True)
profileOut={'garmentVertexCount':len(top['vertices'])//3,'expectedRemovedFaceCount':len(removed),'removedTriangleRootPositions':rest[bt[removed]].ravel().tolist()};dest=O/'Tennis_Female.json';dest.write_text(json.dumps(profileOut,separators=(',',':')))
mask={'sex':'Female','source':'character-motion-matrices17 canonical female_intro','bodyVertexCount':len(rest),'bodyTriangleCount':len(bt),'alwaysCoveredFaceIndices':removed.tolist(),'addedMixedTorsoArmFaces':newfaces.tolist(),'contract':'mask2 plus mixed torso/arm triangles: all corners pass original torso height/head guards, at least one corner passes original torso armMass<0.45. Fixes triangle-wide all-corner rejection at torso arm-weight transition. Added49faces rest bounds x[-0.135627,0.137933],y[1.156,1.211128],z[-0.039312,0.043087]m. No pure-arm face, neck, cuff endpoint or geometry/weight/UV/rig mutation.'};(W/'BodyMask_female-current-matrix-canonical.json').write_text(json.dumps(mask,separators=(',',':')))
(W/'added-face-diagnosis.json').write_text(json.dumps([facefacts(f) for f in newfaces],indent=2))
# Remap by canonical root-space physical face, using the same precision as mask2.
def keys(v,t):return [tuple(sorted(tuple(x) for x in np.round(v[f],5))) for f in t]
k=set(keys(rest,bt[removed]));q=json.loads((R/'proof/reference-rebuild/character-cloth14/poses/female_Forehand_1.json').read_text())['parts'][0];v=xf(arr(q,'rendererToRoot',4),arr(q,'vertices',3));tri=arr(q,'triangles',3).astype(int);target=keys(v,tri);mapped=[i for i,key in enumerate(target) if key in k];assert len(mapped)==len(removed);maskOld={**mask,'source':'character-cloth14 female_Forehand_1','alwaysCoveredFaceIndices':mapped};(W/'BodyMask_female.json').write_text(json.dumps(maskOld,separators=(',',':')))
report={'removed':len(removed),'added':len(newfaces),'preservedMask2Faces':int((~keep).sum()),'addedRestBounds':{'min':rest[bt[newfaces]].reshape(-1,3).min(0).tolist(),'max':rest[bt[newfaces]].reshape(-1,3).max(0).tolist()},'profileSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'status':'Source candidate; actual motion render gate pending'};(O/'manifest.json').write_text(json.dumps(report,indent=2));print(report)
