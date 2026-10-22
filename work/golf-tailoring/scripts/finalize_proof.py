from pathlib import Path
from PIL import Image,ImageDraw
import shutil,json,hashlib
W=Path(__file__).resolve().parents[1];R=W.parents[1];P=R/'ArtDir/hero/kit/golf/tailoring/proof';O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-3/outputs');P.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
for sub in ['verified','native_verified']:
 shutil.copytree(W/'proof'/sub,P/sub,dirs_exist_ok=True)
for sex in ['Male','Female']:
 files=[p for p in sorted((W/'proof/verified').glob(sex+'*.png')) if not any(t in p.name for t in ['Waist','Shoes'])]
 out=Image.new('RGB',(1500,820),'#20242c');d=ImageDraw.Draw(out)
 for i,p in enumerate(files):
  im=Image.open(p);im.thumbnail((300,375));x=(i%5)*300;y=(i//5)*410;out.paste(im,(x+(300-im.width)//2,y+30));d.text((x+8,y+8),p.stem.replace('_',' '),fill='white')
 out.save(P/f'{sex}_poses.png')
canvas=Image.new('RGB',(1600,1180),'#20242c');d=ImageDraw.Draw(canvas)
items=[('native_verified/static_male_body.png','Male outfit',0,0,480,740),('native_verified/static_female_body.png','Female outfit',480,0,480,740),('verified/Male_Waist.png','Fitted male waist',960,0,640,410),('verified/Female_Waist.png','Fitted female waist',960,410,640,410),('verified/Male_Shoes.png','Trouser break and shoe detail',0,740,960,440),('native_verified/static_male_shirt.png','Polo fabric and construction',960,820,640,360)]
for name,label,x,y,w,h in items:
 im=Image.open(W/'proof'/name).convert('RGB');im.thumbnail((w,h-28));canvas.paste(im,(x+(w-im.width)//2,y+28));d.text((x+12,y+8),label,fill='white')
canvas.save(P/'Golf_tailoring_review.png');shutil.copy2(P/'Golf_tailoring_review.png',O/'Golf_tailoring_review.png')
for name in ['identity_checks.json','final_asset_checks.json','promoted.json']:
 shutil.copy2(W/'data'/name,P/name)
for name in ['unity_verified.log','unity_pose_final.log','native_verified.log','uv_check.log']:
 shutil.copy2(W/'logs'/name,P/name)
shutil.copy2(W/'Unity/Assets/Editor/TailoringProof.cs',P/'TailoringProof.cs.txt')
checks=json.loads((W/'data/final_asset_checks.json').read_text());counts={r['sex']:r['kitTriangles'] for r in checks['heroes']}
report=f'''# Golf clothing fit and detail — 6 October 2026

Updated the male and female golf outfits in Unity and the native locker assets. The polo tucks inside the waistband, the belt follows the waist, and the trouser hem has a clean break above the shoe. Polo knit, directional twill, belt leather and shoe panel stitching have stronger material definition.

## Gates

- GATE: Character identity PASS. Original body, face, optional hair and 53-bone rest rig match the source fingerprints. The live golfer restores original sleeve and ankle skin, while a derived golf mesh masks only triangles covered by the polo and waistband. The full original body asset is preserved.
- GATE: Clothing separation PASS. Reviewed rendered address views from four angles and the actual drive backswing, impact and finish (rendered from baked skinned snapshots) from two angles, plus waist and shoe crops. Belt and shirt have separate boundaries; garment sections retain their own materials.
- GATE: Surface mapping PASS. Zero ambiguous UV texels across the eight edited top, bottom and shoe surfaces. Knit, twill and leather use separate fabric identities.
- GATE: Runtime rendering PASS. Isolated Unity 6000.3.24f1 runtime/editor compilation and Metal shader renders completed. Both native locker characters rendered with the regenerated assets and golf-specific surface parameters.
- GATE: Asset consistency PASS. Both native manifests and compressed meshes resolve their maps. Seventeen texture maps retain their existing resolutions and ASTC formats. Kit triangle counts: male {counts['Male']:,}, female {counts['Female']:,}.
- GATE: Full repository test suite FAIL (pre-existing compile blockers). Legacy tests refer to removed GolferView.UsesStandardCharacter, SetFloatingHandsPreview and GolferStyle.Size/Hair/Outfit APIs. These test files were excluded only from the isolated render checkout. Production tests were not changed. No phone build or installation was performed.

## Evidence

[Outfit and detail review](Golf_tailoring_review.png), [male pose sheet](Male_poses.png), [female pose sheet](Female_poses.png). Full-resolution captures are in verified/ and native_verified/. JSON checks and renderer logs are alongside this report. The pose harness is saved as TailoringProof.cs.txt.

Editable source garments are in ../source/. Production assets and four targeted C# changes were applied without committing. promoted.json records exact file hashes; previous versions are backed up under work/golf-tailoring/rollback/production/.
'''
(P/'GATE_RESULTS.md').write_text(report);(O/'GATE_RESULTS.md').write_text(report.replace('(Golf_tailoring_review.png)','(Golf_tailoring_review.png)').replace('[male pose sheet](Male_poses.png), [female pose sheet](Female_poses.png)','male and female pose sheets in the repository proof folder'))
print(P)
