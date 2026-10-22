from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,shutil,re,zipfile
from plate_profiles import MALE,FEMALE
R=Path(__file__).resolve().parents[2];D=R/'ArtDir/hero/base_lock';P=D/'proof';OUT=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs');O=OUT/'HeroBase_Review';O.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',15)
source=json.loads((P/'saved-source-audit.json').read_text());blender=json.loads((P/'silhouette-metrics.json').read_text());unity_audit=(P/'unity-mesh-material-audit.txt').read_text();bounds_audit=(P/'unity-import.txt').read_text()
results=[]
for sex,suf,pr in [('Male','M',MALE),('Female','F',FEMALE)]:
 panel=Image.new('RGB',(1680,770),(32,32,36));draw=ImageDraw.Draw(panel);draw.text((18,12),f'HeroBase_{sex} — CURRENT CANDIDATE · GATE: BASE FAIL',font=font,fill='white');views={}
 bald_panel=Image.new('RGB',(1680,1500),(32,32,36));bd=ImageDraw.Draw(bald_panel);bd.text((18,12),f'{sex} — independent hairstyle / body-only prefab · actual Unity renders',font=font,fill='white')
 for i,view in enumerate(['front','back','threequarter']):
  shot=Image.open(P/'unity'/(suf+'_'+view+'.png')).convert('RGB');panel.paste(shot.crop((360,0,920,720)),(560*i,50));draw.text((560*i+16,40),view,font=small,fill='white')
  bald_panel.paste(shot.crop((360,0,920,720)),(560*i,50));bd.text((560*i+16,37),'Default hair · '+view,font=small,fill='white')
  bald=Image.open(P/'unity'/(suf+'_bald_'+view+'.png')).convert('RGB');bald_panel.paste(bald.crop((360,0,920,720)),(560*i,780));bd.text((560*i+16,767),'Body only · '+view,font=small,fill='white')
  a=np.array(Image.open(P/'blender'/(suf+'_'+view+'.png')).getchannel('A'))>127;mask=np.array(Image.open(P/'unity'/(suf+'_'+view+'_mask.png')).convert('RGB')).mean(axis=2)>127
  ba=np.array(Image.open(P/'blender'/(suf+'_bald_'+view+'.png')).getchannel('A'))>127;bm=np.array(Image.open(P/'unity'/(suf+'_bald_'+view+'_mask.png')).convert('RGB')).mean(axis=2)>127
  views[view]={'blender_unity_silhouette_difference_over_union':float((a^mask).sum()/(a|mask).sum()),'body_only_blender_unity_silhouette_difference_over_union':float((ba^bm).sum()/(ba|bm).sum())}
  if view in ['front','back']:
   cx=pr['cx' if view=='front' else 'back_cx'];b=np.array(Image.open(P/'masks'/(suf+'_'+view+'_target.png')))>0;shift=Image.new('L',(1280,720));shift.paste(Image.fromarray(np.uint8(mask)*255),(cx-640,0));c=np.array(shift)>0;views[view]['unity_plate_silhouette_difference_over_union']=float((b^c).sum()/(b|c).sum())
 panel.save(P/('03_unity_'+suf.lower()+'.png'));bald_panel.save(P/('04_hair_removal_'+suf.lower()+'.png'));results.append({'sex':sex,'views':views})
# Head closeups are crops of native renders, scaled equally for review. Measurements above use uncropped native images.
heads=Image.new('RGB',(1440,690),(32,32,36));hd=ImageDraw.Draw(heads);hd.text((18,12),'Removable hair — complete scalp in the independent body prefabs · Unity URP',font=font,fill='white')
for row,(sex,suf) in enumerate([('Male','M'),('Female','F')]):
 y=55+row*315
 for col,(view,bald) in enumerate([(v,b) for v in ['front','threequarter','back'] for b in [False,True]]):
  label=sex+' '+view+(' · body only' if bald else ' · default hair');hd.text((col*240+8,y),label,font=small,fill='white')
  path=P/'unity'/(suf+('_bald' if bald else '')+'_'+view+'.png');im=Image.open(path).convert('RGB').crop((546,8 if sex=='Male' else 68,734,206 if sex=='Male' else 215));im=im.resize((224,round(im.height*224/188)),Image.Resampling.LANCZOS);heads.paste(im,(col*240+8,y+26))
