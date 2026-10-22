from pathlib import Path
W=Path(__file__).parent;G=W.parents[1]/'golf'/'bake-gallery-hero3.py';g=G.read_text();s=(W/'bake-tennis-audience-hero2.py').read_text()
s=s.replace('TennisSeatedHero2','TennisSeatedHero3').replace('TennisPromenadeHero2','TennisPromenadeHero3')
a=g.index('def shoulder_envelope');b=g.index("for sex in ['Male','Female']",a);helpers=g[a:b];where=s.index("for sex in ['Male','Female']");s=s[:where]+helpers+s[where:]
needle="  # Weight-based anatomical ownership prevents arbitrary cuts across the face."
s=s.replace(needle,"""  # Classify complete head and central neck before torso coverage is pruned.
""")
s=s.replace("   # Collar belongs to the torso; head includes a full neck down inside it.\n", """   if src.name.startswith('Body'):
    point=coords[v.index];offset=floor-standing_floor;head_floor=(1.445 if sex=='Male' else 1.425)-offset
    if point.z>head_floor or (point.z>1.31-offset and abs(point.x)<.095):return 'HEAD'
    if part=='HEAD':return 'BODY'
""")
needle="  per_vertex=[kind(v) for v in m.vertices];pieces={}"
s=s.replace(needle,"""  per_vertex=[kind(v) for v in m.vertices];pieces={}
  def evaluated_bounds(prefix):
   result=[]
   for item in inputs:
    if not item.name.startswith(prefix):continue
    ee=item.evaluated_get(deps);mm=ee.to_mesh();result.extend(item.matrix_world@v.co-Vector((0,0,floor)) for v in mm.vertices);ee.to_mesh_clear()
   return (min(v.z for v in result),max(v.z for v in result)) if result else (0,0)
  bottom_floor,bottom_top=evaluated_bounds('Kit_Bottom');sock_floor,sock_top=evaluated_bounds('Kit_Sock')
""")
s=s.replace("   part=max(counts,key=counts.get);pieces.setdefault(part,[]).append(poly)","""   part=max(counts,key=counts.get)
   if src.name.startswith('Body'):
    centre=sum((coords[v] for v in poly.vertices),Vector())/len(poly.vertices);offset=floor-standing_floor
    if centre.z>(1.445 if sex=='Male' else 1.425)-offset:part='HEAD'
    if part=='BODY' and centre.z>bottom_floor+.02:continue
    if part=='BODY' and centre.z<sock_top-.018:continue
    if part.startswith('ARM'):
     shoulder=Vector(anchor['LeftUpperArm' if part=='ARM_L' else 'RightUpperArm'])
     if (centre-shoulder).length<.17:continue
   pieces.setdefault(part,[]).append(poly)""")
s=s.replace("   # Cap the actual garment/anatomical shoulder cut loops before reduction.","   joint_rings={}\n   # Cap the actual garment/anatomical shoulder cut loops before reduction.")
s=s.replace("     if min((centre-Vector(anchor[name])).length", """     if src.name=='Kit_Top' and part=='BODY' and len(component)>30:
      side='Left' if centre.x>0 else 'Right';span=max(v.co.z for v in vs)-min(v.co.z for v in vs)
      if side not in joint_rings or span>joint_rings[side][2]:
       side_faces=[f for e in component for f in e.link_faces];index=side_faces[0].material_index if side_faces else 0
       joint_rings[side]=([v.co.copy() for v in vs],index,span)
     if min((centre-Vector(anchor[name])).length""")
s=s.replace("   if original_cloth:ob.data,count=fitted_cloth(original_cloth,scalp,ob.name,True)\n   else:count=decimate(ob,budget)","""   if src.name=='Kit_Top':ob.data,count=fitted_cloth(original_cloth,scalp,ob.name,True)
   elif original_cloth:ob.data,count=exterior_kit(original_cloth,scalp,ob.name,True,1800 if src.name=='Kit_Bottom' else (800 if src.name.startswith('Kit_Shoe') else 240))
   else:count=decimate(ob,budget)
   if src.name=='Kit_Top' and part=='BODY':ob.data,count=shoulder_envelope(ob.data,{k:(v[0],v[1]) for k,v in joint_rings.items()},True)""")
s=s.replace("   if original_cloth:\n    far.data,unused_count=fitted_cloth(original_cloth,scalp,far.name,False)","""   if src.name=='Kit_Top':
    far.data,unused_count=fitted_cloth(original_cloth,scalp,far.name,False)
    if part=='BODY':far.data,unused_count=shoulder_envelope(far.data,{k:(v[0],v[1]) for k,v in joint_rings.items()},False)
   elif original_cloth:
    far.data,unused_count=exterior_kit(original_cloth,scalp,far.name,False,250 if src.name=='Kit_Bottom' else (100 if src.name.startswith('Kit_Shoe') else 60))""")
(W/'bake-tennis-audience-hero3.py').write_text(s)
r=(W/'render-source-proof.py').read_text().replace("asset='TennisSeatedHero2' if '--seated' in sys.argv else 'TennisPromenadeHero2'","asset='TennisSeatedHero3' if '--seated' in sys.argv else 'TennisPromenadeHero3'");(W/'render-source3-proof.py').write_text(r)
