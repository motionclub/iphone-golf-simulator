"""Separate the approved sleeve and torso panels at the resting contact seam.
This prevents fabric from being stitched between a resting arm and the waist.
"""
import bpy,bmesh
from mathutils import Vector

def refine_panels(o,main):
 mesh=o.data;main=set(main);oldRows=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in mesh.vertices]
 verts=[];faces=[];rows=[];materials=[];smooth=[];mapping={}
 for poly in mesh.polygons:
  group='detail'
  if all(i in main for i in poly.vertices):
   mass=sum(sum(w for n,w in oldRows[i].items() if 'Arm' in n or 'Shoulder' in n) for i in poly.vertices)/len(poly.vertices)
   center=sum((mesh.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
   group=('Left' if center.x>0 else 'Right') if mass>.4 else 'torso'
  ids=[]
  for i in poly.vertices:
   key=(i,group)
   if key not in mapping:
    mapping[key]=len(verts);verts.append(mesh.vertices[i].co[:]);row=oldRows[i].copy()
    if group in ['Left','Right']:row={group+'UpperArm':1.}
    elif group=='torso':
     row={n:w for n,w in row.items() if n in ['Hips','Spine','Chest','UpperChest','Neck','Head','LeftUpperLeg','RightUpperLeg']}
     if not row:row={'UpperChest':1.}
    total=sum(row.values());rows.append({n:w/total for n,w in row.items()})
   ids.append(mapping[key])
  faces.append(ids);materials.append(poly.material_index);smooth.append(poly.use_smooth)
 new=bpy.data.meshes.new('Golf_ApprovedPoloPanels');new.from_pydata(verts,[],faces);new.update()
 for mat in mesh.materials:new.materials.append(mat)
 for poly,mi,sm in zip(new.polygons,materials,smooth):poly.material_index=mi;poly.use_smooth=sm
 o.data=new
 for vg in list(o.vertex_groups):o.vertex_groups.remove(vg)
 groups={n:o.vertex_groups.new(name=n) for n in {n for row in rows for n in row}}
 for i,row in enumerate(rows):
  for n,w in row.items():groups[n].add([i],w,'REPLACE')
 # Close the newly opened panel seams; existing garment openings are retained.
 bm=bmesh.new();bm.from_mesh(new);boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:
  result=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
  for face in result.get('faces',[]):face.smooth=True
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 bm.to_mesh(new);bm.free();new.update()
 print('GOLF_POLO_PANELS',len(verts),len(new.polygons),flush=True)
