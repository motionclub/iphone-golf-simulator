"""Strict unchanged geometry gates for the scratch compact column adapter."""
import os,sys,json,types
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
sys.path.insert(0,os.path.dirname(__file__))
import bpy,numpy as np
from mathutils import Vector
import postcard_lib as P
import postcard_props_lib as PL
import postcard_look_verify as V
from compact_columns import compact_ring_tile
OUT=os.path.join(os.path.dirname(__file__),'attempt5');os.makedirs(OUT,exist_ok=True)
cases=[dict(name='near14m_3row_seed11',length=9.375,rows=3,height=14.2,bottom=-1.6,width=(1.68,1.78),seed=11),
       dict(name='near18m_3row_seed23',length=9.375,rows=3,height=18.2,bottom=-1.6,width=(1.68,1.78),seed=23),
       dict(name='far26m_3row_seed4',length=9.375,rows=3,height=26.2,bottom=-1.6,width=(1.68,1.78),seed=4),
       dict(name='far30m_worldarc_seed38',length=9.375,rows=3,height=30.2,bottom=-1.6,width=(1.68,1.78),seed=38,arc=True)]
results=[]
for ci,case in enumerate(cases):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear();PL.reset_scatter(None)
    folder=OUT+'/'+case['name'];os.makedirs(folder,exist_ok=True)
    D=P.start('hole10_design',out_dir=folder)
    ln=case['length'];h=case['height']
    path=[(0.,0.),(ln*.5,.15),(ln,0.)]
    if case.get('arc'):
        angles=np.linspace(.4,.4+ln/300,3)
        path=[(300+300*np.cos(t),-100+300*np.sin(t)) for t in angles]
    try:
        result=compact_ring_tile(D,path,
                               [h-.35,h+.35,h-.2],bottom_z=case['bottom'],
                               rows=case['rows'],width_m=case['width'],seed=case['seed'])
    except Exception as exc:
        row=dict(case=case,gates={'CONSTRUCTION':False},pass_=False,error=str(exc))
        results.append(row)
        with open(folder+'/measurements.json','w') as f:json.dump(row,f,indent=2)
        print(f"GATE: {case['name']}:CONSTRUCTION FAIL: {exc}",flush=True)
        continue
    ob=result['object'];S=V.Snap('blend',types.SimpleNamespace(tag='10'))
    shape=V.rock_shape(S.loc(ob));verts,tris=S.oriented(ob)
    columns,side=V.count_columns(verts,tris)
    widths=[s['width'] for s in result['columns']]
    gates=dict(CONSTRUCTION=True,NEAR_TOP=all(12<=s['top']<=60 for s in result['columns']),ROCK_SHAPE=shape['ok'],PCA=shape['r3']>=V.ROCK_TH['stretch_r3_min'],
               CAP_COLUMNS=columns>=V.TH['columns'] and side>=.45,
               FACES=len(ob.data.polygons)<=490,
               WORLD_WIDTH=all(.6<=w<=1.8 for w in widths),
               SIDES=all(s['sides'] in (5,6) for s in result['columns']),
               WORLD_SPAN=result['horizontal_span']<=20.)
    row=dict(case=case,gates=gates,pass_=all(gates.values()),shape=shape,
             cap_columns=columns,actual_shafts=len(widths),side_area_fraction=side,
             polygons=len(ob.data.polygons),triangles=len(tris),
             width_min=min(widths),width_max=max(widths),
             horizontal_span=result['horizontal_span'],path_length=result['path_length'],triangles_per_m=result['triangle_projection_per_m'],projected_3200m_wall_triangles=result['triangle_projection_per_m']*3200,columns=result['columns'])
    with open(folder+'/measurements.json','w') as f:json.dump(row,f,indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=folder+'/fixture.blend',relative_remap=False)
    for g,ok in gates.items():print(f"GATE: {case['name']}:{g} {'PASS' if ok else 'FAIL'}",flush=True)
    print(json.dumps({k:v for k,v in row.items() if k!='columns'}),flush=True)
    results.append(row)
with open(OUT+'/results.json','w') as f:json.dump(results,f,indent=2)
sys.exit(0 if all(r['pass_'] for r in results) else 1)
