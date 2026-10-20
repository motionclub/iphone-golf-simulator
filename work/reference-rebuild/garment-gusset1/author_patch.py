from pathlib import Path
S=Path.cwd()/'work/reference-rebuild/garment-weight-transition/mask3/author_local_cloth_frontcull.py';__file__=str(S);exec(S.read_text().split('regions=np.array')[0])
exec((R/'work/reference-rebuild/garment-gusset1/lod_context.py').read_text())
Z=R/'work/reference-rebuild/garment-gusset1';Z=Z/'lod' if os.environ.get('GUSSET_LOD')=='1' else Z
armtop=(tw*np.isin(ti,[top['bones'].index('LeftUpperArm'),top['bones'].index('RightUpperArm')])).sum(1)
center=tr[tt].mean(1);sel=(abs(center[:,0])>.085)&(abs(center[:,0])<.19)&(center[:,1]>1.10)&(center[:,1]<1.30)&(np.max(armtop[tt],axis=1)>.70)&(np.min(armtop[tt],axis=1)<.30)
# Grow one welded edge ring to move the outer patch boundary off the failing chord.
_,aliases=np.unique(np.round(tr,5),axis=0,return_inverse=True)
for _ in range(1):
 keys=set()
 for f in np.where(sel)[0]:
  for a,b in [(0,1),(1,2),(2,0)]:keys.add(tuple(sorted(aliases[tt[f,[a,b]]])))
 for f,tri in enumerate(aliases[tt]):
  if any(tuple(sorted(tri[[a,b]])) in keys for a,b in [(0,1),(1,2),(2,0)]):sel[f]=True
origtri=tt.copy();parents=np.arange(len(tt));sources=[{i:1.0} for i in range(len(base))];verts=list(base);outtri=tt.tolist();armvals=armtop.tolist()
# Adaptive split along the high-stretch arm-to-torso binding direction. Every
# incident face receives the same split; source boundaries remain conforming.
for level in range(4):
 edges=set()
 for f,t in enumerate(outtri):
  if sel[parents[f]]:
   candidates=[(np.linalg.norm(np.array(verts[t[a]])-verts[t[b]])+.4*abs(armvals[t[a]]-armvals[t[b]]),tuple(sorted((t[a],t[b])))) for a,b in [(0,1),(1,2),(2,0)]]
   score,edge=max(candidates)
   if score>.016:edges.add(edge)
 # Every UV copy of a physical edge must receive the same split. Otherwise
 # the curved LBS midpoint opens a T-junction against an unsplit seam copy.
 _,physical=np.unique(np.round(xf(arr(top,'rendererToRoot',4),np.array(verts)),5),axis=0,return_inverse=True)
 physicalEdges={tuple(sorted((physical[a],physical[b]))) for a,b in edges}
 for tri in outtri:
  for j,k in [(0,1),(1,2),(2,0)]:
   a,b=tri[j],tri[k]
   if tuple(sorted((physical[a],physical[b]))) in physicalEdges:edges.add(tuple(sorted((a,b))))
 mids={}
 for a,b in sorted(edges):
  mids[a,b]=len(verts);verts.append((np.array(verts[a])+verts[b])*.5);armvals.append((armvals[a]+armvals[b])*.5);s={}
  for q in [a,b]:
   for k,v in sources[q].items():s[k]=s.get(k,0)+.5*v
  sources.append(s)
 newtri=[];newpar=[]
 for f,(a,b,c) in enumerate(outtri):
  ab=mids.get(tuple(sorted((a,b))));bc=mids.get(tuple(sorted((b,c))));ca=mids.get(tuple(sorted((c,a))));bits=(ab is not None)+(bc is not None)+(ca is not None)
  if bits==0:ts=[(a,b,c)]
  elif bits==3:ts=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
  elif bits==1:
   if ab is not None:ts=[(a,ab,c),(ab,b,c)]
   elif bc is not None:ts=[(b,bc,a),(bc,c,a)]
   else:ts=[(c,ca,b),(ca,a,b)]
  else:
   if ab is None:ts=[(c,ca,bc),(ca,a,b),(ca,b,bc)]
   elif bc is None:ts=[(a,ab,ca),(ab,b,c),(ab,c,ca)]
   else:ts=[(b,bc,ab),(bc,c,a),(bc,a,ab)]
  newtri.extend(ts);newpar.extend([parents[f]]*len(ts))
 outtri=newtri;parents=np.array(newpar)
verts=np.array(verts);ttnew=np.array(outtri);sourceids=np.zeros((len(verts),3),int);sourceweights=np.zeros((len(verts),3))
for i,s in enumerate(sources):
 for j,(k,v) in enumerate(s.items()):sourceids[i,j]=k;sourceweights[i,j]=v
# Original endpoint bindings, interpolated within each original face. No Body
# weight copying; each original source vertex preserves its anatomical role.
dense=np.zeros((len(base),len(top['bones'])))
for j in range(4):dense[np.arange(len(base)),ti[:,j]]+=tw[:,j]
dn=np.einsum('nk,nkb->nb',sourceweights,dense[sourceids]);ids=np.argsort(-dn,axis=1)[:,:4];ww=np.take_along_axis(dn,ids,1);ww/=ww.sum(1)[:,None];ids[:len(base)]=ti;ww[:len(base)]=tw
uv=np.einsum('nk,nkj->nj',sourceweights,arr(top,'uv',2)[sourceids]);norm=np.einsum('nk,nkj->nj',sourceweights,arr(profile,'normals',3)[sourceids]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
root=xf(arr(top,'rendererToRoot',4),verts);_,alias=np.unique(np.round(root,5),axis=0,return_inverse=True)
active=np.zeros(len(verts),bool);active[np.unique(ttnew[sel[parents]])]=True
# Pin the outer welded boundary of the patch so no seam can disconnect.
inside=set(np.unique(alias[ttnew[sel[parents]]]).tolist());outside=set(np.unique(alias[ttnew[~sel[parents]]]).tolist());boundary=inside&outside
free=active&~np.isin(alias,list(boundary))
# Only local Body torso/upperarm faces are needed for physical clearance.
br=rest[bt].mean(1);bodyfaces=np.where((abs(br[:,0])>.055)&(abs(br[:,0])<.27)&(br[:,1]>1.04)&(br[:,1]<1.405))[0]
np.savez_compressed(Z/'patch.npz',vertices=verts,triangles=ttnew,parents=parents,indices=ids,weights=ww,normals=norm,uv=uv,sourceids=sourceids,sourceweights=sourceweights,selectedSourceFaces=np.where(sel)[0],active=active,free=free,aliases=alias,bodyfaces=bodyfaces)
report={'originalVertices':len(base),'vertices':len(verts),'originalFaces':len(origtri),'faces':len(ttnew),'selectedSourceFaces':int(sel.sum()),'freeVertices':int(free.sum()),'bodyCollisionFaces':len(bodyfaces),'originalVertexPositionError':float(np.max(np.abs(verts[:len(base)]-base))),'weightsRule':'Original bindings preserved at existing vertices; barycentric interpolation for new vertices, four largest influences normalized.','clearanceRule':'Outward exit against 104-vertex Body proxy, 3 mm clearance, 40 mm total displacement cap; six triangle contact iterations capped at 8 mm each. Original outer boundary pinned. Corrected UV-alias edge subdivisions.'}
ta=alias[ttnew];edges=np.sort(np.concatenate([ta[:,[0,1]],ta[:,[1,2]],ta[:,[2,0]]]),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True);report['weldedOpenEdges']=int((counts==1).sum());report['weldedNonmanifoldEdges']=int((counts>2).sum());
(Z/'author-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
