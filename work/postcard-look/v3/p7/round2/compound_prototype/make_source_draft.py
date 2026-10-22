from pathlib import Path
import hashlib,json,ast
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[5]
prototype=(OUT/'prototype.py').read_text();a=prototype.index('S=snap();original=');b=prototype.index('S=snap();checks={}',a);body=prototype[a:b]
body=body.replace("ground=qa['ground_bvh'](list(S.meshes.values()));route=qa['HL'].route_m(D);", "ground=_ground(list(S.meshes.values()));route=route_m(D);")
body=body.replace("qa['dist_poly']",'_dist')
body=body.replace("variants={};proposals=[];reject=collections.Counter();groups=[]","variants={};proposals=[];reject=collections.Counter();groups=[];replacement_by_id={};remove_queue=[]")
body=body.replace(" for old in obs:bpy.data.objects.remove(old,do_unlink=True)"," for old in obs:replacement_by_id[id(old)]=ob;remove_queue.append(old)")
header='''def merge_shared_tuft_clumps(D, scn):
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
'''
tail='''
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
'''
helper=header+'\n'.join('    '+line for line in (body+tail).splitlines())+'\n';ast.parse(helper);(OUT/'helper.py').write_text(helper)
entries=[]
for name in ('hole09_look.py','hole09_build.py'):
 target=ROOT/'blender/scripts'/name;old=target.read_bytes();snapshot=OUT/('old_'+name);snapshot.write_bytes(old)
 if name=='hole09_look.py':new=old.decode()+'\n\n# P7 round2: opt-in genuine shared whole-tuft clumps.\n'+helper
 else:
  new=old.decode();needle='batch_stats = HL.merge_static_scenery(D, scn)';assert new.count(needle)==1
  pos=new.index('\nbpy.context.view_layer.update()',new.index(needle));new=new[:pos]+"\ncompound_stats=HL.merge_shared_tuft_clumps(D,scn)\nprint('[hole09] actual shared clumps', {k:v for k,v in compound_stats.items() if k!='groups'},flush=True)"+new[pos:]
  needle2='masonry_batches=batch_stats, cliff_outline=';assert new.count(needle2)==1;new=new.replace(needle2,'masonry_batches=batch_stats, shared_tuft_clumps=compound_stats, cliff_outline=',1)
 ast.parse(new);draft=OUT/('draft_'+name);draft.write_text(new)
 entries.append(dict(target=str(target),old_sha256=hashlib.sha256(old).hexdigest(),old_snapshot=str(snapshot),new_sha256=hashlib.sha256(draft.read_bytes()).hexdigest(),draft=str(draft),mode='0o644'))
protected=[dict(path=str(ROOT/'blender/scripts'/name),sha256=hashlib.sha256((ROOT/'blender/scripts'/name).read_bytes()).hexdigest()) for name in ('hole09_design.py','postcard_look_verify.py','hole09_qa.py')]
plan=dict(root=str(ROOT),v3=str(ROOT/'work/postcard-look/v3'),entries=entries,protected=protected,production_applied=False,prototype_only_native_unmeasured=True)
p=OUT/'apply_plan.json';p.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(plan=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),entries=entries),indent=2))
