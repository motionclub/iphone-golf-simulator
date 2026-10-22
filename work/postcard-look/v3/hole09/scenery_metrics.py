"""Read actual staged Split scenery; output diagnostics only under v3."""
import json, os, sys
sys.dont_write_bytecode=True
import bpy, numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import postcard_lib as P
import postcard_look_lib as L
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
def opt(k,d=None): return args[args.index(k)+1] if k in args else d
blend=opt('--blend',os.path.dirname(__file__)+'/stage/hole_09.blend')
out=opt('--json',os.path.dirname(__file__)+'/scenery_metrics.json')
D=P.start('hole09_design',out_dir=os.path.dirname(__file__))
bpy.ops.wm.open_mainfile(filepath=blend,load_ui=False)
D.terrain=bpy.data.objects[D.terrain_name]
loops=L.terrain_top_loops(D,D.terrain)
D.loops=[xy.tolist() for xy,ids in loops]
D._distfield=None
objects=[o for o in bpy.data.objects if o.type=='MESH' and not all(c.name=='ASSET_LIBRARY' for c in o.users_collection)]
groups={}; triangles=0
for o in objects:
    o.data.calc_loop_triangles(); n=len(o.data.loop_triangles);triangles+=n
    k='skin' if o.name.startswith('ROCK_SKIN') else 'plant' if o.name.startswith('PLANT_') else 'masonry' if o.name.startswith(('DRESS_RUIN','DRESS_ARCH')) else 'knoll' if o.name.startswith('DRESS_KNOLL') else o.name.split('_')[0]
    groups.setdefault(k,dict(objects=0,triangles=0));groups[k]['objects']+=1;groups[k]['triangles']+=n
knolls=[]
for o in objects:
    if o.name.startswith('DRESS_KNOLL'):
        w=L._mesh_arrays(o)[0]
        knolls.append(dict(name=o.name,height_m=float(w[:,2].max()-D.play_z),world_min=w.min(0).tolist(),world_max=w.max(0).tolist(),cross_ratio=o.get('knoll_cross_ratio')))
skin=sorted((o for o in objects if o.name.startswith('ROCK_SKIN')),key=lambda o:o.name)
# The real four-bed shell has1 cap row plus3 rows per bed, and one
# continuous column for each original/added shoreline position. Diagnose
# its actual outermost spatial vertices, including the water-ellipse clips.
outline=[];nr=13
for o in skin:
    w=L._mesh_arrays(o)[0]
    if len(w)%nr: raise RuntimeError('Unexpected four-bed cliff topology')
    cols=w.reshape(-1,nr,3)
    s=P.signed_dist_m(D,cols[:,:,0].ravel(),cols[:,:,1].ravel()).reshape(-1,nr)
    xy=cols[np.arange(len(cols)),np.argmax(s,axis=1),:2]
    for p in xy:
        if not outline or not np.array_equal(p,outline[-1]):outline.append(p.copy())
if len(outline)>1 and np.array_equal(outline[-1],outline[0]):outline.pop()
xy=np.asarray(outline);n=len(xy);seg=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1)
longest=0.;maxends=None
for start in range(n):
    chain=[];run=0.
    for count in range(1,min(n,100)):
        end=(start+count)%n;chain.append(xy[end]);run+=seg[(end-1)%n]
        if count>1:
            delta=xy[end]-xy[start];length=float(np.linalg.norm(delta))
            if length<1e-8:break
            mid=np.asarray(chain)-xy[start]
            dev=np.abs(mid[:,0]*delta[1]-mid[:,1]*delta[0])/length
            if dev.max()>.10:break
        if run>longest:longest=run;maxends=(start,end)
result=dict(blend=blend,triangles=triangles,meshes=len(objects),groups=groups,
    frame_proof_inventory={p:sorted(o.name for o in objects if o.name.startswith(p)) for p in ('ROCK_SKIN','DRESS_KNOLL','DRESS_RUIN','DRESS_ARCH','SURF_','WATER_')},
    frozen_boundary=dict(loops=len(loops),outer_loops=int(sum(P.signed_area(x)>0 for x,ids in loops)),is_two_independent_islands=len(loops)>=2),
    knolls=knolls,cliff=dict(beds=4,chunks=len(skin),outline_points=n,outline_xy_m=xy.tolist(),max_straight_run_m=float(longest),run_endpoints=maxends,chord_deviation_m=.10,limit_m=4.,pass_gate=bool(longest<=4.)))
with open(out,'w') as f:json.dump(result,f,indent=2)
print('SPLIT_SCENERY '+json.dumps({k:result[k] for k in ('triangles','meshes','groups','frozen_boundary')}),flush=True)
print(f'GATE: CLIFF_OUTLINE_RUN {"PASS" if longest<=4 else "FAIL"} longest {longest:.6f}m, limit4m, chord deviation0.10m',flush=True)
