import bpy,json,pathlib
P=pathlib.Path(__file__).parent
for a in ['shrub_02','shrub_03','fern_02']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'vendor/polyhaven'/a/(a+'_1k.blend')))
 print('ASSET',a)
 for o in bpy.data.objects:
  if o.type=='MESH':print('MODEL',o.name,len(o.data.vertices),sum(len(f.vertices)-2 for f in o.data.polygons),list(o.dimensions),[m.name for m in o.data.materials],[(u.name,u.data_type,u.domain) for u in o.data.attributes if 'UV' in u.name])
