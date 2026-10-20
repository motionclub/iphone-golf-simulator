from pathlib import Path
import shutil,json,hashlib
w=Path('work/character-female33');native=Path('work/character-finish32/native')
out=Path('/Users/adnanyonathan/Documents/Codex/2026-10-08/open/outputs/character-beautification');stage=out/'stage-02-female-clothes';repoProof=Path('ArtDir/hero/clothing/tailored-2026-10-08/proof');repoProof.mkdir(parents=True,exist_ok=True)
queue=json.loads((w/'finished-queue.json.results.json').read_text());lod=json.loads((w/'lod-smoke-queue.json.results.json').read_text());assert all(x['exit']==0 for x in queue+lod)
full=json.loads((w/'native-finished-full/native-polo-proof.json').read_text());distance=json.loads((w/'native-finished-distance/native-polo-proof.json').read_text());nativeProof=full+distance
assert all(g['maxPositionErrorMm']<.2 for x in nativeProof for g in x['garments'])
files={
'female-outfit-native.png':w/'native-finished-full/MatchHero_Female_wave.png',
'female-distance-native.png':w/'native-finished-distance/MatchHero_Female_Distance_wave.png',
'female-serve-native.png':w/'native-finished-full/MatchHero_Female_serve.png',
'unity-adoption-proof.json':w/'unity-adoption-proof.json',
'native-adoption-proof.json':w/'native-adoption-proof.json',
'unity-verification.json':w/'finished-queue.json.results.json',
'lod-verification.json':w/'lod-smoke-queue.json.results.json',
'fixture-update-proof.json':w/'fixture-proof/merge-report.json',
'native-full-merge-proof.json':native/'merged/MatchHero_Female-merge-proof.json',
'native-distance-merge-proof.json':native/'merged/MatchHero_Female_Distance-merge-proof.json'}
for name,src in files.items():shutil.copy2(src,stage/name)
(stage/'native-parity-proof.json').write_text(json.dumps(nativeProof,indent=2))
text='''# GATE_RESULTS — tailored tennis clothing

GATE: FEMALE POLO AND SKIRT PASS

Completed the accepted male polo transfer to the female polo and skirt. Work stops here, as requested. Clothing colors remain customizable; reference hues are not a fidelity requirement.

| Gate | Result | Evidence |
| --- | --- | --- |
| Shared polo construction | PASS | Female reuses the accepted male collar, two-button placket, cuffs, neutral weave and fixed-morph deformation system. Female sleeve clearance and waist overlap are fitted to her existing skeleton. |
| Skirt construction | PASS | Defined pleats, eased outline, waistband and turned hem; original skirt bindings and undershorts retained. Light, navy and teal swatches captured. |
| Motion sampling | PASS | Full garment: 33 clip slots × 5 samples, front/rear. Distance garment: serve, wave, scuba and pushups × 9 samples, front/rear. Selected compressed, raised-arm and rear views visually inspected. No compile or shader errors. |
| Color customization | PASS | Existing palette controls and Shirt/Shorts/ShortsBand roles retained; neutral material detail works with light, dark and saturated swatches. |
| Female detail transition | PASS | Default-enabled runtime, Full → Distance → Full: exact return of skinned vertices, finite morph results and correct mesh selection. |
| Native female polo parity | PASS | 3,764,700 vertex comparisons across Full/Distance exports; maximum error 0.001708 mm against independent Unity samples. |
| Native female skirt parity | PASS | 2,583,360 vertex comparisons across Full/Distance exports; maximum error 0.000455 mm. |
| Native appearance | PASS | Actual SceneKit/Metal snapshots of ready, wave, serve, scuba and pushups for both detail levels. No magenta fallback. |
| Adoption | PASS | Unity clothing code/assets installed and enabled by default; all 46 destination hashes verified. Thirty native female files match the verified garment-only merged packages exactly. |
| Preservation | PASS | Native original buffer prefixes, all nongarment manifest parts, all 53 bones and original animation/rigid tracks retained. Bone animation difference is zero. No map/light/camera/body/head/skin/animation-source files adopted. |
| Fixtures | PASS | Updated 540 changed-garment samples in four existing fixtures; all 3,780 nongarment samples preserved. |

Male polo native parity already passed: 2,978,280 vertex comparisons, maximum 0.001791 mm. Its accepted shape was retained. Male full/distance renders were verified in the preceding stage; this final automatic transition check specifically covers the female.

Coverage: the male profile reconciles eight stale interior triangles among 7,072 faces with the same 282 boundary edges. Female face coverage positions remain unchanged; only the expected top vertex count was updated for the new garment. No covered area was expanded.

The fixed female basis uses 94 shapes. Its approximation over the fitting poses is below 0.356 mm. Full polo has 22,887 vertices; distance polo 18,943. The skirt has 14,352 imported vertices and uses the same silhouette at both levels.

## Proof and limits

Images are unedited captures from the actual Unity or native render paths. Studio capture settings are diagnostic and do not change the production maps, lighting, post-processing or cameras. These checks validate clothes, deformation, customization, export and default garment selection. Physical-iPhone frame rate and a fresh end-to-end iOS app launch were not measured in this pass.

The auxiliary Unity check initially omitted the LOD component normally created by Awake; its harness was corrected. A subsequent editor process crashed in native texture serialization; a fresh female-only run passed. Final queue and native parity results are recorded alongside this file.

![Female outfit in Unity](female-outfit-unity.png)

![Skirt detail in a customizable dark color](female-skirt-detail.png)

![Actual native outfit](female-outfit-native.png)
'''
(stage/'GATE_RESULTS.md').write_text(text)
for p in stage.iterdir():
 if p.is_file():shutil.copy2(p,repoProof/p.name)
plan=out/'plan.md';s=plan.read_text().replace('Shoes and socks remain part of the outfit pass.','This pass includes only the accepted male polo, female polo and female skirt. Shoes, socks and other garments are deferred.');s=s.split('## Current status')[0]+'''## Current status

**Complete — stopped after the female polo and skirt.** Both use the accepted male clothing system, adapted to her fit. Colors remain customizable. The approved male polo is retained; Unity and native garment assets are adopted.

Female full and distance renders, color swatches, 33-clip motion sampling, native vertex parity and the default Full → Distance → Full transition passed. The native packages preserve all existing nongarment parts and animation tracks. Physical-iPhone performance and a fresh complete app launch were not measured.

See [GATE_RESULTS.md](stage-02-female-clothes/GATE_RESULTS.md) and its actual Unity/native images. No subsequent clothing, character or map stage is active.
''';plan.write_text(s)
print('Final clothing proof saved:',stage/'GATE_RESULTS.md')
