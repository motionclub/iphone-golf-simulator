from pathlib import Path
p=Path('work/full-visual-overhaul/tennis/build-premium-coast.py')
s=p.read_text().replace('from mathutils.bvhtree import BVHTree','from mathutils.bvhtree import BVHTree\nfrom mathutils.geometry import delaunay_2d_cdt')
a=s.index('def wave(x,y):');b=s.index('# Real sparse erosion blocks')
s=s[:a]+'''def sample(table,x,y,default=0):
    fx=(x-X0)/STEP;fy=(y-Y0)/STEP;i=int(math.floor(fx));j=int(math.floor(fy));u=fx-i;v=fy-j
    return table.get((i,j),default)*(1-u)*(1-v)+table.get((i+1,j),default)*u*(1-v)+table.get((i,j+1),default)*(1-u)*v+table.get((i+1,j+1),default)*u*v

def wave(x,y):
    return math.sin(x*.035+y*.019)*1.45+math.sin(x*.073-y*.039)*.67+math.cos(x*.11+y*.087)*.28

def elevation(x,y):
    d=sample(distance,x,y)*STEP;k=sample(kind,x,y)
    return -3.85+min(d*(.42+.26*k),5.6+3.6*k)+wave(x,y)*min(1,d/16)
height={(i,j):elevation(X0+i*STEP,Y0+j*STEP) for i,j in land}

# The output shoreline is a smooth polygon, not raster-cell cuts. A constrained
# Delaunay mesh fills each coastline and the inner sand/grass transition rings.
def loops(threshold):
    directed={}
    for i,j in land:
        q=[(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
        if not all(distance.get(p,-1)>=threshold for p in q):continue
        for a,b in zip(q,q[1:]+q[:1]):
            if (b,a) in directed:del directed[b,a]
            else:directed[a,b]=True
    adjacent=collections.defaultdict(list)
    for a,b in directed:adjacent[a].append(b)
    results=[]
    while directed:
        a,b=next(iter(directed));chain=[a];start=a
        while (a,b) in directed:
            del directed[a,b];chain.append(b);a=b
            if a==start:break
            options=[n for n in adjacent[a] if (a,n) in directed]
            if not options:break
            b=options[0]
        if chain[-1]!=start or len(chain)<5:continue
        pts=[Vector((X0+i*STEP,Y0+j*STEP)) for i,j in chain[:-1]]
        area=sum(a.x*b.y-b.x*a.y for a,b in zip(pts,pts[1:]+pts[:1]))*.5
        if area<40:continue
        for _ in range(9):pts=[pts[k]*.5+pts[k-1]*.25+pts[(k+1)%len(pts)]*.25 for k in range(len(pts))]
        # Resample evenly after smoothing to avoid dense straight grid runs.
        arc=[0.];total=0.
        for a,b in zip(pts,pts[1:]+pts[:1]):total+=(b-a).length;arc.append(total)
        count=max(12,int(total/3.5));out=[];segment=0
        for n in range(count):
            target=n*total/count
            while segment<len(pts)-1 and arc[segment+1]<target:segment+=1
            t=(target-arc[segment])/max(.001,arc[segment+1]-arc[segment])
            out.append(pts[segment].lerp(pts[(segment+1)%len(pts)],t))
        results.append(out)
    return results
outer=loops(0);inner=loops(3);coords=[];constraints=[];regions=[];boundary_indices=set()
for ring in outer+inner:
    start=len(coords);coords.extend(ring);ids=list(range(start,len(coords)))
    constraints.extend(zip(ids,ids[1:]+ids[:1]))
    if ring in outer:regions.append(ids);boundary_indices.update(ids)
rng=random.Random(202610073)
for i,j in land:
    if distance[i,j]<2 or i%2 or j%2:continue
    coords.append(Vector((X0+i*STEP+rng.uniform(-1.2,1.2),Y0+j*STEP+rng.uniform(-1.2,1.2))))
xy,_,triangles,original,_,_=delaunay_2d_cdt(coords,constraints,regions,1,.001,True)
verts=[];colours=[]
for n,v in enumerate(xy):
    boundary=any(o in boundary_indices for o in original[n]);d=sample(distance,v.x,v.y)*STEP
    h=-3.85 if boundary else elevation(v.x,v.y)
    verts.append((v.x,v.y,h));colours.append((max(0,min(1,(d-4)/13)),0,sample(kind,v.x,v.y),1))
faces=[tuple(f) for f in triangles];slots=[0]*len(faces)
# Water-hidden boundary skirts use the smooth contour, with matching triangulated IDs.
edges={}
for f in faces:
    for a,b in zip(f,f[1:]+f[:1]):
        key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
for (a,b),count in edges.items():
    if count!=1:continue
    pa,pb=verts[a],verts[b];c=len(verts);verts.extend([(pb[0],pb[1],-4.55),(pa[0],pa[1],-4.55)]);colours.extend([(0,0,0,1)]*2)
    faces.append((a,b,c,c+1));slots.append(0)

def mesh(name,vertices,polygons,materials,slots):
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],polygons);me.update()
    for m in materials:me.materials.append(m)
    for p,s in zip(me.polygons,slots):p.material_index=s;p.use_smooth=True
    layer=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co;layer.data[li].uv=(v.x*.08,v.y*.08)
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return o
terrain=material('COAST_TERRAIN',(.2,.33,.11));coast=mesh('Smooth sculpted resort coast',verts,faces,[terrain],slots)
colour=coast.data.color_attributes.new(name='CoastBlend',type='FLOAT_COLOR',domain='POINT')
for v,c in zip(colour.data,colours):v.color=c

# A shore distance image gives calm turquoise shallows the same actual coast outline.
sea_distance={};q=collections.deque()
for i,j in land:sea_distance[i,j]=0;q.append((i,j))
while q:
    i,j=q.popleft()
    if sea_distance[i,j]>=9:continue
    for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
        p=i+dx,j+dy
        if 0<=p[0]<NX and 0<=p[1]<NY and p not in sea_distance:sea_distance[p]=sea_distance[i,j]+1;q.append(p)
image=bpy.data.images.new('CoastShallows',width=768,height=1024);pixels=[]
for j in range(1024):
    for i in range(768):
        x=X0+i/767*(NX-1)*STEP;y=Y0+j/1023*(NY-1)*STEP
        d=sample(sea_distance,x,y,20)*STEP;v=max(0,min(1,1-d/19));v=v*v*(3-2*v)
        pixels.extend((v,v,v,1))
image.pixels.foreach_set(pixels);image.filepath_raw=str(ROOT/'Unity/Assets/Resources/Tennis/Premium/CoastShallows.png');image.file_format='PNG';image.save()
''' +s[b:]
a=s.index('sites=[]');b=s.index('rocks=mesh')
s=s[:a]+'''sites=[p for p in land if 2<=distance[p]<=5 and (p[0]%5==0 and p[1]%3==0)]
rng.shuffle(sites);selected=[]
for p in sites:
    x=X0+p[0]*STEP;y=Y0+p[1]*STEP
    if abs(x)<38 and abs(y)<40:continue
    if any(math.hypot(x-a,y-b)<28 for a,b in selected):continue
    selected.append((x,y))
    if len(selected)>=16:break
for n,(x,y) in enumerate(selected):
    for member in range(rng.randint(3,5)):
        px=x+rng.uniform(-6,6);py=y+rng.uniform(-6,6);z=elevation(px,py)-1.9
        t=templates[(n+member)%len(templates)]
        m=Matrix.Translation(Vector((px,py,z)))@Matrix.Rotation(rng.uniform(0,math.tau),4,'Z')@Matrix.Diagonal((rng.uniform(9,15),rng.uniform(7,12),rng.uniform(3.3,5.7),1))@t.matrix_world
        start=len(rockverts);rockverts.extend(tuple(m@v.co) for v in t.data.vertices)
        rockfaces.extend(tuple(start+i for i in f.vertices) for f in t.data.polygons);rockslots.extend([0]*len(t.data.polygons))
''' +s[b:]
a=s.index('tree_sites=[]');b=s.index("bpy.ops.object.select_all(action='SELECT')",a)
s=s[:a]+'''tree_sites=[p for p in land if distance[p]>=6 and not(abs(X0+p[0]*STEP)<39 and abs(Y0+p[1]*STEP)<40)]
rng.shuffle(tree_sites);seeds=[];planted=[];understory=0
for i,j in tree_sites:
    x=X0+i*STEP;y=Y0+j*STEP
    if any(math.hypot(x-a,y-b)<36 for a,b in seeds):continue
    seeds.append((x,y))
    if len(seeds)>=22:break

def marker(typ,x,y,h,r):
    ob=bpy.data.objects.new(f'COAST_{typ}_{round(h*100)}_{round(r*100)}_{round(rng.uniform(0,360))}',None)
    bpy.context.collection.objects.link(ob);ob.location=(x,y,elevation(x,y)-.12)
for sx,sy in seeds:
    for n in range(rng.randint(9,15)):
        x=sx+rng.gauss(0,13);y=sy+rng.gauss(0,13)
        if sample(distance,x,y)<3.7 or (abs(x)<39 and abs(y)<40):continue
        if any(math.hypot(x-a,y-b)<5.0 for a,b in planted):continue
        planted.append((x,y));typ='PALM' if rng.random()<.22 else 'CANOPY'
        h=rng.uniform(10.2,14) if typ=='PALM' else rng.uniform(6.0,9.5);r=h*(.53 if typ=='PALM' else rng.uniform(.82,1.05))
        marker(typ,x,y,h,r)
        if n%3==0:
            for dx,dy in [(2.2,-1.7),(-2.0,2.4)]:
                if sample(distance,x+dx,y+dy)<3:continue
                marker('BUSH',x+dx,y+dy,rng.uniform(1.2,2.4),rng.uniform(1.5,2.6));understory+=1
''' +s[b:]
s=s.replace("'grid_metres':STEP", "'source_sample_grid_metres':STEP,'output_topology':'Smoothed closed shore and transition contours with constrained Delaunay fill','shore_loops':len(outer),'forest_pockets':len(seeds),'understory_markers':understory,'shore_bounds':[X0,Y0,(NX-1)*STEP,(NY-1)*STEP]")
p.write_text(s)
