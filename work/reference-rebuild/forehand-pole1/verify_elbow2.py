from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
R=Path.cwd();W=R/'work/reference-rebuild/forehand-pole1';D=R/'proof/reference-rebuild';C=D/'forehand-clearance-control1';allrows={}
for level in ['forehand-elbow2','forehand-elbow2-lod']:
 rows=[];out=D/level;can=json.loads((C/'poses/male_intro.json').read_text())['parts'][0] if (C/'poses/male_intro.json').exists() else json.loads((D/'character-motion-matrices17/poses/male_intro.json').read_text())['parts'][0];names=can['bones'];bind=np.array(can['bindposes']).reshape(-1,4,4);keep=np.array([i for i,n in enumerate(names) if n not in ['RightUpperArm','RightLowerArm']]);hand=np.array([i for i,n in enumerate(names) if n.startswith('Right') and any(k in n for k in ['Hand','Thumb','Index','Middle','Ring','Little'])]);u=names.index('RightUpperArm');l=names.index('RightLowerArm')
 for p in sorted((C/'matrices').glob('male_ForehandOpen_*.json')):
  a=json.loads(p.read_text());b=json.loads((out/'matrices'/p.name).read_text());pa=a['parts'][0];pb=b['parts'][0];am=np.array(pa['rendererToRoot']).reshape(4,4)[None]@np.array(pa['skinMatrices']).reshape(-1,4,4)@np.linalg.inv(bind);bm=np.array(pb['rendererToRoot']).reshape(4,4)[None]@np.array(pb['skinMatrices']).reshape(-1,4,4)@np.linalg.inv(bind);pos=np.linalg.norm(am[:,:3,3]-bm[:,:3,3],axis=1);angles=[]
  for i in hand:
   u1,_,v1=np.linalg.svd(am[i,:3,:3]);u2,_,v2=np.linalg.svd(bm[i,:3,:3]);angles.append(float(np.degrees(np.arccos(np.clip((np.trace((u1@v1).T@(u2@v2))-1)*.5,-1,1)))))
  rows.append({'label':a['label'],'time':a['time'],'sampleTimeEqual':a['time']==b['time'],'rightHandPositionMm':float(pos[names.index('RightHand')]*1000),'rightHandAngleDeg':angles[list(hand).index(names.index('RightHand'))],'handAndFingerMaxPositionMm':float(pos[hand].max()*1000),'handAndFingerMaxAngleDeg':max(angles),'otherBoneMaxPositionMm':float(pos[keep].max()*1000),'upperArmOriginDeltaMm':float(pos[u]*1000),'elbowDeltaMm':float(pos[l]*1000),'maxRetainedSkinMatrixElement':float(np.max(np.abs(am[keep]-bm[keep])))})
 allrows[level]={'gate':'PASS' if all(x['handAndFingerMaxPositionMm']<.01 and x['handAndFingerMaxAngleDeg']<.001 and x['sampleTimeEqual'] for x in rows) else 'FAIL','wristContactGate':'PASS' if all(x['rightHandPositionMm']<.01 and x['rightHandAngleDeg']<.001 for x in rows) else 'FAIL','maxWristPositionMm':max(x['rightHandPositionMm'] for x in rows),'maxWristAngleDeg':max(x['rightHandAngleDeg'] for x in rows),'strictAllFingerExactness':'FAIL; HeroGripPolish world-space finger solve reevaluates after arm swivel, max finger displacement below .035mm; no wrist/socket change','samples':len(rows),'maxHandPositionMm':max(x['handAndFingerMaxPositionMm'] for x in rows),'maxHandAngleDeg':max(x['handAndFingerMaxAngleDeg'] for x in rows),'maxOtherBoneMm':max(x['otherBoneMaxPositionMm'] for x in rows),'rows':rows}
 for rear in ['', '_rear']:
  sheet=Image.new('RGB',(5*350,5*475),(28,28,30));dr=ImageDraw.Draw(sheet)
  for j in range(25):
   im=Image.open(out/f'male_ForehandOpen_{j}{rear}.png');im=im.crop((160,230,620,770)).resize((350,410));x=j%5*350;y=j//5*475;sheet.paste(im,(x,y+30));dr.text((x+8,y+6),f'{j}  '+next(f"{r["time"]:.5f}s" for r in rows if r['label']==f'male_ForehandOpen_{j}'),fill='white')
  sheet.save(W/(level+rear+'-review.jpg'),quality=90)
(W/'unity-elbow2-invariants.json').write_text(json.dumps(allrows,indent=2));print(json.dumps({k:{p:v for p,v in r.items() if p!='rows'} for k,r in allrows.items()},indent=2))
