"""Promote the reviewed World22 candidate only; root owns actual Unity proof."""
from pathlib import Path
import hashlib,json,shutil

stage=Path(__file__).resolve().parent
repo=stage.parents[3]
baseline=json.loads((stage/'baseline.json').read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
# Validate the entire snapshot before the first mutation; preserve peer/root edits.
for relative,expected in baseline.items():
    target=repo/relative;candidate=stage/target.name
    if target.read_bytes()!=candidate.read_bytes() and sha(target)!=expected:
        raise ValueError('Live source changed since staging: '+relative)
for relative in baseline:
    shutil.copyfile(stage/Path(relative).name,repo/relative)
assets=[]
for folder,name,manifest,canonical in [
 ('palm','TennisCoconutPalm','palm-manifest.json','botany'),
 ('canopy','TennisCanopy','canopy-manifest.json','botany'),
 ('clubhouse','TennisClubhouse','clubhouse-manifest.json','architecture')]:
    target=repo/'Unity/Assets/Resources/Tennis/Premium'/(name+'.fbx')
    if not target.with_suffix('.fbx.meta').exists():
        raise ValueError('Stable resource meta missing: '+str(target))
    shutil.copyfile(stage/folder/(name+'.fbx'),target)
    source=repo/'ArtDir/tennis/venues'/canonical/'source';source.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(stage/folder/(name+'.blend'),source/(name+'.blend'))
    shutil.copyfile(stage/folder/manifest,source/(name+'-manifest.json'))
    assets.extend([target,Path(str(target)+'.meta'),source/(name+'.blend'),source/(name+'-manifest.json')])
source_tools=[
 'ArtDir/tennis/venues/botany/build-coconut-palm.py',
 'ArtDir/tennis/venues/botany/render-coconut-palm.py',
 'ArtDir/tennis/venues/botany/botanical_primitives.py',
 'ArtDir/tennis/venues/botany/build-resort-canopy.py',
 'ArtDir/tennis/venues/botany/render-canopy.py',
 'ArtDir/tennis/venues/architecture/build-clubhouse.py',
 'ArtDir/tennis/venues/architecture/render-clubhouse.py']
paths=[*(repo/p for p in baseline),*assets,*(repo/p for p in source_tools)]
manifest={
 'checkpoint':'World22 coherent primary-form candidate',
 'status':'source reviewed candidate installed; actual Unity compilation, art and counters pending',
 'invariants':[
  'authoritative court/net/line/collision geometry and contact/toss/scoring untouched',
  'no added decorative collider; live court/runoff corridor remains clear',
  'root coastal sky block retained exactly; shared golf source/assets untouched',
  'quality settings, shadow cascades/resolution/distance untouched',
  'existing gameplay, postcard9 and reference14 capture cameras untouched;16/17/18 are review-only'],
 'changes':[
  'distant resort cone replaced by lower asymmetric peak cluster at600m with continuous lighting normals and graded geology/haze',
  'left portico brought closer outside runoff; rear L-return frames ocean without blocking centre',
  'existing coconut source keeps counts/schema but overlapping leaflets form fuller connected arches',
  'same-position broadleaf canopies have smoother crown shoulders and normalized pole topology at near/far',
  'clubhouse retains footprint but gains shaped terracotta tiles/eave joinery, unified nonoverlapping arched glass and bounded sky reflection',
  'two rooftop landmark towers replace box silhouettes with rounded stepped curtain walls, projecting cornices, bronze reveals and planted terraces',
  'continuous crater shoulder gains six asymmetric broad buttresses; small hovering flat plates become fewer embedded smooth outcrops',
  'review cameras16A-D test higher horizon/hero placement;17/18 isolate actual clubhouse facade/roof'],
 'sources':{
   'palm':json.loads((stage/'palm/palm-manifest.json').read_text()),
   'canopy':json.loads((stage/'canopy/canopy-manifest.json').read_text()),
   'clubhouse':json.loads((stage/'clubhouse/clubhouse-manifest.json').read_text())},
 'files':[{'path':str(p.relative_to(repo)),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths]
}
proof=repo/'proof/full-visual-overhaul/tennis/world22-installed-manifest.json'
proof.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'installed':list(baseline)+[str(p.relative_to(repo)) for p in assets if p.suffix=='.fbx'],'manifest':str(proof)},indent=2))
