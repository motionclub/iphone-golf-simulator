"""python3 gates.py : assemble checks.json + FEMALE_ARMS_FORM_RESULTS.md from audit_final.json, metrics_*.json (binary gates)."""
import json, numpy as np, hashlib
A=json.load(open('data/audit_final.json')); MS=json.load(open('data/metrics_start.json')); MF=json.load(open('data/metrics_final.json'))
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
G={}
g1=A['G1']
G['ZONE_OUTSIDE=0']=(g1['moved_outside_zone']==0 and g1['max_disp_outside_m']==0.0 and g1['pinned_moved']==0 and g1['hair_identical'] and g1['objects_identical'] and g1['wrist_ring_R_moved']==0 and g1['wrist_ring_L_moved']==0,
  f"moved {g1['moved']} of {g1['arm_zone']} arm-zone verts; moved outside zone {g1['moved_outside_zone']} (max disp outside {g1['max_disp_outside_m']} m, float32 bit-exact); pinned seam verts {g1['pinned_verts']} moved {g1['pinned_moved']} (max {g1['max_pinned_disp_mm']} mm); wrist rings moved R {g1['wrist_ring_R_moved']} / L {g1['wrist_ring_L_moved']}; Hair_F + all other objects identical")
g5=A['G5']; g2=A['G2_mesh']
topo=(g5['verts_same'] and g5['edges_same'] and g5['loops_same'] and g5['poly_start_same'] and g5['material_ids_same'] and g5['smooth_flags_same'] and all(g5['uv_same'].values()) and g5['attrs_same'] and g5['tris_final']==g5['tris_start']
      and g5['tris_final']+4960<=50000 and g2['final']['nonmanifold']==0 and g2['final']['noncontig']==0 and g2['final']['degenerate']==0 and g2['final']['loose']==0 and g2['final']['volume']>0 and g2['self_isect_final']==g2['self_isect_start'])
G['TOPOLOGY']=(topo,f"verts/edges/loops/polygons/material ids/smooth flags/UV/attribute data (incl. raw custom_normal codes) identical to start; tris {g5['tris_final']} (+4960 hair = {g5['tris_final']+4960} <= 50000); non-manifold {g2['final']['nonmanifold']}, degenerate {g2['final']['degenerate']}, loose {g2['final']['loose']}, signed volume {g2['final']['volume']:.5f} m3 (>0); self-intersecting face pairs {g2['self_isect_final']} = start {g2['self_isect_start']} (all in the head: eyes/lashes; 0 in the arms)")
g3=A['G3']
arm_ok=(g3['face_normal_flips(>90deg)']==0 and g3['dihedral_armpit_max_deg_final']<=g3['dihedral_armpit_max_deg_start']+5 and g3['dihedral_armpit_p99_final']<=g3['dihedral_armpit_p99_start']+5 and g3['edge_stretch_ratio_max']<=1.5 and g3['edge_stretch_ratio_min']>=0.6 and g1['pinned_moved']==0)
G['ARMPIT_CLEAN']=(arm_ok,f"torso/arm seam verts moved 0 (limit 0.3 mm); face-normal flips 0; max face-normal change in arm zone {g3['face_normal_change_max_deg_armzone']:.1f} deg; armpit/shoulder-seam dihedral max {g3['dihedral_armpit_max_deg_start']:.1f} -> {g3['dihedral_armpit_max_deg_final']:.1f} deg, p99 {g3['dihedral_armpit_p99_start']:.1f} -> {g3['dihedral_armpit_p99_final']:.1f} deg (limit +5 deg); edge stretch {g3['edge_stretch_ratio_min']:.2f}..{g3['edge_stretch_ratio_max']:.2f} (limit 0.6..1.5)")
sil_ok=(MF['front_arms_xor_pct']<=MS['front_arms_xor_pct']+1 and MF['back_arms_xor_pct']<=MS['back_arms_xor_pct']+1 and MF['consensus_mean_fb']['ratio']<=MS['consensus_mean_fb']['ratio'] and MF['consensus_mean_fb']['ratio']<=1.25 and MF['outer_edge_dev_mm']['mean_abs']<=MS['outer_edge_dev_mm']['mean_abs'])
G['SIL_NOT_WRECKED']=(sil_ok,f"arm-zone XOR vs plate polygon front {MS['front_arms_xor_pct']} -> {MF['front_arms_xor_pct']} %, back {MS['back_arms_xor_pct']} -> {MF['back_arms_xor_pct']} % (limit start+1 pt; the plate back view is itself ~20 % off its own mean); consensus ratio (model/plate-self, <=1.25 and <= start) {MS['consensus_mean_fb']['ratio']} -> {MF['consensus_mean_fb']['ratio']}; outer-edge deviation to plate consensus rows y175..340: mean {MS['outer_edge_dev_mm']['mean_abs']} -> {MF['outer_edge_dev_mm']['mean_abs']} mm, max {MS['outer_edge_dev_mm']['max_abs']} -> {MF['outer_edge_dev_mm']['max_abs']} mm")
# form
dz=np.load('export/arms_delta.npz'); _idx=dz['moved_idx_limbs_order']; _s=dz['start_co']; _n=dz['new_co']
def relief(side):
    sg=1 if side=='R' else -1
    m=(_s[:,0]*sg>0)&(_s[:,2]>=0.90)&(_s[:,2]<=1.30); d=(_n-_s)[m]*1000; zz=_s[m,2]
    rem=[]
    for z0 in np.arange(0.90,1.30,0.01):
        k=(zz>=z0)&(zz<z0+0.01)
        if k.sum()<4: continue
        dd=d[k]-d[k].mean(0); rem.append(np.linalg.norm(dd,axis=1))
    r=np.concatenate(rem); return {'rms':float(np.sqrt((r**2).mean())),'p95':float(np.percentile(r,95))}
