from pathlib import Path
import subprocess,sys,uuid
root=Path.cwd(); scratch=root/'work/golf-motion-fix'; moved=[]
# These three pre-existing tests refer to removed legacy character APIs and prevent any suite compiling.
try:
 for name in ['NativeSessionTests.cs','PlayerBaseTests.cs','StandardCharacterGameplayTests.cs']:
  p=root/'Unity/Assets/Tests/PlayMode'/name
  target=scratch/(name+'.saved')
  p.rename(target);moved.append((p,target))
  meta=Path(str(p)+'.meta'); backup=Path(str(target)+'.meta')
  if meta.exists():meta.rename(backup);moved.append((meta,backup))
 for mode,filters in [('EditMode','GolfArcade.Tests.MotionSwingDetectorTests;GolfArcade.Tests.NativeBridgeTests'),('PlayMode','GolfArcade.PlayTests.GolfMotionReadyTests')]:
  log=scratch/(mode+'.log'); result=scratch/(mode+'.xml')
  cmd=['/Applications/Unity/Hub/Editor/6000.3.24f1/Unity.app/Contents/MacOS/Unity','-batchmode','-projectPath',str(root/'Unity'),'-runTests','-testPlatform',mode,'-testFilter',filters,'-testResults',str(result),'-logFile',str(log)]
  if mode=='EditMode':cmd+=['-nographics']
  code=subprocess.call(cmd)
  print(mode,'exit',code,flush=True)
  if code:sys.exit(code)
finally:
 for p,target in moved:
  if target.exists():target.rename(p)
 print('Restored all three legacy test files.',flush=True)
