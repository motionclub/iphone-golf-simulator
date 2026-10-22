import pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[4]
for sex in ('Male','Female'):
 for weight in (0,.25,.5,.75,1):
  result=subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','4','--python',str(R/'work/full-visual-overhaul/characters/diagnostics/render_hand_multistage_v3h.py'),'--','--stages','--series','--weight='+str(weight),sex],cwd=R)
  if result.returncode:raise SystemExit(result.returncode)
