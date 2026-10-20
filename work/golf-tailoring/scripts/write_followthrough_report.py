from pathlib import Path
import json,shutil,hashlib
W=Path(__file__).resolve().parents[1];R=W.parents[1];O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-3/outputs');P=R/'ArtDir/hero/kit/golf/tailoring/proof/followthrough';P.mkdir(parents=True,exist_ok=True)
asset=json.loads((W/'data/final_asset_checks.json').read_text());fit=json.loads((W/'data/followthrough_bottoms.json').read_text());changes=json.loads((W/'data/followthrough_promoted.json').read_text())
for row in changes:assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['after']
for f in ['motion_checks.txt','contact.png']:
 shutil.copy2(W/'proof/followthrough'/f,P/f)
for name in ['Male_Address_270','Male_Finish_90','Female_Address_270','Female_Finish_90','Female_Finish_270','Female_Coverage_Address_270','Female_Coverage_Impact_270','Female_Coverage_Finish_270']:
 shutil.copy2(W/'proof/followthrough/stills'/f'{name}.png',P/f'{name}.png')
for name in ['identity_checks','final_asset_checks','uv_check','followthrough_bottoms','followthrough_promoted']:
 shutil.copy2(W/'data'/f'{name}.json',P/f'{name}.json')
for name in ['Golf_swing_corrected.gif','Golf_swing_corrected.mp4']:shutil.copy2(O/name,P/name)
for name in ['refine_bottoms_followthrough.py','export_golf_kit.py','followthrough_final.sh','promote_followthrough.py']:shutil.copy2(W/'scripts'/name,P/name)
shutil.copy2(W/'Unity/Assets/Editor/FollowThroughChecks.cs',P/'FollowThroughChecks.cs')
report=f"""# Golf clothing and drive follow-through — 6 October 2026

Applied the verified candidate to the existing golf simulator working tree. The driver finishes behind the head and across the upper back. The male crotch uses the same continuous trouser fabric. The female skirt is longer, follows the thighs as one continuous shell, and has opaque, separately skinned shorts with turned hems beneath it.

Motion references: [PGA TOUR — Rory McIlroy slow motion](https://www.youtube.com/watch?v=BmRL2K-rz0Q) and [TaylorMade — Nelly Korda driver slow motion](https://www.youtube.com/watch?v=xDE9bgwaeqc).

- GATE: Drive finish PASS. 209 samples at 60 Hz per golfer; unchanged bones through 2.50 seconds, after the authored 2.30-second impact. Both hands retain grip contact. Measured results below.
- GATE: Male crotch PASS. Removed the central pocket-lining overlap, smoothed {fit['maleCrotchSmoothedVertices']} garment vertices, and faded the obsolete crotch corrective deltas. The centre uses the same fabric ID and material as the rest of the trousers.
- GATE: Female coverage PASS. Skirt rest hem is {fit['femaleSkirtHemMetres']:.3f} m, down from 0.793 m; shorts hem is {fit['femaleShortsHemMetres']:.3f} m, down from 0.816 m. Low-angle address, backswing, impact and finish views retain opaque coverage. The skirt's lower rings share both thigh transforms to avoid a split drape.
- GATE: Motion preview PASS. Actual Unity Drive animation, runtime follow-through/head clearance, garment correctives and materials; 105 frames per golfer at 30 fps. Meshes baked at each frame to avoid stale editor skinning. Entire club trajectory remains inside the preview frame.
- GATE: Locked identity PASS. Original body, face, optional female hair, and 53-bone rest rig hashes are unchanged. Clothing-covered triangles are omitted only in derived render-body meshes; full original sources remain intact.
- GATE: UV and native assets PASS. Zero ambiguous texels in all checked clothing surfaces; regenerated PNG/KTX maps and native clothing exports. Unity runtime/editor compile and Metal renders pass.
- GATE: Production parity PASS. All {len(changes)} applied files match their inspected candidate hashes. Changes remain uncommitted; previous versions are backed up under work/golf-tailoring/rollback/followthrough-baseline/production.
- GATE: Full repository test suite BLOCKED by existing test/API mismatches (UsesStandardCharacter, SetFloatingHandsPreview, and GolferStyle.Size/Hair/Outfit). Tests were isolated only in the review clone; production tests were not altered. No device build was performed for this visual revision.

{(W/'proof/followthrough/motion_checks.txt').read_text()}

The polo retains outward-facing shoulder fabric during export, uses continuous shoulder skin weights, and masks only covered skin in the derived body. Original garment construction and fitted belt remain in the editable Blender sources.

![Final swing](Golf_swing_corrected.gif)

[HD swing video](Golf_swing_corrected.mp4)
"""
(P/'GATE_RESULTS.md').write_text(report);(O/'Followthrough_review.md').write_text(report);shutil.copy2(P/'contact.png',O/'Golf_swing_review.png');print('REPORT',P,'files',len(changes))