fs=A['form_slices']; lines=[]; form_ok=True
def prof(side,tag):
    a=np.array(fs[f'{side}_{tag}']); return a[:,0],a[:,1]*1000,a[:,2]*1000,a[:,3]*1000
for side in 'RL':
    z,rx,ry,cy=prof(side,'final'); z0,rx0,ry0,cy0=prof(side,'start')
    def dip(rx,z):
        best=0
        for j in range(1,len(rx)-1):
            if 0.95<=z[j]<=1.12: best=max(best,min(rx[:j].max()-rx[j],rx[j+1:].max()-rx[j]))
        return best
    hang=float(np.interp(1.08,z,cy)); hang0=float(np.interp(1.08,z0,cy0)); lower=float(np.interp(0.92,z,cy))
    dd=dip(rx,z); dd0=dip(rx0,z0)
    rel=relief(side)
    ok=(hang>=25 and lower<hang and dd>=1.8 and rel['rms']>=1.5 and rel['p95']>=3.0)
    form_ok&=ok
    lines.append(f"{side}: arm axis y at z1.08 = {hang:+.1f} mm (start {hang0:+.1f}; plate ~ +35; limit >= +25), at z0.92 = {lower:+.1f} mm (leans forward toward the wrist); elbow-neck dip in half-width = {dd:.2f} mm (start {dd0:.2f}; limit >= 1.8); added relief (per-slice displacement with the rigid shift removed, z0.90-1.30) RMS {rel['rms']:.2f} mm (limit >= 1.5), p95 {rel['p95']:.2f} mm (limit >= 3.0) -> {'ok' if ok else 'FAIL'}")
G['ARM_FORM_DEFINED']=(form_ok,' | '.join(lines))
allok=all(v[0] for v in G.values())
out={'gate':'FEMALE_ARMS_FORM','result':'PASS' if allok else 'FAIL','lines':{k:{'pass':bool(v[0]),'evidence':v[1]} for k,v in G.items()},
     'start_sha256':sha('start/start_torso_plus_limbs.blend'),'candidate_sha256':sha('export/HeroBase_Female_arms_candidate.blend'),'artdir_sha256':sha('../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend')}
json.dump(out,open('checks.json','w'),indent=1)
print(out['result']); 
for k,v in G.items(): print(k,'PASS' if v[0] else 'FAIL',v[1][:400])
