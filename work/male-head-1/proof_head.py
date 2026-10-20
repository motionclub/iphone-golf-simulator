from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,shutil
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof';H=P/'male_form_d/head_all_around';S=R/'work/male-silhouette'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Head_1');O.mkdir(exist_ok=True);A=O/'appearance'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();font=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
native=['front','front_left','left','back_left','back','back_right','right','front_right','top'];appearance=['face_front','face_threequarter','face_left','face_back_left','face_back','face_back_right','face_right','face_front_right','face_top']
def fit(canvas,path,box):
 q=Image.open(path).convert('RGBA');x,y,w,h=box;scale=min(w/q.width,h/q.height);q=q.resize((round(q.width*scale),round(q.height*scale)),Image.Resampling.LANCZOS);canvas.paste(q,(x+(w-q.width)//2,y+(h-q.height)//2),q)
def sheet(paths,title,out):
 im=Image.new('RGB',(1800,1960),(43,43,45));dr=ImageDraw.Draw(im);dr.text((20,15),title,font=font(29),fill='white');dr.text((20,56),'Existing male mesh · head revision stage 1 · likeness remains FAIL',font=font(23),fill=(218,218,218))
 for i,(name,p) in enumerate(paths):
  x=i%3*600;y=i//3*620+100;fit(im,p,(x,y+40,600,570));dr.text((x+15,y+8),name.replace('_',' '),font=font(22),fill='white')
 im.save(out)
sheet(list(zip(native,[H/(n+'.png') for n in native])),'Head form · eight directions plus top',P/'01e_head_all_around_m.png')
sheet(list(zip(native,[A/(n+'.png') for n in appearance])),'Actual Blender head · skin and facial-feature preview',O/'head-all-around-skin.png')
comparison=Image.new('RGB',(1800,1720),(43,43,45));dr=ImageDraw.Draw(comparison);dr.text((20,15),'Head form · resumed checkpoint / current revision',font=font(29),fill='white')
for j,(label,folder,prefix) in enumerate([('Before',W/'before','head_'),('After',H,'')]):
 for i,n in enumerate(['front','left','back','front_left']):
  x=i%2*450+j*900;y=i//2*760+85;fit(comparison,folder/(prefix+n+'.png'),(x,y+45,450,700));dr.text((x+15,y+10),label+' · '+n.replace('_',' '),font=font(23),fill='white')
comparison.save(P/'01e_head_before_after_m.png')
source=D/'blender/HeroBase_Male_Silhouette.blend';verify=json.loads((P/'male-form-d-source-verification.json').read_text());metrics=json.loads((P/'male-form-d-metrics.json').read_text());preview=json.loads((A/'preview-audit.json').read_text());assert preview['source_sha256']==sha(source)==verify['source_sha256'];assert preview['body_vertices_unchanged']
regions=[]
for view in ['bald_front','bald_back']:
 t=np.array(Image.open(S/(view+'_target.png')).convert('L'))>127
 counts={}
 for name,path in [('before',W/'before'/(view+'.png')),('after',P/'male_silhouette'/(view+'.png'))]:
  m=np.array(Image.open(path).getchannel('A'))>127;counts[name]={'full_body_error':float(np.sum(m^t)/np.sum(m|t)),'head_crop_error':float(np.sum((m^t)[:160])/np.sum((m|t)[:160])),'difference_pixels':int(np.sum(m^t)),'union_pixels':int(np.sum(m|t))}
 regions.append({'view':view,**counts})
report={'head_likeness_gate':'FAIL','full_body_gate':metrics['silhouette_gate'],'threshold':.02,'source_sha256':sha(source),'head_stage_baseline_sha256':verify['head_stage_baseline_sha256'],'views':regions,'head_crop_description':'Original native image rows 0..159, per authority view; diagnostic only, not a new gate.','changes':metrics['coordinate_edits']['head_stage'],'body_below_1_38m_unchanged':True,'topology_cameras_origins_unchanged':True,'preview_geometry_matches_source':True,'remaining':'Ear attachments/cartilage, jaw-to-neck profile and broad facial planes still differ visibly from head_detail. Cosmetic preview eyes and lips remain provisional. Full bald-view 2% threshold remains unmet.'}
(P/'male-head-1-results.json').write_text(json.dumps(report,indent=2))
lines=['GATE: MALE_FORM FAIL','GATE: MALE_SIL FAIL','Head likeness: FAIL','','Resumed the saved male mesh from the ec8ff3b checkpoint, without restarting or remeshing. This stage worked only on the head/neck above 1.38 m, in sequence: cranial dome, jaw/chin, forehead and ear volumes, broad face planes, then the shared front/back head contours.','', '| Native authority view | Before: full body | After: full body | Before: head crop | After: head crop |','|---|---:|---:|---:|---:|']
for r in regions:lines.append(f'| {r["view"]} | {100*r["before"]["full_body_error"]:.4f}% | {100*r["after"]["full_body_error"]:.4f}% | {100*r["before"]["head_crop_error"]:.4f}% | {100*r["after"]["head_crop_error"]:.4f}% |')
lines+=['','The head crop uses original image rows 0–159 in each native authority image. It is a diagnostic for this part, not a substitute for the full-body 2% gate. Both full-body views still fail.','',f'Metres, A-pose, height {verify["height_metres"]:.6f} m; 24,578 vertices / 49,176 triangles. Existing connectivity, origins, transforms, six locked cameras and three packed plates preserved. Body below 1.38 m exactly preserved. No female or hair changes. No reversed head triangle normals against the resumed checkpoint. The inherited topology was retained, including its pre-existing defects; no production topology PASS is claimed.','', 'The dome is now rounded through its top and sides; the lower face is narrower and less projected, with a smoother throat transition. Ear volumes and shallow orbital/nasal planes were revised in the existing mesh. Ear attachments/cartilage, jaw-to-neck proportions and face planes still differ from the reference. Head likeness remains FAIL.','', 'Skin/eyes/lids/brows/lips are a separate Blender appearance preview, rendered from this exact current mesh in eight directions plus top. They do not alter the grey gate source or manufacture a silhouette PASS.','', 'Fresh scale-one FBX export, independent coordinate reimport and saved Unity prefab/capture verification passed. The original bald reference masks and cameras are unchanged. The frozen authority pair’s continuous outline conflict remains documented in MALE_FORM_RESULTS.md, with its native raster caveat. Further modelling can improve likeness and the current fit; under 2% is not demonstrated.','',f'Saved source SHA-256: `{sha(source)}`','', 'Proof: 01_silhouette_overlay_m.png; 01e_head_all_around_m.png; 01e_head_before_after_m.png; head-all-around-skin.png; 01d_form_m.png; 03_unity_m.png.']
(P/'MALE_HEAD_1_RESULTS.md').write_text('\n'.join(lines)+'\n')
for p in [source,D/'unity_import/HeroBase_Male_Body.fbx',P/'01_silhouette_overlay_m.png',P/'01e_head_all_around_m.png',P/'01e_head_before_after_m.png',P/'01d_form_m.png',P/'03_unity_m.png',P/'MALE_FORM_RESULTS.md',P/'MALE_SIL_RESULTS.md',P/'MALE_HEAD_1_RESULTS.md',P/'male-head-1-results.json',P/'male-form-d-source-verification.json',P/'male-form-d-metrics.json',P/'male-form-unity-audit.txt']:
 shutil.copy2(p,O/p.name)
out=O/'head_native';out.mkdir(exist_ok=True)
for p in H.glob('*.png'):shutil.copy2(p,out/p.name)
manifest={str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file() and p.name!='manifest.json'};(O/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'head_stage_report':str(O/'MALE_HEAD_1_RESULTS.md'),'measurements':regions},indent=2))
