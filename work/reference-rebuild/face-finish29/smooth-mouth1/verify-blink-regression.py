"""Run established source aperture regression against this work-only candidate."""
import pathlib,json
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish29/smooth-mouth1'
source=(R/'work/reference-rebuild/original-blink-finish/verify-stages.py').read_text()
source=source.replace("O=R/'work/reference-rebuild/original-blink-finish'","O=R/'work/reference-rebuild/face-finish29/smooth-mouth1'")
source=source.replace("work/reference-rebuild/original-refinement/{sex}_OriginalSeamEyeMaterial.blend","work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend")
source=source.replace("O/f'{sex}_OriginalSeamBlinkFinish1.blend'","O/f'{sex}_OriginalFaceFinish29Smooth1.blend'")
exec(compile(source,'established-verify-stages.py','exec'))
control=json.loads((R/'work/reference-rebuild/original-blink-finish/blink-finish1-stages-gate.json').read_text())['results']
candidate=json.loads((O/'blink-finish1-stages-gate.json').read_text())['results']
countsExact={sex:all(a['stages']==b['stages'] for a,b in zip(control[sex],candidate[sex])) for sex in ('Male','Female')}
diffs=[]
for sex in ('Male','Female'):
 for a,b in zip(control[sex],candidate[sex]):
  for x,y in zip(a['stages'],b['stages']):
   if x['visibleEyeRays']!=y['visibleEyeRays']:diffs.append({'sex':sex,'clip':a['clip'],'blink':x['blink'],'controlVisibleEyeRays':x['visibleEyeRays'],'candidateVisibleEyeRays':y['visibleEyeRays'],'delta':[v-u for u,v in zip(x['visibleEyeRays'],y['visibleEyeRays'])]})
fullClosed=all(r['stages'][-1]['visibleEyeRays']==[0,0] for sex in candidate for r in candidate[sex]);assert fullClosed
(O/'blink-regression-gate.json').write_text(json.dumps({'gate':'FULL CLOSURE PASS; POSED OCCLUSION CHANGES REQUIRE ACTUAL REVIEW' if diffs else 'PASS','control':'accepted OriginalSeamBlinkFinish1','posedApertureStagesExact':countsExact,'differences':diffs,'clips':['Ready','Serve','Forehand','IntroWave'],'stages':[0,.25,.5,.75,1],'raysPerAperturePerStage':12221,'fullBlinkVisibleEyeRays':0,'fullClosureAllEightClips':fullClosed,'actualUnityArtGate':'PENDING'},indent=2)+'\n')
print('BLINK SOURCE REGRESSION: closure',fullClosed,'countsExact',countsExact,'diffs',diffs,flush=True)
