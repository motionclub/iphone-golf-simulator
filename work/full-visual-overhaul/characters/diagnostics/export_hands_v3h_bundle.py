import pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[4]
for sex in ('Male','Female'):
 for task in ('export_hand_surface_v3h.py','export_hand_pose_contract_v3h.py','export_hand_normals_v3h.py'):
  result=subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','4','--python',str(R/'work/full-visual-overhaul/characters/diagnostics'/task),'--',sex],cwd=R)
  if result.returncode:raise SystemExit(result.returncode)
