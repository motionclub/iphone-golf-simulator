"""Correct actual UV counters only; prior frames and pixel failures retained."""
import os,sys,json
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import bpy,numpy as np
import hole10_look as H
import golf_look_textures as T
HERE=os.path.dirname(__file__);OUT=HERE+'/bounded_v6/fixture'
bpy.ops.wm.open_mainfile(filepath=OUT+'/fixture.blend')
E=T.read_png(HERE+'/bounded_v6/Basalt_E.png')[:,:,:3]/255
rng=np.random.default_rng(1010);r=rng.random((96,2));q=np.sqrt(r[:,0])
H._UV_GLOW_CACHE.update(G=np.flipud(E.max(2)>.2),w=E.shape[1],h=E.shape[0],bary=np.c_[1-q,q*(1-r[:,1]),q*r[:,1]])
stats=[]
for ob in sorted((o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('ROCK_WALL_P7_')),key=lambda o:o.name):
 st=dict(side=0,glow=0,top=0,top_glow_free=0)
 for p in ob.data.polygons:
  pts=np.array([tuple(ob.data.vertices[i].co) for i in p.vertices]);uv=np.array([tuple(ob.data.uv_layers.active.data[i].uv) for i in p.loop_indices]);share=H._face_glow(uv)
  if abs(H._newell(pts)[2])>=.8:st['top']+=1;st['top_glow_free']+=int(share<=2e-4)
  else:st['side']+=1;st['glow']+=int(share>0)
 stats.append(st)
result=json.load(open(OUT+'/result.json'));result['uv_stats']=stats
result['uv_counter_correction']='Previous scratch counters compared decoded uint8 values to .2; corrected to decoded0..1 as original predicate. UV coordinates and rendered frames did not change. Erroneous counters preserved in result_attempt1_uint8_uv_counter.json.'
json.dump(result,open(OUT+'/result.json','w'),indent=2)
print(json.dumps(stats,indent=2))
