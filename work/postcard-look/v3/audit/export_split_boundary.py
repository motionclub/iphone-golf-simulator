import os,sys,json,hashlib,types
import bpy,numpy as np
sys.dont_write_bytecode=True
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'));sys.path.insert(0,os.path.join(repo,'blender/scripts'))
import postcard_look_lib as L
import hole09_design as des
YD=.9144
path=os.path.join(repo,'work/postcard-look/baseline/blender/hole_09.blend')
bpy.ops.wm.open_mainfile(filepath=path,load_ui=False)
ob=bpy.data.objects['TERRAIN_SPLIT'];D=types.SimpleNamespace(play_z=des.PLAY_Z,terrain=ob,terrain_name=ob.name)
loops=L.terrain_top_loops(D,ob)
A=np.array(des.SHORE,float);B=np.roll(A,-1,axis=0);d=B-A;den=np.maximum((d*d).sum(1),1e-12)
label_group={'ridge_west_shore':'ridge','channel_wall_ridge':'ridge','ribbon_east_north':'fairway','ribbon_east_south':'fairway','channel_wall_ribbon_north':'fairway','channel_wall_ribbon_south':'fairway','gap_north_end':'fairway','gap_south_end':'fairway','north_shore':'joins','south_shore':'joins','channel_tip_north':'joins','channel_tip_south':'joins'}
def edges(P):
 out=[]
 for i,(a,b) in enumerate(zip(P,np.roll(P,-1,axis=0))):
  q=(a+b)/2;t=np.clip(((q-A)*d).sum(1)/den,0,1);dist=((A+t[:,None]*d-q)**2).sum(1);near=int(dist.argmin());lab=des.SHORE_LABELS[near]
  out.append({'index':i,'next':(i+1)%len(P),'nearest_design_directed_edge':near,'label':lab,'group':label_group[lab]})
 return out
recs=[]
for P,indices in loops:
 points=P.tolist();canonical=json.dumps(points,separators=(',',':')).encode()
 recs.append({'points_blender_xy_m':points,'points_unity_world_xz_yd':(P/YD).tolist(),'terrain_vertex_indices':indices.tolist(),'points_sha256':hashlib.sha256(canonical).hexdigest(),'directed_edges':edges(P/YD),'signed_area_m2':float(L.P.signed_area(P))})
source=des.__file__
result={'hole':9,'note':'One connected C-shaped outer boundary; no independent two-island polygons or virtual closure edges. Arc groups preserve all actual directed shore edges; joins reported separately.','source_design':os.path.relpath(source,repo),'source_design_sha256':hashlib.sha256(open(source,'rb').read()).hexdigest(),'baseline_blend':os.path.relpath(path,repo),'baseline_blend_sha256':hashlib.sha256(open(path,'rb').read()).hexdigest(),'baseline_mesh':'TERRAIN_SPLIT','coordinate_mapping':'Blender (x_m,y_m,z_m) -> HoleView world (x_m/0.9144,z_m/0.9144,y_m/0.9144); model water origin y=0 after marker alignment. Design (x,d) already course yards.','play_top_world_y_yd':des.PLAY_Z/YD,'sea_base_world_y_yd':0.0,'design_shore_points_yd':des.SHORE,'design_shore_labels':des.SHORE_LABELS,'semantic_stretches':des.SCENERY['shore_stretches'],'design_directed_edges':[{'index':i,'next':(i+1)%len(des.SHORE),'label':lab,'group':label_group[lab]} for i,lab in enumerate(des.SHORE_LABELS)],'actual_baseline_top_loops':recs}
out=os.path.join(os.path.dirname(__file__),'split_frozen_boundary.json');json.dump(result,open(out,'w'),indent=2);print('Saved',out,'design points',len(A),'actual loops',len(loops),'loop vertices',[len(P) for P,_ in loops])
