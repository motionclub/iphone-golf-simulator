import sys,pathlib
script=pathlib.Path(__file__).with_name('render_hand_exact_camera.py')
for sex in ('Male','Female'):
 for weight in (0,.25,.5,.75,1):
  sys.argv=['blender','--','--fair','--series','--weight='+str(weight),sex]
  exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
