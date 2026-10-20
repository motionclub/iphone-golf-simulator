from pathlib import Path
import json,shutil,hashlib
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');W=R/'work/full-visual-overhaul/golf';P=R/'proof/full-visual-overhaul/golf'
j=json.loads((P/'gallery-hero2-source-manifest.json').read_text());assert all(v['far_triangles']<=8000 for v in j['variants'])
fbx=R/'Unity/Assets/Resources/Course/Resort/GolfGallerySpectators.fbx';runtime=R/'Unity/Assets/Scripts/Game/GolfGalleryPresentation.cs';capture=R/'Unity/Assets/Editor/GolfCourseStandardCapture.cs';fixture=R/'Unity/Assets/Editor/GolfGalleryProof.cs'
for src,label in [(fbx,'GolfGallerySpectators-Gallery1.fbx'),(runtime,'GolfGalleryPresentation-Gallery1.cs')]:
 target=W/label
 if not target.exists():shutil.copy2(src,target)
shutil.copy2(W/'GolfGalleryHero2.fbx',fbx);shutil.copy2(W/'GolfGalleryPresentation-Hero2.cs',runtime)
# Rebase only the diagnostic bounds block, preserving any parent's other edits.
s=capture.read_text();new=(W/'GolfCourseStandardCapture-Meadow.cs').read_text();start=new.index('                if(h.Number is >=1 and <=3)\n                {\n                    // Procedural Meadow');end=new.index('                float low=',start);block=new[start:end]
old='                foreach(var collider in view.GetComponentsInChildren<MeshCollider>())\n                    if(collider.sharedMesh && collider.bounds.size.x<2000 && collider.bounds.size.z<2000)bounds.Encapsulate(collider.bounds);\n'
if block not in s:assert old in s;s=s.replace(old,block,1);capture.write_text(s)
# Capture three actual LOD viewing distances and record both source budgets.
s=fixture.read_text().replace('" triangles="+fan.MeshTriangles','" nearTriangles="+fan.MeshTriangles+" farTriangles="+fan.DistantTriangles')
needle='                Shot(cam,Path.Combine(output,"fan_"+i+"_face.png"),fan.Head.position+fan.transform.forward*1.05f+Vector3.up*.11f,fan.Head.position+Vector3.up*.14f,640,640);'
addition=needle+'\n                foreach(float distance in new[]{3.4f,8f,18f})Shot(cam,Path.Combine(output,"fan_"+i+"_distance_"+distance.ToString("0.0",System.Globalization.CultureInfo.InvariantCulture)+".png"),fan.transform.position+fan.transform.forward*distance+Vector3.up*1.12f,fan.transform.position+Vector3.up*.95f,640,900);'
if '"_distance_"' not in s:assert needle in s;s=s.replace(needle,addition);fixture.write_text(s)
files=[fbx,runtime,capture,fixture];manifest={'checkpoint':20,'worldSource':18,'audience':'GalleryHero2 installed; actual Unity acceptance/cost pending','sourceBudget':[(v['variant'],v['triangles'],v['far_triangles']) for v in j['variants']],'lod':{'screenThreshold':.25,'sizeYards':1.75,'farAtGameplayDistanceYards':'~6–8 at48–60deg FOV'},'files':[{'path':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in files]}
(P/'checkpoint20-gallery2-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
