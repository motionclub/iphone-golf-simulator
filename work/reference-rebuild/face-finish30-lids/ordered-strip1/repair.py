"""Replace only each folded eyelid annulus by ordered concentric support rings.
Call repair(body, sex) on frozen broad/ears/forehead source; it preserves outside polygons,
original point prefix, all shape names, weights, UV/material ownership, and rig object.
"""
import bpy,numpy as np,heapq,collections,math
from mathutils import Vector

def cycles(edges):
 adj=collections.defaultdict(list)
 for a,b in edges:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
 assert all(len(v)==2 for v in adj.values()),'Non-manifold annulus boundary'
 remain=set(adj);out=[]
 while remain:
  start=min(remain);loop=[start];prev=-1;i=start
  while True:
   nxt=next(j for j in adj[i]if j!=prev)
   if nxt==start:break
   loop.append(nxt);prev,i=i,nxt
  remain.difference_update(loop);out.append(np.array(loop,int))
 return out

def repair(body,sex):
 groupNames=[g.name for g in body.vertex_groups];me=body.data;p=np.array([v.co[:]for v in me.vertices]);sh={k.name:np.array([v.co[:]for v in k.data])for k in me.shape_keys.key_blocks};T=np.array([poly.vertices[:]for poly in me.polygons],int);assert T.shape[1]==3
 oldN=[tuple(x.vector)for x in me.corner_normals];uvs={u.name:np.array([v.uv[:]for v in u.data])for u in me.uv_layers};colors={a.name:(a.domain,a.data_type,np.array([v.color[:]for v in a.data]))for a in me.color_attributes};mats=list(me.materials);matidx=np.array([q.material_index for q in me.polygons]);oldweights=[[(g.group,g.weight)for g in v.groups]for v in me.vertices];oldLoops=np.array([poly.loop_indices[:]for poly in me.polygons],int)
 E,ec=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0,return_counts=True);allb=E[ec==1];eyeb=allb[np.all((p[allb,1]<-.05)&(p[allb,2]>1.50)&(p[allb,2]<1.64),axis=1)];eyeLoops=cycles(eyeb);assert len(eyeLoops)==2
 adj=[[]for _ in p]
 for a,b in E:
  w=float(np.linalg.norm(p[a]-p[b]));adj[a].append((int(b),w));adj[b].append((int(a),w))
 out={k:list(v)for k,v in sh.items()};weights=list(oldweights);removed=set();newT=[];newUV=[];newColor=[];affected=set();report=[];baseuv=uvs[next(iter(uvs))];rimLash={}
 # A source vertex may have split corners. Pick its first UV/colour for the new rim.
 first=np.full(len(p),-1,int)
 for li,l in enumerate(me.loops):
  if first[l.vertex_index]<0:first[l.vertex_index]=li
 vertexN=np.zeros_like(p);nc=np.zeros(len(p))
 for li,l in enumerate(me.loops):vertexN[l.vertex_index]+=oldN[li];nc[l.vertex_index]+=1
 vertexN/=np.maximum(nc[:,None],1);vertexN/=np.maximum(np.linalg.norm(vertexN,axis=1)[:,None],1e-9)
 for inner in eyeLoops:
  sign=1 if p[inner,0].mean()>0 else -1;distance=np.full(len(p),np.inf);distance[inner]=0;queue=[(0,int(i))for i in inner];heapq.heapify(queue);radius=.050 if sex=='Male'else .046
  while queue:
   length,i=heapq.heappop(queue)
   if length!=distance[i]or length>radius:continue
   for j,w in adj[i]:
    if p[j,0]*sign<.004:continue
    value=length+w
    if value<distance[j]:distance[j]=value;heapq.heappush(queue,(value,j))
  take=np.all(distance[T]<radius,axis=1);patch=T[take];ed,cnt=np.unique(np.sort(np.concatenate([patch[:,[0,1]],patch[:,[1,2]],patch[:,[2,0]]]),axis=1),axis=0,return_counts=True);loops=cycles(ed[cnt==1]);assert len(loops)==2,(sex,sign,[len(l)for l in loops]);outer=next(l for l in loops if len(set(l)&set(inner))==0)
  removed.update(np.flatnonzero(take));affected.update(outer);affected.update(inner)
  bp=p[inner];xmin,xmax=bp[:,0].min(),bp[:,0].max();cx=(xmin+xmax)/2;cz=(bp[:,2].max()+bp[:,2].min())/2;width=xmax-xmin
  # Order outer loop CCW in the front tangent plane, start at its rightmost point.
  area=np.sum(p[outer,0]*np.roll(p[outer,2],-1)-np.roll(p[outer,0],-1)*p[outer,2]);outer=outer if area>0 else outer[::-1];outer=np.roll(outer,-np.argmax(p[outer,0]));xy=p[outer][:,[0,2]];length=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1);oparam=np.r_[0,np.cumsum(length)[:-1]]/length.sum();ext=np.r_[oparam,1]
  phase=oparam*2*np.pi;harmonic=np.c_[np.ones(len(outer)),*[f(k*phase)for k in range(1,5)for f in [np.cos,np.sin]]];outerY={}
  for name in sh:
   fit=harmonic@np.linalg.lstsq(harmonic,sh[name][outer,1],rcond=None)[0];outerY[name]=fit
  # Parameterize the original aperture along its ordered boundary, preserving vertices.
  area=np.sum(p[inner,0]*np.roll(p[inner,2],-1)-np.roll(p[inner,0],-1)*p[inner,2]);inner=inner if area>0 else inner[::-1];inner=np.roll(inner,-np.argmax(p[inner,0]));ang=np.unwrap(np.arctan2((p[inner,2]-cz)/max(.005,np.ptp(bp[:,2])/2),(p[inner,0]-cx)/(width/2)));ang-=ang[0];
  # arc order follows the actual contour, and is strictly increasing after rebuilding.
  lengths=np.linalg.norm(np.roll(p[inner][:,[0,2]],-1,axis=0)-p[inner][:,[0,2]],axis=1);iparam=np.r_[0,np.cumsum(lengths)[:-1]]/lengths.sum()
  corners=bp[[np.argmin(bp[:,0]),np.argmax(bp[:,0])]];u=(bp[:,0]-xmin)/width;upper=bp[:,2]>=corners[0,2]*(1-u)+corners[1,2]*u
  original=next(l for l in eyeLoops if sign*p[l,0].mean()>0);origbp=p[original];ou=(origbp[:,0]-xmin)/width;isup=origbp[:,2]>=corners[0,2]*(1-ou)+corners[1,2]*ou
  depth={k:(np.polyfit(ou[isup],sh[k][original[isup],1],4),np.polyfit(ou[~isup],sh[k][original[~isup],1],4))for k in sh}
  fullz=np.polyfit(ou,sh['Hero_Blink'][original,2],3);fully=np.polyfit(ou,sh['Hero_Blink'][original,1],4)
  # The upper arch is deliberately curved; original flattened socket cuts are not retained.
  upperH=width*(.22 if sex=='Female'else .24);lowerH=width*(.22 if sex=='Female'else .13)
  def rim(theta,name):
   uu=(1+math.cos(theta))/2;up=math.sin(theta)>=-1e-8;arch=max(0,math.sin(math.pi*uu))**.85
   z=corners[0,2]*(1-uu)+corners[1,2]*uu+(upperH if up else -lowerH)*arch
   y=float(np.polyval(depth['Basis'][0 if up and sex=='Female' else 1],uu))-(.0010 if sex=='Female'else .0007)*arch
   if name!='Basis':
    closedZ=float(np.polyval(fullz,0))*(1-uu)+float(np.polyval(fullz,1))*uu-(.004 if sex=='Female'else .0025)*math.sin(math.pi*uu)**.95;closedY=float(np.polyval(fully,uu))+(-.00015 if up else .00015)*arch
    if name=='Hero_Blink':z=closedZ;y=closedY
    elif name=='Hero_Blink_Half':z=(z+closedZ)*.5;y=min((y+closedY)*.5,float(np.polyval(depth[name][0 if up else 1],uu)))
   return np.array([xmin+uu*width,y,z])
  # Use angle from the original inner point to keep corner identities; new rings use 96 samples.
  iu=np.clip((p[inner,0]-xmin)/width,0,1);iup=p[inner,2]>=corners[0,2]*(1-iu)+corners[1,2]*iu;theta0=np.arccos(2*iu-1);innerAngles=np.where(iup,theta0,2*np.pi-theta0);innerAngles=np.mod(innerAngles,2*np.pi);order=np.argsort(innerAngles);inner=inner[order];innerAngles=innerAngles[order];iparam=innerAngles/(2*np.pi)
  for i,theta in zip(inner,innerAngles):
   rimLash[int(i)]=(.75 if sex=='Female'else .50)*max(0,math.sin(theta))**.45
   for name in sh:out[name][int(i)]=rim(float(theta),name)
  count=96;phases=np.arange(count)/count;thetas=phases*2*np.pi;ringids=[inner.tolist()];ringparams=[iparam];rowParams=[0,.02,.04,.07,.11,.17,.25,.35,.46,.58,.69,.78,.86,.92,.96,.98,1];newStart=len(out['Basis']);interpParents=[]
  for frac in rowParams[1:-1]:
   ids=[]
   for v,theta in zip(phases,thetas):
    idx=len(out['Basis']);ids.append(idx);j=min(len(outer)-1,np.searchsorted(ext,v,side='right')-1);f=(v-ext[j])/(ext[j+1]-ext[j]);a,b=int(outer[j]),int(outer[(j+1)%len(outer)])
    for name in sh:
     qout=sh[name][a]*(1-f)+sh[name][b]*f;qin=rim(float(theta),name);q=qin*(1-frac)+qout*frac;n=vertexN[a]*(1-f)+vertexN[b]*f;radial=qout-qin;m1=-(n[0]*radial[0]+n[2]*radial[2])/(-max(.2,-n[1]));m1=np.clip(m1,-.06,.06);t=frac;q[1]=(2*t**3-3*t*t+1)*qin[1]+(-2*t**3+3*t*t)*qout[1]+(t**3-t*t)*m1
     # A narrow rounded support roll gives the lid actual thickness.
     q[1]-=(.0007 if sex=='Female'else .00055)*math.exp(-((frac-.06)/.08)**2)*abs(math.sin(theta))**.4
     out[name].append(q)
    near=int(inner[np.argmin(np.abs(np.angle(np.exp(1j*(innerAngles-theta)))))]);wd=collections.defaultdict(float)
    for k,w in oldweights[near]:wd[k]+=w*(1-frac)
    for k,w in oldweights[a]:wd[k]+=w*frac*(1-f)
    for k,w in oldweights[b]:wd[k]+=w*frac*f
    weights.append(list(wd.items()));interpParents.append((near,a,b,frac,f,theta))
   ringids.append(ids);ringparams.append(phases)
  ringids.append(outer.tolist());ringparams.append(oparam)
  def bridge(A,ta,B,tb):
   ia=ib=0
   while ia<len(A)or ib<len(B):
    na=ta[(ia+1)%len(A)]+(1 if ia+1>=len(A)else 0);nb=tb[(ib+1)%len(B)]+(1 if ib+1>=len(B)else 0)
    if ia>=len(A):na=float('inf')
    if ib>=len(B):nb=float('inf')
    if na<=nb:tri=[A[ia%len(A)],A[(ia+1)%len(A)],B[ib%len(B)]];ia+=1
    else:tri=[A[ia%len(A)],B[(ib+1)%len(B)],B[ib%len(B)]];ib+=1
    q=np.array([out['Basis'][i]for i in tri]);n=np.cross(q[1]-q[0],q[2]-q[0]);
    if n[1]>0:tri=[tri[0],tri[2],tri[1]]
    newT.append(tri)
  from mathutils.geometry import delaunay_2d_cdt
  allids=list(dict.fromkeys(i for rr in ringids for i in rr));local={v:i for i,v in enumerate(allids)};constraints=[]
  for rr in [ringids[0],ringids[-1]]:
   constraints.extend((local[a],local[b])for a,b in zip(rr,rr[1:]+rr[:1]))
  coords=[Vector((out['Basis'][i][0],out['Basis'][i][2]))for i in allids]
  cverts,cedges,cfaces,orig,_,_=delaunay_2d_cdt(coords,constraints,[],0,1e-10,True)
  assert all(len(o)>0 for o in orig),('Crossing eye boundary constraints',sex,sign)
  mapped=[allids[o[0]]for o in orig]
  outer2=np.array([out['Basis'][i][[0,2]]for i in ringids[-1]]);inner2=np.array([out['Basis'][i][[0,2]]for i in ringids[0]])
  def inside(q,poly):
   result=False
   for a,b in zip(poly,np.roll(poly,-1,axis=0)):
    if (a[1]>q[1])!=(b[1]>q[1])and q[0]<(b[0]-a[0])*(q[1]-a[1])/(b[1]-a[1])+a[0]:result=not result
   return result
  for face in cfaces:
   assert len(face)==3
   midpoint=np.mean([cverts[i]for i in face],axis=0)
   if inside(midpoint,outer2)and not inside(midpoint,inner2):newT.append([mapped[i]for i in face])
  # Per-new-vertex UV and pigment, matching the actual Unity mask decoder.
  for near,a,b,frac,f,theta in interpParents:
   uv0=baseuv[first[near]]*(1-frac)+(baseuv[first[a]]*(1-f)+baseuv[first[b]]*f)*frac;mask=np.clip((uv0*64-.5)/63,0,1)
   lash=(.75 if sex=='Female'else .50)*math.exp(-.5*(frac/.065)**2)*max(0,math.sin(theta))**.45;mask[1]=max(mask[1],lash);newUV.append((.5+63*mask)/64)
   newColor.append((near,a,b,frac,f,lash))
  report.append({'side':sign,'removedTriangles':int(take.sum()),'inner':len(inner),'outer':len(outer),'addedVertices':len(out['Basis'])-newStart})
 # Preserve original loop attributes on unchanged faces. New rings reuse Body material.
 keep=np.array([i for i in range(len(T))if i not in removed],int);faces=np.concatenate([T[keep],np.array(newT,int)]);new=bpy.data.meshes.new(me.name+'_OrderedLids');new.from_pydata(out['Basis'],[],faces.tolist());new.update()
 for m in mats:new.materials.append(m)
 for j,i in enumerate(keep):new.polygons[j].material_index=int(matidx[i])
 for poly in new.polygons:poly.use_smooth=True
 for name,arr in uvs.items():
  uv=new.uv_layers.new(name=name)
  for j,i in enumerate(keep):
   for dst,src in zip(new.polygons[j].loop_indices,oldLoops[i]):uv.data[dst].uv=arr[src]
  for poly in new.polygons[len(keep):]:
   for li in poly.loop_indices:
    v=new.loops[li].vertex_index
    value=newUV[v-len(p)]if v>=len(p)and name==next(iter(uvs))else(arr[first[v]].copy()if v<len(p)else arr[first[newColor[v-len(p)][0]]])
    if v in rimLash and name==next(iter(uvs)):
     mask=np.clip((value*64-.5)/63,0,1);mask[1]=max(mask[1],rimLash[v]);value=(.5+63*mask)/64
    uv.data[li].uv=value
 for name,(domain,dtype,arr)in colors.items():
  attr=new.color_attributes.new(name=name,type=dtype,domain=domain)
  if domain=='CORNER':
   for j,i in enumerate(keep):
    for dst,src in zip(new.polygons[j].loop_indices,oldLoops[i]):attr.data[dst].color=arr[src]
   for poly in new.polygons[len(keep):]:
    for li in poly.loop_indices:
     v=new.loops[li].vertex_index
     if v<len(p):
      col=arr[first[v]].copy()
      if name=='SkinPigment'and v in rimLash:col[:3]*=(1-rimLash[v])+np.array([.62,.44,.42])*rimLash[v]
     else:
      near,a,b,frac,f,lash=newColor[v-len(p)];col=arr[first[near]]*(1-frac)+(arr[first[a]]*(1-f)+arr[first[b]]*f)*frac
      if name=='SkinPigment':col[:3]*=(1-lash)+np.array([.62,.44,.42])*lash
     attr.data[li].color=col
  else:
   for i in range(len(p)):attr.data[i].color=arr[i]
   for i,(near,a,b,frac,f,lash)in enumerate(newColor):attr.data[len(p)+i].color=arr[near]*(1-frac)+(arr[a]*(1-f)+arr[b]*f)*frac
 body.shape_key_clear();body.data=new
 body.vertex_groups.clear()
 for name in groupNames:body.vertex_groups.new(name=name)
 for i,ww in enumerate(weights):
  for group,w in ww:
   if w>1e-8:body.vertex_groups[group].add([i],float(w),'REPLACE')
 for name,values in out.items():
  key=body.shape_key_add(name=name,from_mix=False)
  for v,q in zip(key.data,values):v.co=q
  key.value=0
 normals=[(0,0,0)]*len(new.loops)
 for j,i in enumerate(keep):
  if any(v in affected for v in T[i]):continue
  for dst,src in zip(new.polygons[j].loop_indices,oldLoops[i]):normals[dst]=oldN[src]
 new.normals_split_custom_set(normals);new.update()
 return {'sex':sex,'originalVertices':len(p),'vertices':len(new.vertices),'triangles':len(new.polygons),'removedTriangles':len(removed),'eyes':report}
