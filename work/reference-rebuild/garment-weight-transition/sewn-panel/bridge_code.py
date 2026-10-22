 # Explicit sewn strip: original retained cut boundary shares indices with
 # one strip edge; the other is inserted into the supporting panel boundary.
 # This avoids independent underlap edges separating when their weights differ.
 from collections import Counter
 def edgecounts(triangles):
  return Counter(tuple(sorted((int(tri[j]),int(tri[(j+1)%3])))) for tri in triangles for j in range(3))
 keptEdges=edgecounts(keep);deletedEdges=edgecounts(tt[remove]);cutEdges=[e for e,c in keptEdges.items() if c==1 and deletedEdges.get(e,0)>0]
 panelEdges=edgecounts(panelTris);sewEdges=[]
 def atCuff(q):
  side='Left' if q[0]<0 else 'Right';a=cuffBind[names.index(side+'UpperArm'),:3,3];b=cuffBind[names.index(side+'LowerArm'),:3,3];t=(q-a)@(b-a)/np.dot(b-a,b-a);return abs(t-(.58 if sex=='Male' else .62))<1e-5
 for edge,c in panelEdges.items():
  if c==1 and not (atCuff(newPoints[edge[0]]) and atCuff(newPoints[edge[1]])):sewEdges.append(edge)
 edgeSplits={};connections={};maxSewDistance=0.
 for oldIndex in sorted(set(v for edge in cutEdges for v in edge)):
  q=rest[oldIndex];best=None
  for edge in sewEdges:
   u,v=edge;a=newPoints[u];b=newPoints[v];axis=b-a;amount=float(np.clip((q-a)@axis/max(axis@axis,1e-15),0,1));point=a+axis*amount;distance=float(np.linalg.norm(q-point))
   if best is None or distance<best[0]:best=(distance,edge,amount,point)
  if best is None:continue
  distance,edge,amount,point=best;maxSewDistance=max(maxSewDistance,distance);u,v=edge
  if amount<1e-6:index=u
  elif amount>1-1e-6:index=v
  else:
   key=(edge,round(amount,7))
   existing=edgeSplits.setdefault(edge,{})
   if key[1] in existing:index=existing[key[1]]
   else:
    index=len(newPoints);normal=newNormals[u]*(1-amount)+newNormals[v]*amount;normal/=max(np.linalg.norm(normal),1e-12);newPoints.append(point);newNormals.append(normal);newWeights.append(newWeights[u]*(1-amount)+newWeights[v]*amount);newUV.append(newUV[u]*(1-amount)+newUV[v]*amount);newClearance.append(.012);source.append({'panelEdge':[int(u),int(v)],'amount':amount});existing[key[1]]=index
  connections[oldIndex]=index
 # Split boundary triangles at every strip endpoint, removing T-junctions.
 finalPanel=[]
 for triangle in panelTris:
  handled=False
  for j in range(3):
   u,v=triangle[j],triangle[(j+1)%3];edge=tuple(sorted((u,v)))
   if edge not in edgeSplits:continue
   inserts=sorted(edgeSplits[edge].items(),reverse=u>v);chain=[u]+[i for amount,i in inserts]+[v];other=triangle[(j+2)%3]
   finalPanel.extend([[chain[k],chain[k+1],other] for k in range(len(chain)-1)]);handled=True;break
  if not handled:finalPanel.append(triangle)
 panelTris=finalPanel;bridgeTris=[]
 for u,v in cutEdges:
  if u not in connections or v not in connections:continue
  a,b=connections[u]+len(base),connections[v]+len(base)
  if a==b:continue
  for triangle in ([u,v,b],[u,b,a]):
   positions=np.array([rest[k] if k<len(base) else newPoints[k-len(base)] for k in triangle]);n=np.cross(positions[1]-positions[0],positions[2]-positions[0]);target=sum(np.array(profileN[k]) if k<len(base) else newNormals[k-len(base)] for k in triangle)
   if np.linalg.norm(n)<1e-10:continue
   if n@target<0:triangle=[triangle[0],triangle[2],triangle[1]]
   bridgeTris.append(triangle)
