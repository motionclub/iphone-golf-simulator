from pathlib import Path
import shutil,json,numpy as np,subprocess,hashlib
r=Path.cwd()/'work/face-match';a=r/'after';out=Path('/Users/adnanyonathan/Documents/Codex/2026-10-08/op/outputs/face-match')
subprocess.run(['python3',str(r/'tools/ear_review.py'),'after'],check=True)
proof=a/'proof';audit={}
for sex in ['male','female']:
 before=np.genfromtxt(r/'ear-before/raw'/f'{sex}_head.csv',delimiter=',',names=True)
 after=np.genfromtxt(a/'raw'/f'{sex}_head.csv',delimiter=',',names=True)
 p=np.stack([before[x] for x in ['x','y','z']],1);q=np.stack([after[x] for x in ['x','y','z']],1)
 delta=np.linalg.norm(p-q,axis=1);changed=delta>.00005
 ear=(np.abs(p[:,0])>.068)&(p[:,1]>-.105)&(p[:,1]<.060)&(p[:,2]<-.025)
 audit[sex]={'vertex_count_before':len(p),'vertex_count_after':len(q),'vertices_moved_over_0_05mm':int(changed.sum()),'max_displacement_mm':float(delta.max()*1000),'max_outside_ear_region_mm':float(delta[~ear].max()*1000),'changed_bounds_min_m':p[changed].min(0).tolist(),'changed_bounds_max_m':p[changed].max(0).tolist(),'unchanged_triangle_indices':all((r/'ear-before/raw'/f.name).read_bytes()==f.read_bytes() for f in (a/'raw').glob(f'{sex}_head_[0-9]*.txt'))}
(proof/'ear-geometry.json').write_text(json.dumps(audit,indent=2))
for f in proof.glob('*ear*'):shutil.copy2(f,out/'proof'/f.name)
previous=out/'ear-before';previous.mkdir(exist_ok=True)
for f in (r/'ear-before').glob('*_sheet.png'):shutil.copy2(f,previous/f.name)
report=out/'REPORT.md';text=report.read_text();intro='''Latest pass focuses on **both ears only**. Male ears face forward more and sit lower while preserving the authored contour; female ears have a recessed inner bowl, a small cartilage fold and tragus, a rounder upper outline, and an extended tapered lobe. Local normal filtering preserves the folds, and the female ear warmth is registered to the actual ear location. Only `HeroFaceReferenceFit.cs`, `HeroSkinNormals.cs`, and `HeroFaceSkin.shader` are restaged from this pass. The same 16 face/head paths remain staged.

A parallel edit introduced `TotalTotalLength` in `TennisPresentation.cs`, blocking compilation. This pass corrected that single token to the existing `TotalLength` symbol and left it unstaged. A temporary test compatibility edit was fully reverted after the parallel refactor restored its public timing constants. Surrounding presentation and test changes remain intact.

[Male ear close-ups](PROOF/male_ears.png) · [Female ear close-ups](PROOF/female_ears.png) · [Ear geometry audit](PROOF/ear-geometry.json)

The references still have smoother, more precisely defined cartilage. The male attachment crease and female rim remain coarser at close inspection; this pass does not claim an exact ear match. Both debug flags remain unset, and the court lighting and camera framing are unchanged.

'''.replace('PROOF',str(out/'proof'))
text=text.replace('# Face reference matching — staged candidate\n\n','# Face reference matching — staged candidate\n\n'+intro,1).replace('This continuation adds small rounded cheekbone volumes','The preceding face pass added small rounded cheekbone volumes');report.write_text(text);(a/'REPORT.md').write_text(text)
review=out/'review.html';page=review.read_text();start=page.index('<h2>');ears=''
for sex in ['male','female']:
 ears+=f'<h2>{sex.title()} ears — reference / before / current</h2><img src="proof/{sex}_ears.png"><details><summary>Full face context</summary><img src="proof/{sex}_ear_progress.png"></details>'
page=page[:start]+ears+'<h2>Full face comparisons and previous work</h2>'+page[start:];review.write_text(page)
print(json.dumps(audit,indent=2))
