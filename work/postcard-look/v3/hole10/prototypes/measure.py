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
from compact_columns import compact_column_band
OUT=os.path.join(os.path.dirname(__file__),'attempt2');os.makedirs(OUT,exist_ok=True)
cases=[dict(name='band6m_rows3',length=6.,rows=3,height=5.5,bottom=0.,width=(.8,1.5),seed=4),
       dict(name='near10m_rows4_top15',length=10.,rows=4,height=15.2,bottom=-1.6,width=(1.4,1.78),seed=11),
       dict(name='near6m_rows7_top25',length=6.5,rows=7,height=25.2,bottom=-1.6,width=(1.3,1.78),seed=23)]
results=[]
for ci,case in enumerate(cases):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PL._COUNTERS.clear();PL.reset_scatter(None)
    folder=OUT+'/'+case['name'];os.makedirs(folder,exist_ok=True)
    D=P.start('hole10_design',out_dir=folder)
    ln=case['length'];h=case['height']
    try:
        result=compact_column_band(D,[(0.,0.),(ln*.5,.15),(ln,0.)],
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
             horizontal_span=result['horizontal_span'],columns=result['columns'])
    with open(folder+'/measurements.json','w') as f:json.dump(row,f,indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=folder+'/fixture.blend',relative_remap=False)
    for g,ok in gates.items():print(f"GATE: {case['name']}:{g} {'PASS' if ok else 'FAIL'}",flush=True)
    print(json.dumps({k:v for k,v in row.items() if k!='columns'}),flush=True)
    results.append(row)
with open(OUT+'/results.json','w') as f:json.dump(results,f,indent=2)
sys.exit(0 if all(r['pass_'] for r in results) else 1)
