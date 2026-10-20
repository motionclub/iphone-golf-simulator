"""Evaluate the binary FEMALE_TORSO_FORM2 gates from the measured JSON files -> checks.json (+ GATE lines printed).
Thresholds are anchored to plate measurements (documented in FEMALE_TORSO_FORM2_RESULTS.md); line definitions are this chat's."""
import sys,json; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from torso2 import *
import seam
from footprint import grid_surface
ck=json.load(open(WD/'export/form2_checks.json')); g7=json.load(open(WD/'export/form2_gate_scripts_checks.json')); fm=json.load(open(WD/'export/form2_feature_metrics.json'))
co=np.load(WD/'data/co_FORM2_final.npy'); cand=np.load(WD/'data/cand_co.npy')
P={**DEFAULT2,**json.load(open(WD/'export/form2_params.json'))}
lines=[]
def L(group,name,value,cond,limit,basis):
    lines.append(dict(group=group,line=name,value=value,limit=limit,result='PASS' if cond else 'FAIL',basis=basis))
topo=ck['topology']
L('ZONE_OUTSIDE','moved outside zone vs chat-7 candidate',ck['moved_outside_zone_vs_chat7_candidate'],ck['moved_outside_zone_vs_chat7_candidate']==0,'== 0','float32 exact, audit/form2.npz vs audit/cand_start.npz')
L('ZONE_OUTSIDE','moved outside zone vs ORIGINAL start 200dc3b9',ck['moved_outside_zone_vs_original_start'],ck['moved_outside_zone_vs_original_start']==0,'== 0','float32 exact')
L('ZONE_OUTSIDE','zone border vertices moved (seam with arms/neck/legs)',ck['border_vertices_moved_vs_original'],ck['border_vertices_moved_vs_original']==0,'== 0','238 border vertices pinned bit-exact')
tp=all(v for k,v in topo.items() if isinstance(v,bool))
L('TOPOLOGY','poly/loop/edge/material/smooth/UV/custom-normal raw codes/Hair/other objects identical',tp,tp,'all True','audit dumps')
L('TOPOLOGY','triangles (budget 35-50k)',topo['tris_candidate_vs_new'][1],topo['tris_candidate_vs_new'][1]==topo['tris_candidate_vs_new'][0] and topo['tris_candidate_vs_new'][1]<=50000,'unchanged, <=50k','')
L('TOPOLOGY','flipped zone triangles vs original',ck['flipped_zone_tris_vs_original'],ck['flipped_zone_tris_vs_original']==0,'== 0','face-normal dot < 0')
L('TOPOLOGY','zone triangles turned >60 deg vs original',ck['zone_tris_turned_gt60deg'],ck['zone_tris_turned_gt60deg']<=2,'<= 2','chat-7 value 0')
sx=g7['side_profile_torso_band_xor_z0.82_1.30']['after']
L('SIDE_SIL','side-profile torso-band XOR vs plate (chat-7 gate script, z .82-1.30)',round(sx,4),sx<=0.05,'<= 0.05','metrics_side.py gradient-edge contour of L+R profile panels')
fb=g7['torso_visible_edge_run_xor_rows_z0.82_1.165']['after']
L('SIDE_SIL','front torso visible-edge XOR vs bald plate (rows z .82-1.165)',round(fb['front'],4),fb['front']<=0.05,'<= 0.05','metrics_fb.py')
L('SIDE_SIL','back torso visible-edge XOR vs bald plate',round(fb['back'],4),fb['back']<=0.05,'<= 0.05','metrics_fb.py')
bs=ck['border_steps_mm']
L('SEAM_CLEAN','displacement step at a pinned border edge, legs (mm)',round(bs['legs']['max_mm'],2),bs['legs']['max_mm']<=8.0,'<= 8','|d(v)-d(border)| over one edge (~12 mm)')
L('SEAM_CLEAN','... arm junction (mm)',round(bs['arm']['max_mm'],2),bs['arm']['max_mm']<=10.0,'<= 10','chat 7 / first form2 version had 17 mm')
L('SEAM_CLEAN','... neck/shoulder top (mm)',round(bs['top']['max_mm'],2),bs['top']['max_mm']<=1.0,'<= 1','')
dh=ck['dihedral']
L('SEAM_CLEAN','zone edges with dihedral >40 deg (count)',dh['form2']['n_gt40'],dh['form2']['n_gt40']<=dh['original']['n_gt40'],f"<= original ({dh['original']['n_gt40']})",'inherited mesh creases are not increased')
L('SEAM_CLEAN','worst zone dihedral (deg)',round(dh['form2']['max_deg'],1),dh['form2']['max_deg']<=dh['original']['max_deg']+0.5,f"<= original ({dh['original']['max_deg']:.1f})",'')
rg=ck['bi_laplacian_roughness_mm_zone_interior']
L('SEAM_CLEAN','bi-Laplacian roughness mean (mm), zone interior',round(rg['form2']['mean'],3),rg['form2']['mean']<=rg['chat7_candidate']['mean']+1e-9,f"<= chat 7 ({rg['chat7_candidate']['mean']:.3f})",'')
L('SEAM_CLEAN','bi-Laplacian roughness p95 (mm)',round(rg['form2']['p95'],3),rg['form2']['p95']<=rg['chat7_candidate']['p95']+1e-9,f"<= chat 7 ({rg['chat7_candidate']['p95']:.3f})",'')
b=fm['bust']; gl=fm['glute']
envF=plate_front(1.21); 
L('BUST_VOLUME','mound apex envelope vs plate side profile (mm)',round(1000*(b['apex_envelope_front_m']-plate_front(0.5*(b['L']['apex_z']+b['R']['apex_z']))),1),abs(1000*(b['apex_envelope_front_m']-plate_front(0.5*(b['L']['apex_z']+b['R']['apex_z']))))<=4.0,'|err| <= 4','plate front table at apex z')
L('BUST_VOLUME','sternal valley: apex front vs sternum strip (mm)',round(b['sternal_valley_mm'],1),8<=b['sternal_valley_mm']<=20,'8..20','separation between the two mounds')
wd=1000*(0.5*(b['L']['footprint_x_range_abs'][1]-b['L']['footprint_x_range_abs'][0]+b['R']['footprint_x_range_abs'][1]-b['R']['footprint_x_range_abs'][0])); hh=1000*(b['L']['footprint_z_range'][1]-b['L']['footprint_z_range'][0])
L('BUST_VOLUME','mound footprint width (mm)',round(wd,0),70<=wd<=110,'70..110','plate mound ~80-100 mm wide (band-pass highlight/crescent)')
L('BUST_VOLUME','mound footprint height (mm)',round(hh,0),100<=hh<=130,'100..130','plate: crescent z1.18 to blend z~1.30')
L('BUST_VOLUME','underbust edge: footprint lower z',round(b['L']['footprint_z_range'][0],3),1.17<=b['L']['footprint_z_range'][0]<=1.20,'1.17..1.20','plate dark crescent z 1.18-1.19')
hgt=0.5*(b['L']['height_above_wall_mm']+b['R']['height_above_wall_mm'])
L('BUST_VOLUME','mound height above the local chest wall at the apex (mm)',round(hgt,1),hgt>=15,'>= 15','soft but real mounds (not a flat pancake)')
cx=0.5*(0.5*(b['L']['footprint_x_range_abs'][0]+b['L']['footprint_x_range_abs'][1])+0.5*(b['R']['footprint_x_range_abs'][0]+b['R']['footprint_x_range_abs'][1]))
L('BUST_VOLUME','mound footprint centre |x| (m)',round(cx,3),0.060<=cx<=0.090,'0.060..0.090','plate mounds centred x ~ +-0.07..0.085')
ga=gl; apx=0.5*(abs(ga['L']['apex_x'])+abs(ga['R']['apex_x']))
L('GLUTE_FORM','two lobes: apex |x| (m)',round(apx,3),0.060<=apx<=0.090,'0.060..0.090','plate lobe centres ~ +-0.07..0.085')
L('GLUTE_FORM','lobe apex z (m)',round(ga['L']['apex_z'],3),0.85<=ga['L']['apex_z']<=0.89,'0.85..0.89','plate glute apex z~0.86')
ea=1000*(ga['L']['apex_y']-plate_back(ga['L']['apex_z']))
L('GLUTE_FORM','lobe apex depth vs plate side profile (mm)',round(ea,1),abs(ea)<=4.0,'|err| <= 4','plate back table')
cl={r['z']:r['cleft_depth_mm'] for r in ga['cleft']}
dmid=[cl[0.86],cl[0.88],cl[0.90]]
L('GLUTE_FORM','cleft depth at z .86/.88/.90 (mm)',[round(v,1) for v in dmid],all(18<=v<=32 for v in dmid),'18..32','readable cleft, plate faint line deepening toward the crotch')
zs=sorted(cl); start=None
for z0,z1 in zip(zs[::-1][1:],zs[::-1][:-1]):
    pass
