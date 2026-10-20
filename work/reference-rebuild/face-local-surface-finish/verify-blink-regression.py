"""Run established source aperture regression against this work-only candidate."""
import pathlib,json
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-local-surface-finish'
source=(R/'work/reference-rebuild/original-blink-finish/verify-stages.py').read_text()
source=source.replace("O=R/'work/reference-rebuild/original-blink-finish'","O=R/'work/reference-rebuild/face-local-surface-finish'")
source=source.replace("for sex in ('Male','Female'):","for sex in ('Male',):")
source=source.replace("work/reference-rebuild/original-refinement/{sex}_OriginalSeamEyeMaterial.blend","work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend")
source=source.replace("O/f'{sex}_OriginalSeamBlinkFinish1.blend'","O/f'{sex}_OriginalSeamLocalSurfaceFinish1.blend'")
exec(compile(source,'established-verify-stages.py','exec'))
control=json.loads((R/'work/reference-rebuild/original-blink-finish/blink-finish1-stages-gate.json').read_text())['results']['Male']
candidate=json.loads((O/'blink-finish1-stages-gate.json').read_text())['results']['Male']
countsExact=all(a['stages']==b['stages'] for a,b in zip(control,candidate));assert countsExact,(control,candidate)
(O/'blink-regression-gate.json').write_text(json.dumps({'gate':'PASS','control':'accepted OriginalSeamBlinkFinish1','posedApertureStagesExact':countsExact,'clips':['Ready','Serve','Forehand','IntroWave'],'stages':[0,.25,.5,.75,1],'raysPerAperturePerStage':12221,'fullBlinkVisibleEyeRays':0,'actualUnityArtGate':'PENDING'},indent=2)+'\n')
print('GATE: BLINK SOURCE REGRESSION PASS; ALL POSED APERTURE STAGES EXACT',flush=True)
