"""Clone-only cloth cage and barycentric detail binding. Run in Blender.
No animation samples or clip-specific data are inputs.
"""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parent
g=np.load(root/'out/GolfKitHero_Female/unity/Kit_Top_final.npz')
points=g['pos'];faces=g['tri'][(g['part']==0)&np.isin(g['panel'],[0,1,2,3])]
mesh=bpy.data.meshes.new('SM_GolfClothCage');mesh.from_pydata(points.tolist(),[],faces.tolist());mesh.update()
bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00015)
# The old seam projection left tiny overlapping faces at the armholes.
# A simulation surface must have exactly two faces at every interior edge.
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.00001)
while any(len(e.link_faces)>2 for e in bm.edges):
 bad={f for e in bm.edges if len(e.link_faces)>2 for f in e.link_faces}
 face=min(bad,key=lambda f:(-sum(len(e.link_faces)>2 for e in f.edges),f.calc_area()))
 bmesh.ops.delete(bm,geom=[face],context='FACES_ONLY')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
obj=bpy.data.objects.new('SM_GolfClothCage',mesh)
collection=bpy.data.collections.new('COL_GarmentClothPrototype');bpy.context.scene.collection.children.link(collection);collection.objects.link(obj)
modifier=obj.modifiers.new('Low density simulation surface','DECIMATE');modifier.ratio=1200/len(mesh.polygons)
deps=bpy.context.evaluated_depsgraph_get();simple=bpy.data.meshes.new_from_object(obj.evaluated_get(deps))
obj.modifiers.clear();obj.data=simple
bm=bmesh.new();bm.from_mesh(simple)
while any(len(e.link_faces)>2 for e in bm.edges):
 bad={f for e in bm.edges if len(e.link_faces)>2 for f in e.link_faces}
 face=min(bad,key=lambda f:(-sum(len(e.link_faces)>2 for e in f.edges),f.calc_area()))
 bmesh.ops.delete(bm,geom=[face],context='FACES_ONLY')
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(simple);bm.free()
simple.calc_loop_triangles();p=np.asarray([v.co[:]for v in simple.vertices]);tri=np.asarray([t.vertices[:]for t in simple.loop_triangles])
# Transfer the existing garment field, never body-nearest weights.
tree=BVHTree.FromPolygons(points.tolist(),faces.tolist(),all_triangles=True)
def nearest(tree,p,faces,points):
 q,_,fi,_=tree.find_nearest(Vector(p));t=faces[fi];a,b,c=points[t];ab=b-a;ac=c-a;ap=np.asarray(q)-a
 aa=ab@ab;bb=ac@ac;cross=ab@ac;d=max(aa*bb-cross*cross,1e-20)
 u=(bb*(ap@ab)-cross*(ap@ac))/d;v=(aa*(ap@ac)-cross*(ap@ab))/d
 bary=np.clip([1-u-v,u,v],0,1);bary/=bary.sum();return int(fi),t,bary
manifest=json.loads((root/'out/GolfKitHero_Female/unity/manifest.json').read_text());piece=next(x for x in manifest['pieces']if x['name']=='Kit_Top')
hero=json.loads((root/'dump-polo/GolfKitHero_Female/hero.json').read_text())
# cv2io holds the authoritative palette order for exported npz indices.
import sys
sys.path.insert(0,str(root.parent/'clothing-v2/py'));import cv2io
cv2io.DUMP=str(root/'dump-polo');h=cv2io.Hero('GolfKitHero_Female');palette=[h.body.bones.index(n)for n in piece['bones']]
W=np.zeros((len(points),len(h.body.bones)))
for k in range(4):np.add.at(W,(np.arange(len(points)),g['bi'][:,k]),g['bw'][:,k])
weights=[]
for v in p:
 _,t,bary=nearest(tree,v,faces,points);w=(W[t]*bary[:,None]).sum(0)[palette];ids=np.argsort(w)[-4:][::-1];ws=w[ids];ws/=ws.sum()
 weights.append(dict(ids=ids.tolist(),values=ws.tolist()))
tree=BVHTree.FromPolygons(p.tolist(),tri.tolist(),all_triangles=True);mapping=[]
for v in points:
 fi,t,bary=nearest(tree,v,tri,p);a,b,c=p[t];u=b-a;u/=np.linalg.norm(u);n=np.cross(b-a,c-a);n/=np.linalg.norm(n);vv=np.cross(n,u)
 offset=v-(p[t]*bary[:,None]).sum(0)
 mapping.append(dict(triangle=fi,bary=dict(zip(['x','y','z'],bary.tolist())),offset=dict(zip(['x','y','z'],[float(offset@u),float(offset@vv),float(offset@n)]))))
detail_panel=np.full(len(points),-1)
for panel in [0,1,2,3,4,5,6,7]:detail_panel[np.unique(g['tri'][g['panel']==panel])]=panel
data=dict(points=[dict(zip(['x','y','z'],v.tolist()))for v in p],triangles=tri.ravel().tolist(),weights=weights,mapping=mapping,rigidDetail=np.isin(detail_panel,[4,5,6,7]).tolist())
dest=root/'cage-prototype';dest.mkdir(exist_ok=True);(dest/'golf_cage.json').write_text(json.dumps(data,separators=(',',':')))
# Topological evidence: sewn main shell, only intended neck/hem/cuff boundaries.
bm=bmesh.new();bm.from_mesh(simple);boundary=[e for e in bm.edges if e.is_boundary]
report=dict(vertices=len(p),triangles=len(tri),boundaryEdges=len(boundary),nonmanifoldInteriorEdges=sum(not e.is_manifold and not e.is_boundary for e in bm.edges),animationInputs=0)
bm.free();(dest/'topology.json').write_text(json.dumps(report,indent=2));print(report)
collection.hide_render=True;collection.hide_viewport=True
