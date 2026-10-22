"""Scratch-only Phase4 adapter: Phase1 footprints, closed cut shafts, real depth."""
import json, math, random
import numpy as np
import bpy
import postcard_props_lib as PL
import postcard_look_lib as L
import hole09_stone as ST


def _closed_cut_column(xy, z0, z1, rng, cuts=4):
    """Connected prism from actual5/6-side footprint plus four real corner cuts.

    The cuts truncate two upper and two lower corners without splitting a chip
    into a detached component. Horizontal cap remains one5..8-corner polygon.
    No stone is scaled to its height; its planes define final world dimensions.
    """
    xy=np.asarray(xy,float)
    cen=xy.mean(0); n=len(xy)
    normals=[]; offsets=[]
    for i in range(n):
        a,b=xy[i],xy[(i+1)%n]
        edge=b-a
        normal=np.array([edge[1],-edge[0],0.])
        normal/=np.linalg.norm(normal)
        if normal[:2]@(cen-a)>0: normal=-normal
        normals.append(normal); offsets.append(float(normal[:2]@a))
    normals.extend(([0.,0.,1.],[0.,0.,-1.]))
    offsets.extend((z1,-z0))
    width=max(np.linalg.norm(a-b) for a in xy for b in xy)
    first=rng.randrange(n)
    # Each fracture joins three actual incident edges. Radial planes can graze
    # an irregular footprint's second edge and produce a millimetre sliver.
    # Edge-point planes remove one real corner with bounded, visible chip legs.
    corners=(first,(first+n//2)%n,(first+1)%n,(first+1+n//2)%n)
    for i,iz in list(zip(corners,(1,1,0,0)))[:cuts]:
        corner=np.r_[xy[i],z1 if iz else z0]
        leg=rng.uniform(.16,.23)
        a=np.r_[xy[i]+leg*(xy[(i-1)%n]-xy[i]),corner[2]]
        b=np.r_[xy[i]+leg*(xy[(i+1)%n]-xy[i]),corner[2]]
        c=corner+np.array([0.,0.,-rng.uniform(.22,.36) if iz else rng.uniform(.22,.36)])
        normal=np.cross(b-a,c-a);normal/=np.linalg.norm(normal)
        if normal@(corner-a)<0:normal=-normal
        normals.append(normal);offsets.append(float(normal@a))
    result=ST.polyhedron(normals,offsets)
    if result is None: raise RuntimeError('column half-spaces are empty')
    vertices,planes=result
    faces=[f for _i,f in planes]
    if not ST.valid(vertices,planes,min_area=.0004,min_edge=.012):
        raise RuntimeError('column cut creates a sliver')
    # Direct across-corner width is measurement truth, rather than the input.
    actual=max(np.linalg.norm(a-b) for a in vertices[:,:2] for b in vertices[:,:2])
    if not (.6<=actual<=1.8): raise RuntimeError(f'actual column width{actual:g} outside.6..1.8m')
    return vertices,faces,dict(sides=n,width=actual,bottom=z0,top=z1,cuts=cuts)


def compact_column_band(D,path,top_z,bottom_z=0.,rows=3,seed=0,
                        width_m=(.8,1.5),name='ROCK_WALL_COMPACT',
                        max_faces=490,max_span_m=20.,clip=None):
    """One local geological band, grouped across actual neighboring rows.

    Caller supplies a small compact path segment and real neighboring rows.
    Full-height near clusters must each reach12m under H_NEAR_WALL; low
    geological bands are only a candidate where no such top gate applies.
    This prototype deliberately rejects an oversized cluster rather than
    flushing a row-wise thin tail. A full-ring caller must tile compact arc
    segments and geological bands, retaining complete neighboring-row groups.
    Returns one closed mesh and per-shaft metadata. No source files are edited.
    """
    if not (1<=max_faces<=490 and 1.9<=max_span_m<=20.):
        raise ValueError('compact rock caps remain <=490 faces and <=20m span')
    raw=PL.build_column_wall(D,path,top_z,bottom_z=bottom_z,width_m=width_m,
                            rows=rows,closed=False,seed=seed,name=name+'_RAW',
                            max_faces=490,max_span_m=20.,clip=clip)
    footprints=[]
    for ob in raw:
        for record in json.loads(ob['lk_v3_columns']):
            # Phase1 lays its first complete bottom ring at the vertex-range
            # start. Reuse that5/6-sided world footprint and its actual top.
            a=record['verts'][0]; n=record['sides']
            xy=np.array([tuple(ob.data.vertices[a+i].co)[:2] for i in range(n)])
            footprints.append((xy,record['top']))
    raw_names={o.name for o in raw}
    for old in raw:
        D.objects.pop(old.name,None)
        old_mesh=old.data;bpy.data.objects.remove(old,do_unlink=True)
        if old_mesh.users==0:bpy.data.meshes.remove(old_mesh)
    D.look_objects=[s for s in getattr(D,'look_objects',[]) if s not in raw_names]
    if not footprints:raise RuntimeError('no legal complete column footprints')
    rng=random.Random(seed+3217)
    mb=PL._MB(('LK_BASALT',)); specs=[]
    for xy,z1 in footprints:
        vertices,faces,spec=_closed_cut_column(xy,bottom_z,z1,rng)
        vi,fi=len(mb.V),len(mb.F)
        mb.V.extend(tuple(v) for v in vertices)
        for face in faces:mb.f(tuple(vi+i for i in face))
        spec.update(verts=[vi,len(mb.V)],faces=[fi,len(mb.F)])
        specs.append(spec)
    bounds=np.ptp(np.array(mb.V)[:,:2],axis=0)
    span=float(np.linalg.norm(bounds))
    if len(mb.F)>max_faces or span>max_span_m:
        raise RuntimeError(f'compact cluster exceeds limit: {len(mb.F)} faces,{span:.3f}m span')
    mesh=PL._finalize(name,mb,'box',smooth_angle=None,library=False)
    ob=bpy.data.objects.new(name,mesh)
    PL._collection_for('ROCK_').objects.link(ob)
    PL._parent(D,ob)
    ob['lk_v3_columns']=json.dumps(specs)
    ob['lk_v3_world_sized']=True
    ob['lk_v3_compact_band']=True
    return dict(object=ob,columns=specs,horizontal_span=span)


def compact_ring_tile(D,path,top_z,bottom_z=-1.6,rows=4,seed=0,
                      width_m=(1.68,1.78),pitch_m=1.875,depth_pitch_m=1.75,
                      name='ROCK_WALL_COMPACT',max_faces=490,max_span_m=20.,clip=None):
    """Compact full-height geological tile with actual depth and one cut/shaft.

    Four real staggered rows of broad 5/6-sided columns fit a ~7.5m path tile.
    They are whole closed connected stones. The single visible top fracture
    reduces wall triangle cost; no normals, material names or gates exempt it.
    Path should be oriented so the left side contains the backing rock. The
    caller must account for its 6..7m real inward depth in clearance checks.
    Each chunk is still independently checked by inherited rock_shape and PCA.
    This helper never flushes an underfilled thin tail or clips part of a stone.
    """
    if not (1<=max_faces<=490 and 1.9<=max_span_m<=20.):
        raise ValueError('compact rock caps remain <=490 faces and <=20m span')
    if not (.6<=width_m[0]<=width_m[1]<=1.8):raise ValueError('invalid world column widths')
    pts=np.asarray(path,float)[:,:2]
    seg=np.diff(pts,axis=0);lens=np.linalg.norm(seg,axis=1)
    acc=np.r_[0.,np.cumsum(lens)];length=float(acc[-1])
    if length<1e-6:raise ValueError('empty tile path')
    heights=np.full(len(pts),float(top_z)) if np.isscalar(top_z) else np.asarray(top_z,float)
    if len(heights)!=len(pts):raise ValueError('one height per path point required')
    count=max(1,int(round(length/pitch_m)))
    rng=random.Random(seed+7519);mb=PL._MB(('LK_BASALT',));specs=[]
    hex_columns=set(rng.sample(range(rows*count),max(1,round(rows*count*.25))))
    for row in range(rows):
        for k in range(count):
            # Stagger neighboring rows without appending a trailing narrow batch.
            sc=length*(k+.5+.15*(row%2))/count
            si=min(len(seg)-1,max(0,int(np.searchsorted(acc,sc,side='right')-1)))
            f=(sc-acc[si])/lens[si];tangent=seg[si]/lens[si]
            left=np.array([-tangent[1],tangent[0]])
            center=pts[si]+seg[si]*f+left*(.68+row*depth_pitch_m)
            width=rng.uniform(*width_m)
            angle=math.atan2(tangent[1],tangent[0])+math.pi/6+rng.uniform(-.12,.12)
            n=6 if row*count+k in hex_columns else 5
            xy=np.array([center+.5*width*np.array([math.cos(angle+math.tau*j/n),math.sin(angle+math.tau*j/n)]) for j in range(n)])
            if clip is not None and not all(clip(x,y) for x,y in xy):continue
            ht=float(heights[si]*(1-f)+heights[si+1]*f)-rng.uniform(.02,.55)
            vertices,faces,spec=_closed_cut_column(xy,bottom_z,ht,rng,cuts=1)
            vi,fi=len(mb.V),len(mb.F);mb.V.extend(tuple(v) for v in vertices)
            for face in faces:mb.f(tuple(vi+i for i in face))
            spec.update(verts=[vi,len(mb.V)],faces=[fi,len(mb.F)])
            specs.append(spec)
    if not specs:raise RuntimeError('no complete legal columns')
    span=float(np.linalg.norm(np.ptp(np.array(mb.V)[:,:2],axis=0)))
    if len(mb.F)>max_faces or span>max_span_m:
        raise RuntimeError(f'compact tile exceeds {len(mb.F)}faces,{span:.3f}m span')
    mesh=PL._finalize(name,mb,'box',smooth_angle=None,library=False)
    ob=bpy.data.objects.new(name,mesh);PL._collection_for('ROCK_').objects.link(ob);PL._parent(D,ob)
    ob['lk_v3_columns']=json.dumps(specs);ob['lk_v3_world_sized']=True
    ob['lk_v3_compact_tile']=True
    return dict(object=ob,columns=specs,horizontal_span=span,path_length=length,
                rows=rows,columns_per_row=count,triangle_projection_per_m=(sum(len(f)-2 for f in mb.F)/length))
