import os,sys,json,subprocess,pathlib,shutil
r=pathlib.Path(__file__).resolve().parents[3]
stage=sys.argv[1];dest=r/'work/face-match'/stage;dest.mkdir(parents=True,exist_ok=True)
for file in ['Unity/Assets/Scripts/Tennis/HeroFaceReferenceFit.cs','Unity/Assets/Resources/Tennis/Shaders/HeroFaceSkin.shader','Unity/Assets/Scripts/Tennis/HeroSkinNormals.cs']:
 p=r/file
 if p.exists():shutil.copy2(p,dest/p.name)
env=os.environ.copy()
for key in ['VISUAL_CHARACTER_SKIN_POLISH','VISUAL_BLINK_NORMAL_FIELD']:env.pop(key,None)
job={'name':'face-match-'+stage,'method':'GolfArcade.EditorTools.HeroFaceMatchCapture.Run','env':{'FACE_MATCH_OUT':str(dest/'raw'),'HERO_VENUE':'resort'}}
if '--film' in sys.argv:job['env']['FACE_MATCH_FILM']='1'
queue=dest/'queue.json';queue.write_text(json.dumps([job],indent=2))
code=subprocess.call([sys.executable,str(r/'work/full-visual-overhaul/capture_queue.py'),str(queue)],cwd=r,env=env)
if code==0:subprocess.run([sys.executable,str(r/'work/face-match/tools/sheets.py'),stage],cwd=r,check=True)
sys.exit(code)
