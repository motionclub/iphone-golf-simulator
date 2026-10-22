import bpy, collections
seen={}
for o in bpy.data.objects:
    if o.type!='MESH': continue
    k=o.data.name
    seen.setdefault(k,[len(o.data.polygons),0,o.name,[m.name if m else None for m in o.data.materials]])[1]+=1
big=[(f,n,k,on) for k,(f,n,on,m) in seen.items() if f>500]
for b in sorted(big,reverse=True): print(b)
print('prop meshes >500 faces (PLANT/ROCK/DRESS except SKIN/KNOLL/SAND/RUIN/ARCH):')
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(('PLANT_','ROCK_','DRESS_')) and len(o.data.polygons)>500 and not o.name.startswith(('ROCK_SKIN','DRESS_KNOLL','DRESS_SAND','DRESS_RUIN','DRESS_ARCH')): print(' ',o.name,len(o.data.polygons))
# materials
mats=collections.Counter(m.name for o in bpy.data.objects if o.type=='MESH' for m in o.data.materials if m)
print(mats)
print('plant materials',set(m.name for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('PLANT_') for m in o.data.materials))
print('linked dup plants', len(set(o.data.name for o in bpy.data.objects if o.name.startswith('PLANT_'))))
