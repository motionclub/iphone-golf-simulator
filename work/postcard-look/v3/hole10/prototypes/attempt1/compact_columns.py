"""Scratch-only Phase4 adapter: Phase1 footprints, closed cut shafts, real depth."""
import json, math, random
import numpy as np
import bpy
import postcard_props_lib as PL
import postcard_look_lib as L
import hole09_stone as ST


def _closed_cut_column(xy, z0, z1, rng):
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
    for k,iz in enumerate((1,1,0,0)):
        i=(first+k*(2 if n==6 else 1))%n
        direction=xy[i]-cen; direction/=np.linalg.norm(direction)
        normal=np.r_[direction,.62 if iz else -.62]
        normal/=np.linalg.norm(normal)
        corner=np.r_[xy[i],z1 if iz else z0]
        normals.append(normal)
        offsets.append(float(normal@corner)-rng.uniform(.10,.16)*width)
    result=ST.polyhedron(normals,offsets)
    if result is None: raise RuntimeError('column half-spaces are empty')
    vertices,planes=result
    faces=[f for _i,f in planes]
    if not ST.valid(vertices,planes,min_area=.0004,min_edge=.012):
        raise RuntimeError('column cut creates a sliver')
    # Direct across-corner width is measurement truth, rather than the input.
    actual=max(np.linalg.norm(a-b) for a in vertices[:,:2] for b in vertices[:,:2])
    if not (.6<=actual<=1.8): raise RuntimeError(f'actual column width{actual:g} outside.6..1.8m')
    return vertices,faces,dict(sides=n,width=actual,bottom=z0,top=z1,cuts=4)


def compact_column_band(D,path,top_z,bottom_z=0.,rows=3,seed=0,
                        width_m=(.8,1.5),name='ROCK_WALL_COMPACT',
                        max_faces=490,max_span_m=20.):
    """One local geological band, grouped across actual neighboring rows.

    Caller supplies a small compact path segment and real neighboring rows.
    Full-height near clusters must each reach12m under H_NEAR_WALL; low
    geological bands are only a candidate where no such top gate applies.
    This prototype deliberately rejects an oversized cluster rather than
    flushing a row-wise thin tail. A full-ring caller must tile compact arc
    segments and geological bands, retaining complete neighboring-row groups.
    Returns one closed mesh and per-shaft metadata. No source files are edited.
    """
    raw=PL.build_column_wall(D,path,top_z,bottom_z=bottom_z,width_m=width_m,
                            rows=rows,closed=False,seed=seed,name=name+'_RAW',
                            max_faces=490,max_span_m=20.)
    footprints=[]
    for ob in raw:
        for record in json.loads(ob['lk_v3_columns']):
            # Phase1 lays its first complete bottom ring at the vertex-range
            # start. Reuse that5/6-sided world footprint and its actual top.
            a=record['verts'][0]; n=record['sides']
            xy=np.array([tuple(ob.data.vertices[a+i].co)[:2] for i in range(n)])
            footprints.append((xy,record['top']))
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
    bpy.data.collections.get('ENVIRONMENT',bpy.context.scene.collection).objects.link(ob)
    PL._parent(D,ob)
    ob['lk_v3_columns']=json.dumps(specs)
    ob['lk_v3_world_sized']=True
    ob['lk_v3_compact_band']=True
    raw_names={o.name for o in raw}
    for old in raw:
        D.objects.pop(old.name,None)
        old_mesh=old.data;bpy.data.objects.remove(old,do_unlink=True)
        if old_mesh.users==0:bpy.data.meshes.remove(old_mesh)
    D.look_objects=[s for s in getattr(D,'look_objects',[]) if s not in raw_names]
    return dict(object=ob,columns=specs,horizontal_span=span)