import numpy as _np
zz=_np.array(sorted(cl)); dd=_np.array([cl[z] for z in zz]); start=float(_np.interp(5.0,dd[::-1],zz[::-1])) if (dd>=5).any() else 0.0
L('GLUTE_FORM','cleft start z (depth reaches 5 mm)',round(start,3),0.93<=start<=0.965,'0.93..0.965','plate cleft begins ~0.945')
L('GLUTE_FORM','cleft depth at z .98 (mm) - no slit in the lumbar',round(cl[0.98],1),cl[0.98]<=3.0,'<= 3','')
sh=ga['shelf_rise_1.00_to_0.94_mm']; shp=1000*(plate_back(0.94)-plate_back(1.0))
L('GLUTE_FORM','upper shelf rise z1.00->0.94 (mm) vs plate table',round(sh,1),abs(sh-shp)<=8.0,f'plate {shp:.1f} +- 8','')
rc=0.5*(ga['L']['curv_radius_cm']+ga['R']['curv_radius_cm'])
L('GLUTE_FORM','lobe horizontal curvature radius at the apex (cm)',round(rc,1),5.0<=rc<=11.0,'5..11','round cheeks (not flat pads)')
# underbutt rise at |x|=0.07 between z=0.806 and 0.852
xs=np.arange(-0.19,0.1901,0.002); zs2=np.arange(0.78,1.06,0.002); ba=grid_surface(co,'back',xs,zs2)
iz=lambda z:int(round((z-0.78)/0.002)); ix=lambda x:int(round((x+0.19)/0.002))
rise=1000*np.mean([ba[iz(0.852),ix(sx_)]-ba[iz(0.808),ix(sx_)] for sx_ in (-0.07,0.07)])
L('GLUTE_FORM','underbutt fold: back surface rise z .808 -> .852 at |x|=.07 (mm)',round(rise,1),rise>=15.0,'>= 15','lobe lower flank rising off the fixed leg-top ring (fold limited by the zone floor)')
# upper rim crease: dihedral in the glute upper-rim region
a0=seam.dihedral(CO0); a1=seam.dihedral(co); mid=0.5*(co[seam.PAIR_E[:,0]]+co[seam.PAIR_E[:,1]])
rim=seam.ZPAIR&(mid[:,2]>=0.92)&(mid[:,2]<=1.0)&(np.abs(mid[:,0])<0.15)&(mid[:,1]>0)
L('GLUTE_FORM','no hard rim: worst dihedral at the lobe upper rim z .92-1.0 (deg)',round(float(a1[rim].max()),1),a1[rim].max()<=30.0,'<= 30','')
L('GLUTE_FORM','no hard rim: worst dihedral INCREASE vs original there (deg)',round(float((a1-a0)[rim].max()),1),(a1-a0)[rim].max()<=25.0,'<= 25','')
res={'gate':'FEMALE_TORSO_FORM2','lines':lines}
groups={}
for l in lines: groups.setdefault(l['group'],[]).append(l['result']=='PASS')
res['group_results']={k:('PASS' if all(v) else 'FAIL') for k,v in groups.items()}
res['overall']='PASS' if all(r=='PASS' for r in res['group_results'].values()) else 'FAIL'
res['failed_lines']=[l for l in lines if l['result']!='PASS']
res['not_automated']=['visual form match vs plate (Adnan eye): proof/04, proof/05, proof/01','mirror-stripe smoothness: proof/06 (visual)','integration with limbs+arms: proof/08, proof/09 (visual)']
json.dump(res,open(WD/'checks.json','w'),indent=1)
for l in lines: print(f"{l['group']:13s} {l['result']}  {l['line']}: {l['value']}  (limit {l['limit']})")
print('GROUPS',res['group_results'],'OVERALL',res['overall'])
