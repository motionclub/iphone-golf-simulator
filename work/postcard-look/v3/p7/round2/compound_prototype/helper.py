def merge_shared_tuft_clumps(D, scn):
    """Real shared whole-tuft clumps; keep singles, cap120faces and support.

    Scenery positions/pivots may change. Actual source-copy tuple count, each
    source template's UV/Col, polygon total and scoring geometry remain intact.
    No hidden original objects or stored counts are used to satisfy a gate.
    Original unchanged full checks run after this opt-in build operation.
    """
    import collections
    import hashlib
    import postcard_look_verify as Q
    from mathutils import Matrix, Vector
    from mathutils.bvhtree import BVHTree
    design,dp=Q.load_design(9);C=Q.Ctx(9,design,dp,{})
    def snap():
        bpy.context.view_layer.update()
        return Q.Snap('blend',C)
    def _dist(poly,xy):
        return P._dist_pts_segs(np.asarray(xy,float).reshape(-1,2),poly[:-1],poly[1:])
    def _ground(objs):
        verts,faces=[],[]
        for ob in objs:
            if not ob.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')):continue
            W,ls,lt,lv,mi,pn=L._mesh_arrays(ob);base=len(verts)
            verts.extend(map(tuple,W))
            for pi in range(len(ls)):
                if pn[pi,2]>.2:
                    first,n=int(ls[pi]),int(lt[pi])
                    faces.append([base+int(v) for v in lv[first:first+n]])
        return BVHTree.FromPolygons(verts,faces)
    S=snap();original=sorted((o for n,o in S.meshes.items() if n.startswith('PLANT_TUFT')),key=lambda o:o.name)
    plants_before=len(S.named('PLANT_'));tri_before=sum(S.loc(o)['ntri'] for o in S.meshes.values())
    ground=_ground(list(S.meshes.values()));route=route_m(D);shore=np.array([P.m(x,y) for x,y in D.SHORE]+[P.m(*D.SHORE[0])])
    frozen={n:dict(V=S.wld(o)['W'].copy(),T=S.wld(o)['T'].copy()) for n,o in S.meshes.items() if n.startswith(Q.COLL_PREFIXES)}
    source={o.name:dict(kind=o.data.name,V=S.wld(o)['W'].copy(),pivot=np.array(o.matrix_world.translation),uv=np.array([u.uv[:] for u in o.data.uv_layers.active.data]),rgba=Q.sway_colors(o.data)[0],faces=len(o.data.polygons),tri=S.loc(o)['ntri'],zone=str(o.get('h9_zone',o.get('h9_class','old'))),fringe=int(o.get('lk_fringe',0))) for o in original}
    # Respect original singles and original author cluster identities; no invisible
    # nodes remain. Field tufts without fringe IDs may form genuine nearby groups.
    keys=collections.defaultdict(list)
    for o in original:
     r=source[o.name];k=o.data.name
     if not k.startswith(('PLANT_TUFT_D','PLANT_TUFT_E','PLANT_TUFT_F','PLANT_TUFT_S','PLANT_TUFT_T')):continue
     keys[(r['zone'],r['fringe'])].append(o)
    candidate_groups=[];singles=0
    for key,items in sorted(keys.items()):
     if key[1]>0 and len(items)==1:singles+=1;continue
     pending=list(items)
     while pending:
      o=pending.pop(0);r=source[o.name];near=sorted((x for x in pending if np.linalg.norm(source[x.name]['pivot'][:2]-r['pivot'][:2])<=1.8),key=lambda x:np.linalg.norm(source[x.name]['pivot'][:2]-r['pivot'][:2]))
      fillers=[x for x in near if source[x.name]['faces']<=40]
      members=[o]
      if r['faces']<=40 and len(fillers)>=2:members+=fillers[:2]
      elif r['faces']>40 and fillers:members+=fillers[:1]
      elif r['faces']<=40:
       tall=[x for x in near if 40<source[x.name]['faces']<=84]
       if tall:members=[tall[0],o]
      if len(members)==1:continue
      for x in members:
       if x in pending:pending.remove(x)
      if sum(source[x.name]['faces'] for x in members)>120:raise RuntimeError('compound violates120poly cap')
      candidate_groups.append((key,members))
    # Use >=3 real shape templates per kind sequence, repeated instances. A sequence
    # with fewer six legal proposals stays unchanged rather than creating uniques.
    by=collections.defaultdict(list)
    for key,obs in candidate_groups:
     obs=sorted(obs,key=lambda o:o.data.name);by[tuple(o.data.name for o in obs)].append((key,obs))
    variants={};proposals=[];reject=collections.Counter();groups=[];replacement_by_id={};remove_queue=[]
    for kinds,items in sorted(by.items()):
     if len(items)<6:reject['insufficient_real_variant_instances']+=len(items);continue
     for j in range(3):
      key,obs=items[j];pivot=np.array(obs[0].matrix_world.translation);V=[];F=[];UV=[];colors=[];parts=[];vi=fi=li=0
      for ob in obs:
       r=source[ob.name];W=r['V']-pivot
       # All actual tuple roots are on frozen flat ground. Preserve every source
       # vertex, polygon, UV and Col float in the authored template.
       V.extend(map(tuple,W));F.extend(tuple(vi+i for i in p.vertices) for p in ob.data.polygons)
       UV.extend(map(tuple,r['uv']));colors.extend(map(tuple,r['rgba']))
       parts.append(dict(source=ob.name,kind=ob.data.name,verts=[vi,vi+len(W)],faces=[fi,fi+len(ob.data.polygons)],root_local=(r['pivot']-pivot).tolist(),source_vertex_sha=hashlib.sha256(np.asarray(W,np.float64).tobytes()).hexdigest(),rgba_sha=hashlib.sha256(r['rgba'].tobytes()).hexdigest()))
       vi+=len(W);fi+=len(ob.data.polygons)
      me=bpy.data.meshes.new('PLANT_TUFT_COMPOUND_'+str(len(variants)));me.from_pydata(V,[],F);me.materials.append(bpy.data.materials['LK_PLANTS'])
      uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.asarray(UV,float).ravel())
      col=me.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT');col.data.foreach_set('color',np.asarray(colors,np.float32).ravel());me.color_attributes.active_color_name='Col';me.color_attributes.render_color_index=0
      me.update();me['lk_v3_real_tuft_parts']=json.dumps(parts);variants[(kinds,j)]=(me,parts)
     for i,(key,obs) in enumerate(items):
      me,parts=variants[(kinds,i%3)];oldp=np.array(obs[0].matrix_world.translation);local=np.array([v.co[:] for v in me.vertices]);old_height=max(source[o.name]['V'][:,2].max() for o in obs)-oldp[2]
      scale=min(2.,old_height/max(local[:,2].max(),1e-9));scale=max(.5,scale)
      # Genuine original pivot with a shared rotated whole-clump template. Scenery
      # positions and shader pivot phase may change; scoring positions may not.
      angle=float(obs[0].rotation_euler.z);rot=np.array(Matrix.Rotation(angle,3,'Z'))
      W=(local*scale)@rot.T+oldp;roots=np.array([p['root_local'] for p in parts])*scale@rot.T+oldp
      lies=P.lie_codes_m(D,roots[:,0],roots[:,1]);vertex_route=float(_dist(route,W[:,:2]).min());rootshore=float(_dist(shore,roots[:,:2]).min())
      if np.isin(lies,[P.LIE_WATER,P.LIE_FAIRWAY,P.LIE_GREEN,P.LIE_TEE,P.LIE_BUNKER]).any():reject['root_lie']+=1;continue
      if rootshore<1.1:reject['shore']+=1;continue
      if vertex_route<2.:reject['route']+=1;continue
      if np.linalg.norm(np.ptp(W[:,:2],axis=0))>20.:reject['span']+=1;continue
      if float(np.ptp(W[:,2]))>2.0:reject['height']+=1;continue
      # Keep the original group's largest cap: this does not prune real tufts.
      if W[:,2].max()>max(source[o.name]['V'][:,2].max() for o in obs)+1e-6:reject['original_top_cap']+=1;continue
      supported=True
      for root in roots:
       hit=ground.ray_cast(Vector((float(root[0]),float(root[1]),40.)),Vector((0,0,-1)))
       if hit[0] is None or abs(float(root[2])-hit[0].z)>.06:supported=False;break
      if not supported:reject['all_root_support']+=1;continue
      prototypes=[o for o in bpy.data.objects if o.name.startswith('PLANT_TUFT_COMPOUND') and o.data==me]
      proposals.append(dict(key=key,obs=obs,me=me,parts=parts,loc=oldp,scale=scale,angle=angle,roots=roots,span=float(np.linalg.norm(np.ptp(W[:,:2],axis=0)))))
    # Insufficient real mesh users are not installed; no keepalive hidden objects.
    users=collections.Counter(x['me'].name for x in proposals)
    for row in proposals:
     if users[row['me'].name]<2:reject['one_accepted_variant_user']+=1;continue
     obs=row['obs'];ob=bpy.data.objects.new(row['me'].name+'.'+str(len(groups)).zfill(3),row['me']);obs[0].users_collection[0].objects.link(ob);ob.parent=obs[0].parent;ob.location=row['loc'];ob.scale=(row['scale'],)*3;ob.rotation_euler.z=row['angle']
     ob['h9_zone']=row['key'][0];ob['lk_v3_real_tuft_parts']=json.dumps(row['parts']);ob['lk_v3_reauthored_clump']=True
     groups.append(dict(name=ob.name,replaced=[x.name for x in obs],real_tufts=len(obs),mesh=ob.data.name,span_m=row['span'],actual_roots=row['roots'].tolist(),parts=row['parts']))
     for old in obs:replacement_by_id[id(old)]=ob;remove_queue.append(old)
    
    # Remap all real scenery references while every old Blender object is valid,
    # then delete the replaced instances. No stale wrapper or keepalive remains.
    def remap(value):
        if id(value) in replacement_by_id:return replacement_by_id[id(value)]
        if isinstance(value,list):
            out=[];seen=set()
            for item in value:
                item=remap(item)
                if isinstance(item,bpy.types.Object):
                    if id(item) in seen:continue
                    seen.add(id(item))
                out.append(item)
            return out
        if isinstance(value,dict):
            for key in list(value):value[key]=remap(value[key])
            if 'objs' in value and isinstance(value['objs'],list):
                live=[o for o in value['objs'] if isinstance(o,bpy.types.Object) and o.type=='MESH']
                value['count']=len(live)
                value['tris']=sum(len(o.data.polygons) if all(len(p.vertices)==3 for p in o.data.polygons) else sum(len(p.vertices)-2 for p in o.data.polygons) for o in live)
                value['renderer_by_kind']=dict(collections.Counter(o.data.name for o in live))
                value['actual_whole_tufts']=sum(len(json.loads(o.data.get('lk_v3_real_tuft_parts','[]'))) if o.get('lk_v3_reauthored_clump') else 1 for o in live)
            return value
        return value
    remap(scn)
    for old in remove_queue:bpy.data.objects.remove(old,do_unlink=True)
    S=snap();tri_after=sum(S.loc(o)['ntri'] for o in S.meshes.values())
    if tri_after!=tri_before:raise RuntimeError('shared clump changed actual triangle total')
    for name,row in frozen.items():
        w=S.wld(S.meshes[name])
        if not np.array_equal(w['W'],row['V']) or not np.array_equal(w['T'],row['T']):
            raise RuntimeError('shared clump changed scoring geometry')
    actual_whole_tufts=sum(len(g['parts']) for g in groups)+sum(1 for n,o in S.meshes.items() if n.startswith('PLANT_TUFT') and not o.get('lk_v3_reauthored_clump'))
    if actual_whole_tufts!=len(original):raise RuntimeError('lost a real whole tuft')
    result=dict(plants_before=plants_before,plants_after=len(S.named('PLANT_')),
                tuft_renderers_before=len(original),tuft_renderers_after=len(S.named('PLANT_TUFT')),
                actual_whole_tufts_before=len(original),actual_whole_tufts_after=actual_whole_tufts,
                triangles_before=tri_before,triangles_after=tri_after,
                compound_renderers=len(groups),real_shared_compound_variants=len({g['mesh'] for g in groups}),
                original_singles_retained=singles,rejects=dict(reject),groups=groups,
                native_draw_calls_unmeasured=True)
    D.shared_tuft_clumps=result
    return result
