from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,shutil,numpy as np
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof';H=P/'male_form_d/head_all_around'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Hand_4');FD=O.parent/'Male_Form_D';A=O/'appearance'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();font=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
blend=D/'blender/HeroBase_Male_Silhouette.blend';verify=load(P/'male-form-d-source-verification.json');metrics=load(P/'male-form-d-metrics.json');preview=load(A/'preview-audit.json')
assert sha(blend)==verify['source_sha256']==preview['source_sha256']==metrics['source_verification']['source_sha256'];assert preview['body_vertices_unchanged'] and preview['source_unchanged']
b=np.load(W/'baseline/mesh.npz')['co'];c=np.load(W/'accepted.npy');scope=np.load(W/'scope.npy');assert np.array_equal(c[~scope],b[~scope])
assert verify['outside_distal_hand_region_unchanged'] and verify['head_geometry_unchanged']
def fit(canvas,q,box):
 if not isinstance(q,Image.Image):q=Image.open(q)
 q=q.convert('RGBA');x,y,w,h=box;s=min(w/q.width,h/q.height);q=q.resize((round(q.width*s),round(q.height*s)),Image.Resampling.LANCZOS);canvas.paste(q,(x+(w-q.width)//2,y+(h-q.height)//2),q)
im=Image.new('RGB',(2100,1650),(36,36,39));dr=ImageDraw.Draw(im);dr.text((20,16),'Distal hand / thumb correction · existing male mesh',font=font(30),fill='white');dr.text((20,58),'Before / current · rounded thumb restored · fingers remain an unfinished blockout',font=font(23),fill=(220,220,220))
for col,n in enumerate(['hand_front','hand_threequarter','hand_left']):
 for row,(label,folder) in enumerate([('Before',W/'before'),('Current',W/'accepted')]):
  y=110+row*750;dr.text((col*700+15,y),label+' · '+n.replace('hand_','').replace('_',' '),font=font(24),fill='white');fit(im,folder/(n+'.png'),(col*700,y+40,700,690))
im.save(P/'01h_hand_form_m.png')
names=['front','front_left','left','back_left','back','back_right','right','front_right','top'];im=Image.new('RGB',(1800,1960),(43,43,45));dr=ImageDraw.Draw(im);dr.text((20,15),'Current saved head · eight directions plus top',font=font(29),fill='white');dr.text((20,56),'Head geometry unchanged in hand revision · CHIN and likeness remain FAIL',font=font(23),fill=(218,218,218))
for i,n in enumerate(names):
 x=i%3*600;y=i//3*620+100;dr.text((x+15,y+8),n.replace('_',' '),font=font(22),fill='white');fit(im,H/(n+'.png'),(x,y+40,600,570))
im.save(P/'01e_head_all_around_m.png')
im=Image.new('RGB',(2000,1220),(43,43,45));dr=ImageDraw.Draw(im);dr.text((20,14),'Actual current Blender body · skin and provisional facial features',font=font(26),fill='white');dr.text((20,54),'Geometry identical to saved source · hair absent · appearance preview only',font=font(22),fill=(218,218,218))
for i,n in enumerate(['front','back','left','right','threequarter']):
 dr.text((i*400+15,93),n.replace('threequarter','three-quarter'),font=font(21),fill='white');fit(im,A/('body_'+n+'.png'),(i*400,125,400,1065))
im.save(O/'body-all-around-skin.png')
edit=load(W/'accepted-edit.json');report={'gate':'MALE_FORM FAIL','threshold':.02,'source_sha256':sha(blend),'baseline_sha256':verify['head_stage_baseline_sha256'],'edit':edit,'native_bald_views':metrics['measurements'],'outside_distal_hands_unchanged':True,'head_neck_torso_legs_unchanged':True,'hand_anatomy':'Unfinished blockout; thumb spike repaired, finger shapes still rough.','chin':'FAIL','full_head_likeness':'FAIL','reference_hand_pose_conflict':'Frozen front target has a separated projected thumb; reflected back target has a substantially different continuous hand contour. Both remain authority.'}
(P/'male-hand-4-results.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['GATE: MALE_FORM FAIL','', 'Latest direct human threshold: each bald view ≤2.0%; still unmet. CHIN FAIL; ARMS_SIDE, FEET_SIDE, SHOULDERS, WAIST PASS for their defined defects.', '',
 'Continued the d977d900d020 saved mesh, working only on distal hands and their wrist transitions. Earlier contour edits stretched thumb vertices into a thin spike. Correspondence with the historical existing mesh vertices/edges was verified, then local coordinates were unfolded and the palm/fingers fitted to both unchanged authority masks. No restart, remesh, mesh replacement or vertex/face additions.', '',
 '| View | Before | Current | Difference / union | 2% gate |','|---|---:|---:|---:|---|']
before={'bald_front':3.8232114976580327,'bald_back':3.7009053253639514}
for m in metrics['measurements']:lines.append(f'| {m["view"]} | {before[m["view"]]:.4f}% | {m["error"]*100:.4f}% | {m["difference_pixels"]} / {m["union_pixels"]} | FAIL |')
lines += ['', 'The larger error falls from 3.8232% to 3.7819%; the front improves while the back rises slightly. This is not a claim that both views improved. The separate thumb volume is less distorted and excessive hand depth is reduced. Finger surfaces and anatomy remain rough, with inherited topology defects; no production hand/topology PASS is claimed.', '',
 'The frozen front reference has a separate projected thumb; the reflected back mask has a substantially different hand contour. This supports the reference-pair conflict already documented in MALE_FORM_RESULTS.md. Continuous 6.2479% reference distance / ≥3.1239% minimax bound is not an exact native-raster impossibility proof. Both original native masks remain authoritative; under 2% is not achieved.', '',
 f'All vertices outside the distal-hand region are exactly unchanged, including the head/neck, torso and legs. Metres, A-pose, height {verify["height_metres"]:.6f} m, 24,578 vertices / 49,176 triangles, connectivity, origins, transforms, six locked cameras and three packed plates retained. No female, hair, rig or fashion changes.', '',
 'Fresh scale-one FBX reimport and actual saved Unity prefab/capture verification passed. Source and Unity FBX match. Female prerequisite hashes retained. Grey main source has one Body_M and Blockout_Grey; skin and provisional face objects belong only to the separate appearance preview on identical body geometry.', '',
 'Proof: 01h_hand_form_m.png; 01_silhouette_overlay_m.png; 01d_form_m.png; 03_unity_m.png; 01e_head_all_around_m.png; body-all-around-skin.png.', '',
 f'Saved source SHA-256: `{sha(blend)}`',f'FBX SHA-256: `{verify["fbx_sha256"]}`']
(P/'MALE_HAND_4_RESULTS.md').write_text('\n'.join(lines)+'\n')
hist=FD/'history/head_stage_3';hist.mkdir(parents=True,exist_ok=True)
for n in ['MALE_HEAD_3_RESULTS.md','male-head-3-results.json','01g_jaw_surface_m.png','MALE_FORM_D_COMPLETION_AUDIT.md']:
 p=FD/n
 if p.exists():shutil.move(str(p),str(hist/n))
audit=['# Resumed male form audit — distal hand stage 4','',
 'Previous goal turn: progress, because the authoritative jaw/neck source and required proofs were updated. This turn also changes authoritative state: local hand/thumb repair and fresh Blender/FBX/Unity proof. The goal remains active. No completion or blocked status is claimed; other local form and contour corrections remain possible.', '',
 'GATE MALE_FORM FAIL. ARMS_SIDE PASS; CHIN FAIL; FEET_SIDE PASS; SHOULDERS PASS; WAIST PASS. Strict 2% native authority gate unmet: bald_front 3.7746163384%; bald_back 3.7818975506%. Full head likeness FAIL.', '',
 'Local distal-hand vertices only; head/neck, torso, legs and other vertices exactly unchanged. No restart/remesh. Metres, A-pose, height, topology, cameras, origins and packed references retained. Rounded thumb spike repair accepted with shared palm/finger outline and reduced excessive hand depth; fingers still unfinished.', '',
 'Actual current saved Blender, independent FBX reimport, saved Unity prefab and capture hashes verified. Female prerequisites unchanged. Current appearance preview has identical Body_M geometry. All proof processes completed before packaging.', '',
 f'Source SHA-256: {sha(blend)}.',f'FBX SHA-256: {verify["fbx_sha256"]}.', '',
 'Current deliverables in Male_Hand_4 and refreshed Male_Form_D. Male_Head_1/2/3 are historical checkpoints. Reference-pair conflict remains documented with native-raster caveat. No 2% PASS or production topology/hand PASS is claimed.']
(P/'MALE_FORM_D_COMPLETION_AUDIT.md').write_text('\n'.join(audit)+'\n')
files=[blend,D/'unity_import/HeroBase_Male_Body.fbx']+[P/n for n in ['01_silhouette_overlay_m.png','01h_hand_form_m.png','01e_head_all_around_m.png','01d_form_m.png','03_unity_m.png','MALE_FORM_RESULTS.md','MALE_SIL_RESULTS.md','MALE_HAND_4_RESULTS.md','male-hand-4-results.json','MALE_FORM_D_COMPLETION_AUDIT.md','male-form-d-source-verification.json','male-form-d-source-audit.json','male-form-d-metrics.json','male-form-d-eye-checks.json','male-form-d-female-unchanged.json','male-form-unity-audit.txt','male-form-export.json','male-form-reference-limit.json','MALE_FORM_REFERENCE_CONFLICT.png']]
for p in files:shutil.copy2(p,O/p.name)
for n in ['01h_hand_form_m.png','01e_head_all_around_m.png','MALE_HAND_4_RESULTS.md','male-hand-4-results.json','MALE_FORM_D_COMPLETION_AUDIT.md']:shutil.copy2(P/n,FD/n)
out=O/'head_native';out.mkdir(exist_ok=True)
for p in H.glob('*.png'):shutil.copy2(p,out/p.name)
out=O/'hand_native';out.mkdir(exist_ok=True)
for p in (W/'accepted').glob('hand_*.png'):shutil.copy2(p,out/p.name)
out=O/'native_masks';out.mkdir(exist_ok=True)
for p in (FD/'native_masks').glob('*'):shutil.copy2(p,out/p.name)
for f in [O,FD]:
 manifest={str(p.relative_to(f)):sha(p) for p in f.rglob('*') if p.is_file() and p.name!='manifest.json'};(f/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'gate':'MALE_FORM FAIL','source_sha256':sha(blend),'output':str(O)},indent=2))