heads.save(P/'hair-removal-heads.png')
face=Image.new('RGB',(780,340),(36,36,39));dr=ImageDraw.Draw(face)
for i,(sex,suf,pr) in enumerate([('Male','M',MALE),('Female','F',FEMALE)]):
 y0=15 if sex=='Male' else 72;y1=201 if sex=='Male' else 211;src=Image.open(D/(sex.lower()+'_body_plain.jpg')).convert('RGB').crop((pr['cx']-70,y0,pr['cx']+70,y1));cur=Image.open(P/'unity'/(suf+'_front.png')).convert('RGB').crop((570,y0,710,y1))
 for j,(label,im) in enumerate([(sex+' plate',src),(sex+' URP',cur)]):
  x=(i*2+j)*195;dr.text((x+8,12),label,font=small,fill='white');im=im.resize((180,round(im.height*180/140)),Image.Resampling.NEAREST);face.paste(im,(x+5,45))
face.save(P/'face-comparison.png')
(P/'unity-comparison-metrics.json').write_text(json.dumps({'method':'Native 1280x720 renders. Unity silhouette is a separate unlit-white geometry pass with the same camera and meshes. Body-only proofs instantiate independent body prefabs, with no hair object. Both plate overlays use fixed frozen scale and x-only framing translation. Lighting remains a separate visual gate.','measurements':results},indent=2))
manifest={};metric_rows=[];removal_rows=[]
for row in source:
 sex=row['sex'];suf=sex[0];body,hair=row['parts'];total=body['triangles']+hair['triangles'];attachment=row['attachment'];exports={}
 assert row['plate_hash_matches'] and row['armatures']==0
 assert body['scalp_boundary_edges']==body['scalp_nonmanifold_edges']==body['hair_materials']==0
 assert f'{sex} REMOVE_HAIR_ROOT body_mesh_unchanged=True body_renderers=1' in unity_audit
 assert f'{sex} BODY_PREFAB hair_dependencies=0' in unity_audit
 assert re.search(sex+r' BALD .* renderers=1',bounds_audit)
 for part in row['parts']:
  match=re.search(sex+' '+part['name']+r' vertices=\d+ tris=(\d+)',unity_audit);assert match and int(match.group(1))==part['triangles']
 for asset in row['exports']:
  src=D/'unity_import'/asset['path'];dst=R/'Unity/Assets/Characters/HeroBase/Models'/src.name;sha=hashlib.sha256(src.read_bytes()).hexdigest();assert sha==asset['sha256']==hashlib.sha256(dst.read_bytes()).hexdigest(),'Stale Unity model'
  exports[asset['path']]={'sha256':sha,'mesh_count':len(asset['mesh_names']),'triangles':asset['triangles'],'materials':asset['materials']}
 prefabs={}
 for rel in [f'HeroBase_{sex}.prefab',f'Bodies/HeroBase_{sex}_Body.prefab',f'Hair/Hair_Default_{sex}.prefab']:
  file=R/'Unity/Assets/Characters/HeroBase'/rel;prefabs[rel]={'path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 manifest[sex]={'exports':exports,'prefabs':prefabs,'hair_anchor_metres':attachment['hair_anchor_metres'],'body_contains_hair':False,'scalp_boundary_edges':0,'scalp_nonmanifold_edges':0}
 world=float(re.search(sex+r' DEFAULT_HAIR .* HEIGHT=([0-9.]+)',bounds_audit).group(1));bald=float(re.search(sex+r' BALD .* HEIGHT=([0-9.]+)',bounds_audit).group(1))
 metric_rows.append(f'| {sex} | {body["triangles"]:,} | {hair["triangles"]:,} | {total:,} | {world:.6f} | {bald:.6f} |')
 removal_rows.append(f'| {sex} | one Body_{suf} mesh; no Hair material | one body renderer; zero hair dependencies | {body["scalp_boundary_edges"]} open / {body["scalp_nonmanifold_edges"]} nonmanifold scalp edges | {bald:.6f} m |')
(P/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
lines=['GATE: BASE FAIL','','Current static-character candidate. The removable-hair requirement passes; the overall plate-fidelity goal remains active.','','| Required line | Result | Evidence |','|---|---|---|']
for row in blender['measurements']:
 m=row['metrics'];lines.append(f"| {row['sex'].title()} front/back overlay ≤ ~5% | FAIL | {m['front']['symmetric_difference_over_union']*100:.2f}% / {m['back']['symmetric_difference_over_union']*100:.2f}%; 01_silhouette_overlay_{row['sex'][0]}.png, silhouette-metrics.json |")
lines += ['| Face / hair match locked plate | FAIL | face-comparison.png and 02_match_m.png / 02_match_f.png: cheek/jaw, mouth/eyelid shapes, quiff and bob clump shapes still differ. |','| Unity not softer/flatter/yellower than Blender match | FAIL | 03_unity_m.png / 03_unity_f.png: darker skin/hair, sharper facial shadows and flatter body lighting remain. Geometry preservation alone does not prove visual fidelity. |','| Independent hair, complete head with hair removed | PASS | Separate body-only FBXs and prefabs have no hair material or hairstyle dependency. Unity deletion check leaves the same body mesh. Full skin-colored scalp has zero open/nonmanifold edges above the forehead; body-only front/back/3q actual Unity proofs are 04_hair_removal_m/f.png and hair-removal-heads.png. |','| Solid opaque separate hair | PASS | Independent head-local hairstyle FBXs and prefabs; hair meshes have zero boundary/nonmanifold edges. Unity URP Lit, surface=0, queue=2000. |','| Metres, foot origin, height / scale | PASS | Source body transforms identity, foot origin. Unity assembled heights Male 1.699999m / Female 1.697157m; body-only 1.650911m / 1.682942m. Root scale=1. |','| 35–50k triangles | PASS | Male 49,368; Female 49,552 including default hair. Source, separate re-imported FBXs and Unity mesh audits agree per part. |','| FBX / normals / face textures | PASS | Separate FBXs All -Z/Y scale 1; Unity meshCompression Off, normals Import, face atlases 2048 sRGB, no Crunch, uncompressed default importer, mipmaps. |','| Prefabs and front/back/3q Unity proofs | PASS | Independent body, independent hairstyle, and assembled prefabs; actual default/bald Unity renders and masks in unity/. |','| No clothes, bandana, rig, animator | PASS | Sources contain Body and Hair objects, no armatures; each FBX contains only one intended mesh. Static prefabs, no Animator. |','| Proof + GATE_RESULTS.md | PASS | This file and named 01/02/03/04 proofs exist. |','','Technical PASS does not make BASE PASS.','','Proof method: independently hand-traced front/back polygon masks from unmodified authority JPEGs. Boundary precision estimated ±2 pixels. Metric is symmetric difference / union, with a 127 alpha/luminance threshold. Native renders translated to plate X centre; no warp or body-specific scale adjustment.','','Topology limit: the complete scalp has zero open or nonmanifold edges. Elsewhere, body meshes retain intentional face/socket openings and overlapping facial components, with 1–2 nonmanifold edges. This is not a claim that the entire body is a single watertight shell. Hair volumes are closed.','','Independent body prefabs:']
for sex in ['Male','Female']:lines.append(str(R/'Unity/Assets/Characters/HeroBase/Bodies'/('HeroBase_'+sex+'_Body.prefab')))
lines+=['','Optional hairstyle prefabs:']
for sex in ['Male','Female']:lines.append(str(R/'Unity/Assets/Characters/HeroBase/Hair'/('Hair_Default_'+sex+'.prefab')))
lines+=['','Assembled preview prefabs:']
for sex in ['Male','Female']:lines.append(str(R/'Unity/Assets/Characters/HeroBase'/('HeroBase_'+sex+'.prefab')))
lines+=['','Blender authoring sources (separate Body and Hair objects):']
for sex in ['Male','Female']:lines.append(str(D/'blender'/('HeroBase_'+sex+'.blend')))
lines+=['','Unity preview scene:',str(R/'Unity/Assets/Characters/HeroBase/HeroBase_Studio.unity'),'','No overall completion claim is made.']
(P/'GATE_RESULTS.md').write_text('\n'.join(lines)+'\n')
(D/'METRICS.md').write_text('# Hero Base current measured candidate\n\nPlate hashes and landmarks are frozen in plate-measurements.json.\n\n| Base | Body triangles | Default hair triangles | Total triangles | With hair height m | Body-only height m |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(metric_rows)+'\n\nSource, independently re-imported FBXs and Unity triangle counts agree.\n\nCurrent silhouette errors: '+ '; '.join(f"{row['sex'].title()} front {row['metrics']['front']['symmetric_difference_over_union']*100:.2f}%, back {row['metrics']['back']['symmetric_difference_over_union']*100:.2f}%" for row in blender['measurements'])+'. These fail the ~5% gate.\n\nEvidence: proof/saved-source-audit.json, proof/unity-mesh-material-audit.txt, proof/unity-import.txt, proof/silhouette-metrics.json, proof/GATE_RESULTS.md.\n')
(D/'SCALE.md').write_text('''# Hero Base static scale and modularity contract

Blender uses metres, body origin at foot midpoint, identity source transforms. FBX uses scale 1, FBX All, -Z forward/Y up. Unity global and file scales are 1. Axis conversion appears on imported mesh children; prefab roots remain identity. Actual default-hair and body-only heights are in METRICS.md.

The complete scalp, ears and face belong to Body_M/Body_F. Hair belongs to independent hairstyle assets. Body-only FBXs and Bodies/ prefabs contain no Hair mesh, material, or hairstyle dependency. Assembled prefabs add an optional HairRoot with a separate nested hairstyle prefab. Remove HairRoot or swap only its child; the body mesh stays unchanged.

Default styles are exported in head-local coordinates. Unity Y-up pivots: male (0,1.4881459,0), female (0,1.5180602,0) metres. New styles must be fitted to their chosen head, around the corresponding pivot; child transform position/rotation zero, scale one. Hair is closed opaque solid volume, URP Lit. Pigment atlases have no baked hair cap or directional lighting.

Current scope is static: no Mixamo, skeleton, Animator, clips or clothes. Future rigging should attach HairRoot to the head transform. It does not require merging the hair into the body.

LOD0 target is 35–50k triangles with default hair. Later hand-authored LOD1 18–25k and LOD2 8–12k are suggestions, not delivered now. Preserve face, scalp and hair forms, and reverify at each LOD. Head albedo is 2048, sRGB, mipmapped, Crunch off, default uncompressed.

A third body needs its own locked plates, complete scalp and measured head pivot. Reuse the separation and attachment contract; fit hair to the head shape. Reverify plate and Unity gates.
''')
(P/'HAIR_REMOVAL_RESULTS.md').write_text('GATE: REMOVABLE HAIR PASS\n\nThe body remains complete when the hairstyle is removed.\n\n| Base | Independently re-imported body FBX | Unity body-only prefab | Scalp topology above forehead | Bald height |\n|---|---|---|---|---|\n'+'\n'.join(removal_rows)+'\n\nBoth source heads have full skin-colored crowns and backs, intact ears, faces and necks. Body-only Unity prefabs were rendered from front, back and three-quarter views and visually inspected. The actual deletion check removes HairRoot and retains the same body mesh. Source, FBX and Unity body triangle counts agree.\n\nProof: 04_hair_removal_m.png, 04_hair_removal_f.png and hair-removal-heads.png. Audits: saved-source-audit.json, unity-mesh-material-audit.txt, unity-import.txt, candidate-manifest.json.\n\nUse Bodies/HeroBase_Male_Body.prefab or Bodies/HeroBase_Female_Body.prefab for the base. Optional default styles live under Hair/. Assembled HeroBase prefabs put only the separate hairstyle under HairRoot. See the Unity README and SCALE.md for fitting coordinates.\n\nThe overall BASE gate remains FAIL for plate silhouette, face/hair fidelity and Unity lighting. This hair-removal pass does not claim that those remaining gates are complete.\n')
for name in ['01_silhouette_overlay_m.png','01_silhouette_overlay_f.png','02_match_m.png','02_match_f.png','03_unity_m.png','03_unity_f.png','04_hair_removal_m.png','04_hair_removal_f.png','hair-removal-heads.png','HAIR_REMOVAL_RESULTS.md','face-comparison.png','GATE_RESULTS.md','BLENDER_STARTUP_DIAGNOSIS.md','candidate-manifest.json','silhouette-metrics.json','unity-comparison-metrics.json','saved-source-audit.json','unity-import.txt','unity-mesh-material-audit.txt']:shutil.copy2(P/name,O/name)
shutil.copy2(R/'Unity/Assets/Characters/HeroBase/README.md',O/'HAIR_CUSTOMIZATION.md')
# Portable authoring exports: four independent FBXs, textures and attachment manifests.
with zipfile.ZipFile(OUT/'HeroBase_Modular_FBX.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for path in sorted((D/'unity_import').rglob('*')):
  if path.is_file() and (path.name.endswith('_Body.fbx') or path.name.startswith('Hair_Default_') or path.suffix=='.json' or path.suffix=='.png'):z.write(path,str(path.relative_to(D/'unity_import')))
 z.write(D/'SCALE.md','SCALE.md');z.write(P/'HAIR_REMOVAL_RESULTS.md','HAIR_REMOVAL_RESULTS.md')
print(json.dumps(results,indent=2));print('REVIEW_WRITTEN',O)
