from pathlib import Path
import hashlib
root=Path.cwd(); lp=root/'blender/scripts/hole10_look.py'; bp=root/'blender/scripts/hole10_build.py'
a=(root/'work/postcard-look/v3/hole10/prototypes/compact_columns.py').read_text()
assert hashlib.sha256(a.encode()).hexdigest()=='4b6e0402e0e30f583e21e590266114308481f66613c49f6d35589f83f177aefc'
s=lp.read_text();s=s.replace('import math\n','import math\nimport json\n',1).replace('import postcard_props_lib as PL\n','import postcard_props_lib as PL\nimport hole09_stone as ST\n',1)
helper=a[a.index('def _closed_cut_column'):a.index('def compact_column_band')]+a[a.index('def compact_ring_tile'):]
s+='\n\n# Phase 4: world-sized complete columns, adapted from the measured scratch fixture.\n'+helper
s+='''

def _ring_tiles(cx, cy, th, radius, target_m=9.375):
    """Closed actual shoreline paths partitioned by distance, no thin final tail."""
    xy=np.c_[cx+radius*np.cos(th),cy+radius*np.sin(th)]
    xy=np.vstack([xy,xy[:1]])
    ds=np.linalg.norm(np.diff(xy,axis=0),axis=1);arc=np.r_[0.,np.cumsum(ds)]
    n=max(1,round(arc[-1]/target_m))
    for k in range(n):
        q=np.linspace(arc[-1]*k/n,arc[-1]*(k+1)/n,5)
        yield k,np.c_[np.interp(q,arc,xy[:,0]),np.interp(q,arc,xy[:,1])]


def near_wall(D,W,kinds_var):
    """Three real broad column rows, low full-height tiles; no scaled wall pieces."""
    cx,cy=P.m(W['cx'],W['cd']);th,rad=near_radius_profile(D,W)
    out=[]
    for k,path in _ring_tiles(cx,cy,th,rad):
        c=path.mean(0);a=math.atan2(c[1]-cy,c[0]-cx)
        h=22.5+3.0*math.sin(5*a+.2)
        if WINDOW[0]<=heading_from_tee(*c)<=WINDOW[1]:h=15.5+2.0*math.sin(3*a)
        r=compact_ring_tile(D,path,h,seed=102000+k,name=f'ROCK_WALL_BASALT_N_V3_{k:03d}')
        ob=r['object'];UV_STATS[ob.name]=author_uv(ob.data,random.Random(104000+k),uf=.7,vf=.32,p_glow=.3)
        out.append(ob)
    return out,th,rad


def far_ring(D,W,kinds_var):
    """Continuous low ring with seven genuine narrow tall fractured ridge sectors."""
    cx,cy=P.m(W['cx'],W['cd']);th=np.linspace(0,math.tau,1440,endpoint=False)
    rad=np.full(len(th),.5*(W['r_inner']+W['r_outer'])*P.YD)
    out=[]
    for k,path in _ring_tiles(cx,cy,th,rad):
        c=path.mean(0);a=math.atan2(c[1]-cy,c[0]-cx)%math.tau
        in_window=WINDOW[0]<=heading_from_tee(*c)<=WINDOW[1]
        h=21.5+3*math.sin(9*a+.7)
        peak=abs((a-.2+math.pi/7)%(math.tau/7)-math.pi/7)<math.radians(4.3) and not in_window
        heights=[h,44.2,69.2] if peak else [h]
        if in_window:heights=[18.5+2*math.sin(4*a)]
        prior=None
        for j,top in enumerate(heights):
            r=compact_ring_tile(D,path,top,seed=101000+k,name=f'ROCK_WALL_BASALT_F_V3_{k:03d}_{j}',bottoms=None if prior is None else [c['top'] for c in prior['columns']])
            ob=r['object'];UV_STATS[ob.name]=author_uv(ob.data,random.Random(105000+k*7+j),uf=.7,vf=.32,p_glow=.3)
            if prior is not None:
                ob['lk_v3_support_gap_m']=max(abs(c['bottom']-b['top']) for c,b in zip(r['columns'],prior['columns']))
            out.append(ob);prior=r
    return out


def make_lava_stack(D,s,top,seed):
    x,y=P.m(s['x'],s['d']);yaw=(seed*.618)%math.tau
    tangent=np.array([math.cos(yaw),math.sin(yaw)]);left=np.array([-tangent[1],tangent[0]])
    c=np.array([x,y])-left*3.9
    path=np.array([c-tangent*4.6875,c+tangent*4.6875])
    r=compact_ring_tile(D,path,top,bottom_z=-1.6,seed=seed,name=f'ROCK_BASALT_STACK_V3_{seed}')
    ob=r['object'];UV_STATS[ob.name]=author_uv(ob.data,random.Random(seed+100),uf=.7,vf=.32,p_glow=.3)
    # Preserve world geometry while giving a real stack its design-centre origin.
    for v in ob.data.vertices:v.co.x-=x;v.co.y-=y
    ob.location=(x,y,0.);ob.data.update()
    return dict(obs=[ob],main=ob,nat_h=top,top=top,scale0=1.,sat_scale0=[],design=s,seed=seed)


def build_tee_platform(D,pad):
    """Closed stone body under the exact frozen grass square; real interior piers."""
    hull=pad_outline(pad);path=inset_polygon(hull,.75);closed=np.vstack([path,path[:1]])
    seg=np.diff(closed,axis=0);lens=np.linalg.norm(seg,axis=1);arc=np.r_[0.,np.cumsum(lens)]
    total=float(arc[-1]);count=round(total/1.2);rng=random.Random(10245)
    mb=PL._MB(('LK_BASALT',));columns=[];z=max(v.co.z for v in pad.data.vertices)+.0115
    for k in range(count):
        sc=total*(k+.5)/count;j=min(len(seg)-1,int(np.searchsorted(arc,sc,side='right')-1))
        t=(sc-arc[j])/lens[j];p=path[j]+seg[j]*t;tan=seg[j]/lens[j]
        width=rng.uniform(1.13,1.25);ang=math.atan2(tan[1],tan[0])+math.pi/6+rng.uniform(-.1,.1)
        n=6 if k%4==0 else 5
        xy=np.array([p+.5*width*np.array([math.cos(ang+math.tau*i/n),math.sin(ang+math.tau*i/n)]) for i in range(n)])
        vv,ff,spec=_closed_cut_column(xy,-1.6,z,rng,cuts=1);vi,fi=len(mb.V),len(mb.F)
        mb.V.extend(tuple(v) for v in vv)
        for f in ff:mb.f(tuple(vi+i for i in f))
        spec.update(verts=[vi,len(mb.V)],faces=[fi,len(mb.F)]);columns.append(spec)
    for gx in (-3.,-1.,1.,3.):
        for gy in (-2.1,0.,2.1):
            p=np.array([gx,gy]);width=rng.uniform(.95,1.3);ang=rng.uniform(-.2,.2);n=6 if rng.random()<.25 else 5
            xy=np.array([p+.5*width*np.array([math.cos(ang+math.tau*i/n),math.sin(ang+math.tau*i/n)]) for i in range(n)])
            vv,ff,spec=_closed_cut_column(xy,-1.6,z-.07,rng,cuts=1);vi,fi=len(mb.V),len(mb.F)
            mb.V.extend(tuple(v) for v in vv)
            for f in ff:mb.f(tuple(vi+i for i in f))
            spec.update(verts=[vi,len(mb.V)],faces=[fi,len(mb.F)]);columns.append(spec)
    me=PL._finalize('DRESS_PADRIM_V3',mb,'box',smooth_angle=None,library=False)
    ob=bpy.data.objects.new('DRESS_PADRIM_V3',me);PL._collection_for('DRESS_').objects.link(ob);PL._parent(D,ob)
    UV_STATS[ob.name]=author_uv(me,random.Random(10246),uf=.7,vf=.32,p_glow=.3)
    ob['lk_v3_columns']=json.dumps(columns);ob['lk_v3_world_sized']=True
    return [ob],dict(rows=count,total_m=total,slabs=len(columns),faces=len(mb.F),w_min=min(c['width'] for c in columns),w_max=max(c['width'] for c in columns),w_mean=float(np.mean([c['width'] for c in columns])),win_lum_mean=float(texture_measure()['zone_lum_mean']),win_lum_max=float(texture_measure()['zone_lum_max']),zones=list(range(len(ZONES))),du=.7/TILE,z_lo=z,z_hi=z)
'''
# Reduce only redundant far-field crust, retaining whole spatial cell groups.
s=s.replace('    left = list(plan)\n','''    groups={}
    for c in plan:groups.setdefault((int(c[0]//CRUST_CELL_M),int(c[1]//CRUST_CELL_M)),[]).append(c)
    keys=list(groups);random.Random(1069).shuffle(keys)
    selected=[]
    for key in keys:
        if len(selected)>=1000:break
        selected.extend(groups[key])
    left=list(selected)
''',1)
lp.write_text(s)
b=bp.read_text();start=b.index('def make_stack(');end=b.index('\n\ndef refit_stack',start)
b=b[:start]+'''def make_stack(D,s,top,rnd):
    return HL.make_lava_stack(D,s,top,101100+int(s['x']*13+s['d']*7))
'''+b[end:]
b=b.replace('rounds, sight_left = clear_sightlines(D, stacks + mesas)','''# World-sized columns are rebuilt lower if they obstruct play, never stretched.
blocked,_ = blocked_lines(D,stacks+mesas)
rounds=0
for st_ in list(blocked):
    if st_.get('kind')=='crust':continue
    idx=stacks.index(st_);old=st_['main'];old_name=old.name
    D.objects.pop(old_name,None);bpy.data.objects.remove(old,do_unlink=True)
    D.look_objects=[n for n in D.look_objects if n!=old_name]
    HL.UV_STATS.pop(old_name,None)
    stacks[idx]=HL.make_lava_stack(D,st_['design'],6.5,st_['seed']);rounds+=1
_,sight_left=blocked_lines(D,stacks+mesas)''')
start=b.index('stack_foot = [');end=b.index('\nfoot = ',start)
b=b[:start]+'''stack_foot = [(o.location.x,o.location.y,.5*math.hypot(footprint(o)[2]-footprint(o)[0],footprint(o)[3]-footprint(o)[1])+3.) for st in stacks for o in st['obs']]'''+b[end:]
b=b.replace('tri_budget=FR_BUDGET','tri_budget=33000',1)
b=b.replace('basalt_width_m=(1.4, 2.4)','basalt_width_m=(0.85, 1.55)')
b=b.replace('FW_TILE = L.LOOK["LK_FAIRWAY"][2]','''bpy.data.objects['FAIRWAY_FIRSTCUT'].data.materials[0]=L.look_material('LK_ROUGH',D)
FW_TILE = L.LOOK['LK_ROUGH'][2]''')
b=b.replace('else "plants"\nassert RIM_MODE','else "basalt"\nassert RIM_MODE')
b=b.replace('rim, RIM_STATS = HL.build_tee_rim(D, L, _tee, seed=RIM_SEED, **RIM_SPEC)','''if RIM_MODE=='basalt':rim,RIM_STATS=HL.build_tee_platform(D,_tee)
else:rim,RIM_STATS=HL.build_tee_rim(D,L,_tee,seed=RIM_SEED,**RIM_SPEC)''')
# Three physical smoke groups instead of five independent plumes.
start=b.index('smoke = []');end=b.index('\n# ---- 6.',start)
b=b[:start]+'''smoke = []
smoke += HL.smoke_group(D,TEE_CAM,(96.0,390.0,-5.0),(90.0,120.0),3,seed=5,spread=.30)
smoke += HL.smoke_group(D,APP_CAM,(305.0,118.0,0.0),(90.0,90.0),3,seed=2)
smoke += HL.smoke_group(D,RIM_CAM,(150.0,435.0,95.0),(130.0,120.0),3,seed=4)
'''+b[end:]
# Unverified checkpoint before any expensive audits; all gate predicates unchanged.
needle='# ---- 7. gates of the build itself'
b=b.replace(needle,'''os.makedirs(os.path.join(os.path.dirname(D.out_dir),'checkpoints'),exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(D.out_dir),'checkpoints','p4_unverified.blend'),relative_remap=False)
'''+needle)
b=b.replace('L.export_look_fbx(D)\nfails', '''L.export_look_fbx(D)
import json
with open(os.path.join(D.out_dir,'build_gates.json'),'w') as f_:json.dump([dict(name=n,ok=ok,detail=de) for n,ok,de in GATES],f_,indent=2)
with open(os.path.join(D.out_dir,'build_inventory.json'),'w') as f_:json.dump(dict(stats=st,near=len(near),far=len(ring),crust_chunks=len(crust),crust_kept=crust_kept,fringe={k:v for k,v in fringe.items() if k!='objs'},rim_stats=RIM_STATS,smoke_groups=3,smoke_cards=len(smoke)),f_,indent=2,default=lambda x:float(x) if isinstance(x,np.generic) else str(x))
fails''')
bp.write_text(b)
