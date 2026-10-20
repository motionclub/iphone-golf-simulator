"""Package the actual saved depth-only continuation, without a likeness PASS."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof';H=P/'male_form_d/head_all_around'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Head_2');A=O/'appearance';FD=O.parent/'Male_Form_D';OLD=O.parent/'Male_Head_1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text());font=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
source=D/'blender/HeroBase_Male_Silhouette.blend';verify=load(P/'male-form-d-source-verification.json');metrics=load(P/'male-form-d-metrics.json');preview=load(A/'preview-audit.json');stats=load(W/'depth/profile-comparison.json')
assert sha(source)==verify['source_sha256']==preview['source_sha256']==metrics['source_verification']['source_sha256']
assert preview['source_unchanged'] and preview['body_vertices_unchanged']
base=np.load(W/'baseline/mesh.npz');co=np.load(W/'depth/actual.npy');before=base['co'];tri=base['tri']
assert np.array_equal(co[:,[0,2]],before[:,[0,2]]) and np.array_equal(co[before[:,2]<1.36],before[before[:,2]<1.36])
def normals(coords):
 t=coords[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
scope=np.max(before[tri,2],axis=1)>1.36
reversals=int(np.sum(np.einsum('ij,ij->i',normals(before),normals(co))[scope]<0));assert reversals==0
native=['front','front_left','left','back_left','back','back_right','right','front_right','top']
appearance=['face_front','face_threequarter','face_left','face_back_left','face_back','face_back_right','face_right','face_front_right','face_top']
def fit(canvas,path,box):
 q=Image.open(path).convert('RGBA');x,y,w,h=box;s=min(w/q.width,h/q.height);q=q.resize((round(q.width*s),round(q.height*s)),Image.Resampling.LANCZOS);canvas.paste(q,(x+(w-q.width)//2,y+(h-q.height)//2),q)
def sheet(paths,title,out):
 im=Image.new('RGB',(1800,1960),(43,43,45));dr=ImageDraw.Draw(im);dr.text((20,15),title,font=font(29),fill='white');dr.text((20,56),'Depth revision · chin and head likeness remain FAIL · actual saved geometry',font=font(23),fill=(218,218,218))
 for i,(name,p) in enumerate(paths):
  x=i%3*600;y=i//3*620+100;fit(im,p,(x,y+40,600,570));dr.text((x+15,y+8),name.replace('_',' '),font=font(22),fill='white')
 im.save(out)
sheet(list(zip(native,[H/(n+'.png') for n in native])),'Head form · eight directions plus top',P/'01e_head_all_around_m.png')
sheet(list(zip(native,[A/(n+'.png') for n in appearance])),'Actual Blender head · skin and facial-feature preview',O/'head-all-around-skin.png')
im=Image.new('RGB',(1800,1720),(43,43,45));dr=ImageDraw.Draw(im);dr.text((20,15),'Head depth · saved stage-1 checkpoint / current stage-2 continuation',font=font(27),fill='white')
for j,(label,folder) in enumerate([('Before',OLD/'head_native'),('After',H)]):
 for i,n in enumerate(['front','left','back','front_left']):
  x=i%2*450+j*900;y=i//2*760+85;fit(im,folder/(n+'.png'),(x,y+45,450,700));dr.text((x+15,y+10),label+' · '+n.replace('_',' '),font=font(23),fill='white')
im.save(P/'01f_head_before_after_m.png')
report={'head_likeness_gate':'FAIL','chin_check':'FAIL','full_body_gate':metrics['silhouette_gate'],'threshold':.02,
 'source_sha256':sha(source),'baseline_sha256':verify['head_stage_baseline_sha256'],'changes':metrics['coordinate_edits']['head_stage_2'],
 'profile_calipers':stats,'body_below_1_36m_unchanged':True,'X_Z_coordinates_unchanged':True,'head_triangle_normal_reversals':reversals,
 'preview_geometry_matches_source':True,'native_bald_views':metrics['measurements'],
 'remaining':'Chin curvature, uneven jaw surface, neck/shoulder transition, ear attachment/cartilage and broad face planes remain visibly different. Preview facial features are provisional. The unchanged full-body 2% threshold is unmet.'}
(P/'male-head-2-results.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['GATE: MALE_FORM FAIL','GATE: MALE_SIL FAIL','CHIN: FAIL · Head likeness: FAIL','',
 'Continued the existing male mesh from the saved e87ab1835f49 checkpoint. This pass focused on the jaw/neck depth relationship and its transition into the cranium. Only existing Body_M vertex Y coordinates changed. No restart, remesh, replacement mesh, hair or female work.',
 '', '| Authority view | Native difference / union | Error | 2% gate |','|---|---:|---:|---|']
for m in metrics['measurements']:lines.append(f'| {m["view"]} | {m["difference_pixels"]} / {m["union_pixels"]} | {100*m["error"]:.4f}% | FAIL |')
lines += ['', 'The full-body front/back errors are unchanged from this pass’s checkpoint because every X/Z coordinate is unchanged. Both still fail the direct human 2% requirement. No part crop or profile caliper replaces that gate.', '',
 '| Fixed head-detail profile diagnostic | Before mean absolute depth gap | After |','|---|---:|---:|',
 f'| Eight front jaw/throat calipers | {stats["jaw_throat_caliper_mean_absolute_error_mm_before"]:.3f} mm | {stats["jaw_throat_caliper_mean_absolute_error_mm_after"]:.3f} mm |',
 f'| Five rear neck calipers | {stats["rear_neck_caliper_mean_absolute_error_mm_before"]:.3f} mm | {stats["rear_neck_caliper_mean_absolute_error_mm_after"]:.3f} mm |','',
 'These sampled contour gaps use a fixed, normalized head-detail calibration documented in profile-calibration.json. They are diagnostics, not an independent likeness gate. The original image and all primary silhouette camera/mask data remain unchanged. Stubble coloration was ignored; the outer contour guided the sculpt.', '',
 'The anterior cranium was retracted relative to the retained chin, the nasal/lip plane moved back, the throat moved behind the chin, and the rear neck curve moved toward the reference. The final local displacement field has continuous falloffs. A direct per-layer projection that produced facial ridges was rejected before editing the main source.', '',
 'Actual all-around grey and skin renders still show rough chin/jaw surfaces, a poor neck/shoulder transition, weak ear structure and unfinished facial planes. CHIN remains FAIL even though central sampled contours are closer. The other four flags cover their defined body-form defects, not full character likeness.', '',
 f'METRIC scale 1, A-pose, height {verify["height_metres"]:.6f} m, {verify["vertices"]:,} vertices / {verify["triangles"]:,} triangles. Connectivity, origins, transforms, six locked cameras and three packed references are preserved. Body below 1.36 m is exactly unchanged from this checkpoint. No head triangle normal reversals against the checkpoint. Inherited topology defects were retained; no production topology PASS is claimed.', '',
 'Fresh FBX reimport and actual saved Unity prefab/capture verification passed. Source and Unity FBX hashes agree. Female sources, exports and prefabs retain their prerequisite hashes. Skin, eyes, brows and lips exist only in the separate appearance preview on identical Body_M coordinates.', '',
 'The continuous front/back reference conflict and native raster caveat remain in MALE_FORM_RESULTS.md. This pass does not prove an exact native-raster impossibility or a minimax optimum. Under 2% is not achieved.', '',
 'Proof: 01_silhouette_overlay_m.png; 01f_jaw_neck_profile_m.png; 01e_head_all_around_m.png; 01f_head_before_after_m.png; head-all-around-skin.png; 01d_form_m.png; 03_unity_m.png.', '',
 f'Saved blend SHA-256: `{sha(source)}`',f'FBX SHA-256: `{verify["fbx_sha256"]}`']
(P/'MALE_HEAD_2_RESULTS.md').write_text('\n'.join(lines)+'\n')
# Preserve stage-1 artifacts in the active review package as labelled history.
hist=FD/'history/head_stage_1';hist.mkdir(parents=True,exist_ok=True)
for n in ['MALE_HEAD_1_RESULTS.md','male-head-1-results.json','01e_head_before_after_m.png','MALE_FORM_D_COMPLETION_AUDIT.md']:
 p=FD/n
 if p.exists():shutil.move(str(p),str(hist/n))
prior=P/'MALE_FORM_D_COMPLETION_AUDIT.md';shutil.copy2(prior,W/'baseline/prior-head-stage-1-audit.md')
audit=['# Resumed male form audit — head stage 2','',
 'Second resumed turn: real saved mesh progress on the jaw/neck and cranial depth. Goal remains active; no completion or blocked status is claimed. Old blocked audits remain historical. The direct human 2% rule supersedes the stored 5% objective.', '',
 'GATE: MALE_FORM FAIL; GATE: MALE_SIL FAIL. bald_front 3.8232114977%; bald_back 3.7009053254%. CHIN FAIL, ARMS_SIDE/FEET_SIDE/SHOULDERS/WAIST PASS for their defined defects. Full head likeness FAIL.', '',
 'Front jaw/throat mean sampled depth gap improved 11.682 to 2.044 mm; rear neck 10.472 to 0.910 mm. These are fixed diagnostic calipers, not the full-body gate. Body below 1.36 m and every X/Z coordinate exactly unchanged; no reversed head triangle normals. Cameras, origins, metres, topology and packed plates unchanged.', '',
 'Chin curvature, jaw surface, neck/shoulder transition, ears and face planes still need work. Skin and provisional facial features are a separate current-source preview. No hair, female, rig or fashion work.', '',
 'Current Blender/FBX/Unity proof hashes verified. All seven actual Unity captures reviewed; source and Unity FBX match. Female prerequisite hashes retained. All proof processes completed before packaging.', '',
 f'Current source SHA-256: {sha(source)}.',f'Current FBX SHA-256: {verify["fbx_sha256"]}.', '',
 'Current deliverables: Male_Head_2 and refreshed Male_Form_D. Male_Head_1 is preserved as the historical checkpoint. Further local form work and a cleaner shared silhouette fit remain possible; 2% is unmet.']
prior.write_text('\n'.join(audit)+'\n')
files=[source,D/'unity_import/HeroBase_Male_Body.fbx']+[P/n for n in ['01_silhouette_overlay_m.png','01e_head_all_around_m.png','01f_jaw_neck_profile_m.png','01f_head_before_after_m.png','01d_form_m.png','03_unity_m.png','MALE_FORM_RESULTS.md','MALE_SIL_RESULTS.md','MALE_HEAD_2_RESULTS.md','male-head-2-results.json','MALE_FORM_D_COMPLETION_AUDIT.md','male-form-d-source-verification.json','male-form-d-source-audit.json','male-form-d-metrics.json','male-form-d-eye-checks.json','male-form-d-female-unchanged.json','male-form-unity-audit.txt','male-form-export.json','male-form-reference-limit.json','MALE_FORM_REFERENCE_CONFLICT.png']]
for p in files:shutil.copy2(p,O/p.name)
for n in ['01e_head_all_around_m.png','01f_jaw_neck_profile_m.png','01f_head_before_after_m.png','MALE_HEAD_2_RESULTS.md','male-head-2-results.json','MALE_FORM_D_COMPLETION_AUDIT.md']:shutil.copy2(P/n,FD/n)
shutil.copy2(W/'profile-calibration.json',O/'profile-calibration.json')
out=O/'head_native';out.mkdir(exist_ok=True)
for p in H.glob('*.png'):shutil.copy2(p,out/p.name)
out=O/'native_masks';out.mkdir(exist_ok=True)
for p in (FD/'native_masks').glob('*'):shutil.copy2(p,out/p.name)
# Blender preview backups are intermediate checkpoints, not latest deliverables.
backup=W/'preview-backups';backup.mkdir(exist_ok=True)
for p in A.glob('*.blend1'):shutil.move(str(p),str(backup/p.name))
for folder in [O,FD]:
 manifest={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'};(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'gate':'MALE_FORM FAIL','CHIN':'FAIL','source_sha256':sha(source),'profile_calipers_mm':{n:stats[n] for n in stats if n.endswith('_after')},'output':str(O)},indent=2))
