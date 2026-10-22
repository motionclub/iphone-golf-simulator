import json,pathlib
R=pathlib.Path.cwd();W=R/'work/reference-rebuild/garment-weight-transition/mask-cuff2'
def points(part):
 m=part['rendererToRoot'];v=part['vertices'];return [tuple(round(sum(m[r*4+c]*v[i+c] for c in range(3))+m[r*4+3],5) for r in range(3)) for i in range(0,len(v),3)]
def facekey(points,indices):return tuple(sorted(points[i] for i in indices))
report={}
for sex in ['male','female']:
 current=json.loads((R/f'proof/reference-rebuild/character-cloth14/poses/{sex}_Forehand_1.json').read_text())['parts'][0];mask=json.loads((W/f'BodyMask_{sex}.json').read_text());cp=points(current);ct=current['triangles'];keys={facekey(cp,ct[3*i:3*i+3]) for i in mask['alwaysCoveredFaceIndices']};row={}
 for name,path in [('default-source',R/f'proof/full-visual-overhaul/character-pose-data-1/poses/{sex}_intro.json'),('current-matrix-canonical',R/f'proof/reference-rebuild/character-motion-matrices17/poses/{sex}_intro.json')]:
  q=json.loads(path.read_text())['parts'][0];qp=points(q);qt=q['triangles'];matches=[i//3 for i in range(0,len(qt),3) if facekey(qp,qt[i:i+3]) in keys];matchedKeys={facekey(qp,qt[3*i:3*i+3]) for i in matches};row[name]={'vertexCount':len(qp),'triangles':len(qt)//3,'maskPhysicalFaces':len(keys),'matchedPhysicalFaces':len(matchedKeys),'unmatchedPhysicalFaces':len(keys-matchedKeys),'mappedRenderFaces':len(matches),'positionPrecisionMetres':.00001};(W/f'BodyMask_{sex}-{name}.json').write_text(json.dumps({'alwaysCoveredFaceIndices':matches,'correspondence':row[name]},separators=(',',':')))
 report[sex]=row
(W/'source-correspondence.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
