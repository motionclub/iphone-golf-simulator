import bpy,math,json
from pathlib import Path
from mathutils import Vector,kdtree
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/full-visual-overhaul/tennis')
bpy.ops.wm.open_mainfile(filepath=str(W/'TennisCoast-v3.blend'))
coast=bpy.data.objects.get('Smooth sculpted resort coast');me=coast.data
# Extract actual smooth outer edges at the shore elevation, including the exact
# rendered contour rather than the initial footprint raster.
edges=[]
for edge in me.edges:
 a,b=[coast.matrix_world@me.vertices[n].co for n in edge.vertices]
 if abs(a.z+3.85)<.0001 and abs(b.z+3.85)<.0001:edges.append((a,b))
points=[]
for a,b in edges:
 count=max(1,math.ceil((b-a).length/.45))
 points.extend(a.lerp(b,n/count) for n in range(count))
tree=kdtree.KDTree(len(points))
for n,p in enumerate(points):tree.insert(Vector((p.x,p.y,0)),n)
tree.balance();x0=-272.5;y0=-217.5;w=537.5;h=692.5;size=(1024,1280)
image=bpy.data.images.new('Smooth shoreline distance',width=size[0],height=size[1]);pixels=[]
for j in range(size[1]):
 for i in range(size[0]):
  x=x0+i/(size[0]-1)*w;y=y0+j/(size[1]-1)*h;d=tree.find(Vector((x,y,0)))[2]
  value=max(0,1-d/22);value=value*value*(3-2*value);pixels.extend((value,value,value,1))
image.pixels.foreach_set(pixels);image.filepath_raw=str(W/'CoastShallows-v4.png');image.file_format='PNG';image.save()
for name,p in [('COAST_SHORE_ORIGIN',(x0,y0,0)),('COAST_SHORE_U',(x0+w,y0,0)),('COAST_SHORE_V',(x0,y0+h,0))]:bpy.data.objects[name].location=p
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.fbx(filepath=str(W/'TennisCoast-v4.fbx'),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,path_mode='AUTO');bpy.ops.wm.save_as_mainfile(filepath=str(W/'TennisCoast-v4.blend'))
print('SMOOTH_SHORE_SDF',json.dumps({'contour_edges':len(edges),'contour_samples':len(points),'pixels':size,'bounds':[x0,y0,w,h],'waterline':'actual smoothed rendered contour, 30m padded bounds'}))
