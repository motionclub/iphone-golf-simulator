from pathlib import Path
W=Path(__file__).parent;R=W.parents[3];g=(R/'ArtDir/golf/tools/bake-gallery-hero4.py').read_text();p=W/'bake-tennis-audience-hero3.py';s=p.read_text()
a=s.index('def fitted_cloth');b=s.index('def shoulder_envelope',a);a2=g.index('def fitted_cloth');b2=g.index('def shoulder_envelope',a2)
helper=g[a2:b2].replace('pos.z>1.19','pos.z>cloth_cut').replace('pos.z<1.22','pos.z<cloth_cut+.03').replace('median().z<1.15','median().z<cloth_cut-.04');s=s[:a]+helper+s[b:]
s=s.replace("if point.z>head_floor or (point.z>1.31-offset and abs(point.x)<.095):return 'HEAD'", "neck_split=anchor['Neck'][2]-(.02 if sex=='Male' else .01)\n    if point.z>head_floor or (point.z>neck_split and abs(point.x)<.095):return 'HEAD'")
s=s.replace("    if part=='BODY' and not leg and centre.z>bottom_floor+.02:continue", "    neck_split=anchor['Neck'][2]-(.02 if sex=='Male' else .01)\n    neck_junction=(1.31-offset<centre.z<neck_split+.025 and abs(centre.x)<.095 and -.105<centre.y<.10)\n    if part=='BODY' and not leg and not neck_junction and centre.z>bottom_floor+.02:continue")
s=s.replace("if near and 'Kit_Bottom' in name and not SEATED:","if False and near and 'Kit_Bottom' in name:")
# Shoes, socks and lower apparel at phone distance use sealed fitted point
# envelopes, not an aggressively collapsed thin original garment shell.
needle=" ob=bpy.data.objects.new(name+'_outer',mesh);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob\n"
assert needle in s
s=s.replace(needle,needle+''' if not near:
  original=mesh;bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.delete(bm,geom=list(bm.faces),context='FACES_ONLY')
  result=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
  used=sorted({v for f in bm.faces for v in f.verts},key=lambda v:v.index);remap={v:i for i,v in enumerate(used)}
  hull=bpy.data.meshes.new(name+'_closed_fitted_distance');hull.from_pydata([v.co.copy() for v in used],[],[[remap[v] for v in f.verts] for f in bm.faces]);hull.update()
  for material in original.materials:hull.materials.append(material)
  sole_index=next((i for i,m in enumerate(original.materials) if m and m.name.startswith('Kit_Sole')),None)
  low=min(v.co.z for v in hull.vertices);high=max(v.co.z for v in hull.vertices)
  for face in hull.polygons:
   centre=sum((hull.vertices[i].co for i in face.vertices),Vector())/len(face.vertices)
   face.material_index=sole_index if sole_index is not None and centre.z<low+(high-low)*.19 else 0;face.use_smooth=True
  bm.free();mesh=hull;ob.data=mesh
''')
s=s.replace("False,250 if src.name=='Kit_Bottom' else (100 if src.name.startswith('Kit_Shoe') else 60)","False,180 if src.name=='Kit_Bottom' else (100 if src.name.startswith('Kit_Shoe') else 40)")
s=s.replace("mod.ratio=.28;mod.use_collapse_triangulate=True", "mod.ratio=.20;mod.use_collapse_triangulate=True")
p.write_text(s)
