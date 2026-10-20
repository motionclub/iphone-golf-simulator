from pathlib import Path
import json,shutil,hashlib
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/full-visual-overhaul/golf';P=R/'proof/full-visual-overhaul/golf'
j=json.loads((P/'gallery-hero3-source-manifest.json').read_text());assert all(v['far_triangles']<=8000 for v in j['variants'])
fbx=R/'Unity/Assets/Resources/Course/Resort/GolfGallerySpectators.fbx'
backup=W/'GolfGallerySpectators-GalleryHero2.fbx'
if not backup.exists():shutil.copy2(fbx,backup)
shutil.copy2(W/'GolfGalleryHero3.fbx',fbx)
files=[fbx,R/'Unity/Assets/Scripts/Game/Gallery.cs',R/'Unity/Assets/Scripts/Game/GolfGalleryPresentation.cs',R/'Unity/Assets/Editor/GolfCourseStandardCapture.cs',R/'Unity/Assets/Editor/GolfGalleryProof.cs']
manifest={'checkpoint':21,'worldSource':18,'audience':'GalleryHero3 installed for actual near/far/cheer acceptance; not yet runtime certified','sourceBudget':[(v['variant'],v['triangles'],v['far_triangles']) for v in j['variants']],'repairs':['Complete real head and central neck preserved before covered-skin filtering; lateral clavicles remain torso-owned.','Actual fitted shirt armhole contours form a shallow overlapping shoulder closure.','Only closed lower garment exteriors are reduced; near shorts/skirt consolidate their volume before reduction.','Shoe and sock exteriors are independently capped, retaining their physical dimensions.'],'unchanged':['Seven original placements, lie/ground rejection, RNG schedule, Count/Centre/Rope/Cheer API.','Four rigid pieces, no bones/skinning/animator/colliders; source2 runtime and .25 near/far LOD threshold.','World18 scenery and canonical physics source.'],'files':[{'path':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files]}
(P/'checkpoint21-gallery3-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
