"""Current saved jaw-surface continuation and all-around proof, without PASS."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof';H=P/'male_form_d/head_all_around'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Head_3');A=O/'appearance';FD=O.parent/'Male_Form_D';OLD=O.parent/'Male_Head_2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text());font=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
source=D/'blender/HeroBase_Male_Silhouette.blend';verify=load(P/'male-form-d-source-verification.json');metrics=load(P/'male-form-d-metrics.json');preview=load(A/'preview-audit.json');stats=load(W/'profile-comparison.json');edit=load(W/'jaw-edit.json')
assert sha(source)==verify['source_sha256']==preview['source_sha256']==metrics['source_verification']['source_sha256']==stats['source_sha256']
assert preview['source_unchanged'] and preview['body_vertices_unchanged']
base=np.load(W/'baseline/mesh.npz');co=np.load(W/'jaw/actual.npy');b=base['co'];tri=base['tri']
assert np.array_equal(co[:,[0,2]],b[:,[0,2]]) and np.array_equal(co[b[:,2]<1.35],b[b[:,2]<1.35]) and np.array_equal(co[b[:,2]>1.54],b[b[:,2]>1.54])
def normals(c):
 t=c[tri];return np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
scope=np.max(b[tri,2],axis=1)>1.35;reversals=int(np.sum(np.einsum('ij,ij->i',normals(b),normals(co))[scope]<0));assert reversals==0
native=['front','front_left','left','back_left','back','back_right','right','front_right','top'];appearance=['face_front','face_threequarter','face_left','face_back_left','face_back','face_back_right','face_right','face_front_right','face_top']
def fit(canvas,path,box):
 q=Image.open(path).convert('RGBA') if not isinstance(path,Image.Image) else path.convert('RGBA');x,y,w,h=box;s=min(w/q.width,h/q.height);q=q.resize((round(q.width*s),round(q.height*s)),Image.Resampling.LANCZOS);canvas.paste(q,(x+(w-q.width)//2,y+(h-q.height)//2),q)
def sheet(paths,title,out):
 im=Image.new('RGB',(1800,1960),(43,43,45));dr=ImageDraw.Draw(im);dr.text((20,15),title,font=font(29),fill='white');dr.text((20,56),'Jaw surface revision · CHIN and full likeness remain FAIL · actual saved geometry',font=font(22),fill=(218,218,218))
 for i,(name,p) in enumerate(paths):
  x=i%3*600;y=i//3*620+100;fit(im,p,(x,y+40,600,570));dr.text((x+15,y+8),name.replace('_',' '),font=font(22),fill='white')
 im.save(out)
sheet(list(zip(native,[H/(n+'.png') for n in native])),'Head form · eight directions plus top',P/'01e_head_all_around_m.png')
sheet(list(zip(native,[A/(n+'.png') for n in appearance])),'Actual Blender head · skin and facial-feature preview',O/'head-all-around-skin.png')
ref=Image.open(D/'male_head_detail.jpg').convert('RGB');im=Image.new('RGB',(1800,1870),(43,43,45));dr=ImageDraw.Draw(im)
dr.text((20,16),'Chin / under-chin / neck surface · reference and actual Blender geometry',font=font(27),fill='white');dr.text((20,56),'Local depth sculpt; original X/Z silhouette unchanged · likeness still FAIL',font=font(23),fill=(218,218,218))
for row,(n,box) in enumerate([('front',(148,74,310,326)),('left',(505,76,713,326)),('front_left',(139,396,300,643))]):
 y=100+row*590
 for col,(label,path) in enumerate([('Reference · '+n,ref.crop(box)),('Before · '+n,OLD/'head_native'/(n+'.png')),('After · '+n,H/(n+'.png'))]):
  dr.text((col*600+15,y+8),label.replace('_',' '),font=font(23),fill='white');fit(im,path,(col*600,y+42,600,535))
im.save(P/'01g_jaw_surface_m.png')
report={'gate':'MALE_FORM FAIL','silhouette_gate':'MALE_SIL FAIL','CHIN':'FAIL','head_likeness':'FAIL','threshold':.02,'source_sha256':sha(source),'baseline_sha256':verify['head_stage_baseline_sha256'],'edit':edit,'profile_calipers':stats,'native_bald_views':metrics['measurements'],'body_below_1_35m_unchanged':True,'upper_head_above_1_54m_unchanged':True,'X_Z_coordinates_unchanged':True,'head_triangle_normal_reversals':reversals,'preview_geometry_matches_source':True,'remaining':'Lower-jaw curvature and its transition to neck, ears and broad facial planes still differ visibly from head_detail. Strict full-body 2% gate unmet.'}
(P/'male-head-3-results.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['GATE: MALE_FORM FAIL','GATE: MALE_SIL FAIL','CHIN: FAIL · Head likeness: FAIL','',
 'Continued the saved 8da71e595209 male mesh; only existing jaw, under-chin and lower-neck vertex depth changed. Local positive coordinate fairing reduces surface ripples, and a rounded lower-face depth field is guided by the fixed head-detail profile calipers. No restart, remesh or replacement mesh.', '',
 '| Native authority view | Difference / union | Error | Required |','|---|---:|---:|---:|']
for m in metrics['measurements']:lines.append(f'| {m["view"]} | {m["difference_pixels"]} / {m["union_pixels"]} | {100*m["error"]:.4f}% | ≤2.0% |')
lines += ['', 'Both full-body views still fail. Each native alpha mask is identical to this stage’s saved checkpoint: all X/Z coordinates were preserved. The latest direct human 2% requirement supersedes the stored goal’s older 5% rule.', '',
 f'The local graph depth-Laplacian diagnostic fell from {edit["diagnostic_mean_absolute_depth_laplacian_mm_before"]:.3f} to {edit["diagnostic_mean_absolute_depth_laplacian_mm_after"]:.3f} mm within the specified jaw/neck region. This documents reduced depth ripples, not likeness or a silhouette PASS. Front jaw/throat mean sampled gap is {stats["jaw_throat_caliper_mean_absolute_error_mm_after"]:.3f} mm; rear neck {stats["rear_neck_caliper_mean_absolute_error_mm_after"]:.3f} mm. The calibrated central profile is retained; these diagnostic samples do not prove the full form matches.', '',
 'An XYZ fairing candidate was rejected because it worsened both silhouette measurements. An overly strong local depth projection was reduced before source mutation to avoid reversing existing thin face normals. Only the accepted depth field was saved.', '',
 'Actual all-around grey and skin renders show softer neck ripples and a rounder lower-face depth, but lower-jaw curvature and its transition to the neck remain visibly different. Ears, broad facial planes and provisional cosmetic features still require work. CHIN and head likeness remain FAIL.', '',
 f'METRIC scale 1, A-pose, height {verify["height_metres"]:.6f} m; {verify["vertices"]:,} vertices / {verify["triangles"]:,} triangles. Body below 1.35 m, upper head above 1.54 m, connectivity, transforms, origins, six locked cameras and three packed plates unchanged. No head triangle normal reversals relative to the checkpoint. Inherited topology defects remain; no production topology PASS is claimed.', '',
 'Current scale-one FBX reimport and actual saved Unity prefab/capture verification passed. Female sources, exports and prefabs retain their prerequisite hashes. Hair, female, rig and fashion work are absent. Skin and facial features exist only in a separate preview on identical Body_M coordinates.', '',
 'The continuous reference conflict and native-raster caveat remain in MALE_FORM_RESULTS.md. This is not an exact native-raster impossibility proof, a minimax optimum, or an achieved 2% result.', '',
 'Proof: 01g_jaw_surface_m.png; 01e_head_all_around_m.png; head-all-around-skin.png; 01_silhouette_overlay_m.png; 01d_form_m.png; 03_unity_m.png.', '',
 f'Saved source SHA-256: `{sha(source)}`',f'FBX SHA-256: `{verify["fbx_sha256"]}`']
(P/'MALE_HEAD_3_RESULTS.md').write_text('\n'.join(lines)+'\n')
hist=FD/'history/head_stage_2';hist.mkdir(parents=True,exist_ok=True)
for n in ['MALE_HEAD_2_RESULTS.md','male-head-2-results.json','01f_jaw_neck_profile_m.png','01f_head_before_after_m.png','MALE_FORM_D_COMPLETION_AUDIT.md']:
 p=FD/n
 if p.exists():shutil.move(str(p),str(hist/n))
audit=['# Resumed male form audit — head stage 3','',
 'Previous goal turn: progress. The last stage changed the authoritative source, completed export verification and added evidence identifying the next jaw-surface work. This third resumed turn also changes authoritative geometry. No repeated blocked audit threshold applies; the goal remains active.', '',
 'Current GATE: MALE_FORM FAIL; MALE_SIL FAIL. CHIN FAIL; ARMS_SIDE, FEET_SIDE, SHOULDERS and WAIST PASS for their defined defects. bald_front 3.8232114977%; bald_back 3.7009053254%; latest direct human threshold 2% remains unmet. Full head likeness FAIL.', '',
 'Saved local jaw/under-chin/neck depth sculpt, without remesh or restart. Every X/Z coordinate, body below 1.35 m, upper head above 1.54 m, cameras, origins, topology, metres and packed plates unchanged. Native authority masks identical to checkpoint. No reversed head triangle normals. Surface depth ripples reduced, but lower-jaw/neck curvature remains imperfect.', '',
 'Source/FBX independent verification and actual saved Unity captures checked. Current cosmetic appearance preview uses identical Body_M coordinates. All proof processes completed before packaging. Female prerequisite hashes retained.', '',
 f'Source SHA-256: {sha(source)}.',f'FBX SHA-256: {verify["fbx_sha256"]}.', '',
 'Current deliverables: Male_Head_3 and refreshed Male_Form_D. Historical Male_Head_1/2 packages remain unchanged. Under 2% is not demonstrated, and no goal completion is claimed. Further reference-guided local form and shared silhouette work remain possible.']
(P/'MALE_FORM_D_COMPLETION_AUDIT.md').write_text('\n'.join(audit)+'\n')
files=[source,D/'unity_import/HeroBase_Male_Body.fbx']+[P/n for n in ['01_silhouette_overlay_m.png','01e_head_all_around_m.png','01g_jaw_surface_m.png','01d_form_m.png','03_unity_m.png','MALE_FORM_RESULTS.md','MALE_SIL_RESULTS.md','MALE_HEAD_3_RESULTS.md','male-head-3-results.json','MALE_FORM_D_COMPLETION_AUDIT.md','male-form-d-source-verification.json','male-form-d-source-audit.json','male-form-d-metrics.json','male-form-d-eye-checks.json','male-form-d-female-unchanged.json','male-form-unity-audit.txt','male-form-export.json','male-form-reference-limit.json','MALE_FORM_REFERENCE_CONFLICT.png']]
for p in files:shutil.copy2(p,O/p.name)
for n in ['01e_head_all_around_m.png','01g_jaw_surface_m.png','MALE_HEAD_3_RESULTS.md','male-head-3-results.json','MALE_FORM_D_COMPLETION_AUDIT.md']:shutil.copy2(P/n,FD/n)
out=O/'head_native';out.mkdir(exist_ok=True)
for p in H.glob('*.png'):shutil.copy2(p,out/p.name)
out=O/'native_masks';out.mkdir(exist_ok=True)
for p in (FD/'native_masks').glob('*'):shutil.copy2(p,out/p.name)
for folder in [O,FD]:
 manifest={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='manifest.json'};(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'gate':'MALE_FORM FAIL','CHIN':'FAIL','source_sha256':sha(source),'output':str(O)},indent=2))
