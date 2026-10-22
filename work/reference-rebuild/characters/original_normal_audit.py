import bpy,pathlib,math,json,collections
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';out={}
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'));b=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));me=b.data;me.calc_loop_triangles();head=b.vertex_groups['Head'].index;eyeZ=1.585 if sex=='Male' else 1.557
 p=[v.co.copy() for v in me.vertices];old=[v.normal.copy() for v in me.vertices];h=[sum(g.weight for g in v.groups if g.group==head) for v in me.vertices];keys={};ids=[];copies=[]
 for i,v in enumerate(p):
  k=tuple(round(x,6) for x in v)
  if k not in keys:keys[k]=len(copies);copies.append([])
  j=keys[k];ids.append(j);copies[j].append(i)
 sums=[Vector() for _ in copies]
 for t in me.loop_triangles:
  a,b1,c=t.vertices;n=(p[b1]-p[a]).cross(p[c]-p[a])
  for v in (a,b1,c):sums[ids[v]]+=n
 norm=[n.normalized() for n in sums];sel=[i for i,v in enumerate(p) if 1.40<v.z<1.69 and abs(v.x)<.10 and v.y<-.02];jaw=[i for i in sel if p[i].z<eyeZ-.055];angles=[math.degrees(old[i].angle(norm[ids[i]],0)) for i in sel];dups=[]
 for c in copies:
  if len(c)>1 and any(i in sel for i in c):dups.extend(math.degrees(old[c[0]].angle(old[i],0)) for i in c[1:])
 cuts=[(int(e.vertices[0]),int(e.vertices[1])) for e in me.edges if (h[e.vertices[0]]>=.75)!=(h[e.vertices[1]]>=.75) and any(i in sel for i in e.vertices)]
 cornerAngles=[math.degrees(c.vector.angle(norm[ids[me.loops[i].vertex_index]],0)) for i,c in enumerate(me.corner_normals) if me.loops[i].vertex_index in sel];out[sex]={'cornerVsGeometricMean':sum(cornerAngles)/len(cornerAngles),'cornerVsGeometricMax':max(cornerAngles),'hasCustomNormals':me.has_custom_normals,'allSmoothFaces':all(p.use_smooth for p in me.polygons),'frontVertices':len(sel),'frontRejectedBy75HeadMask':sum(h[i]<.75 for i in sel),'jawVertices':len(jaw),'jawRejectedBy75HeadMask':sum(h[i]<.75 for i in jaw),'headMaskBoundaryEdgesInFace':len(cuts),'sourceVsWeldedNormalAngleMean':sum(angles)/len(angles),'sourceVsWeldedNormalAngleMax':max(angles),'coincidentVertexNormalPairs':len(dups),'coincidentNormalAngleMax':max(dups,default=0)}
(O/'original-normal-audit.json').write_text(json.dumps(out,indent=2));print('SOURCE_NORMAL_AUDIT',out)
