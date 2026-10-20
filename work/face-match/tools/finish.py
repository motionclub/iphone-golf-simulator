from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,json,csv,hashlib,re
repo=Path.cwd();r=repo/'work/face-match';after=r/'after';proof=after/'proof';proof.mkdir(exist_ok=True)
subprocess.run(['python3',str(r/'tools/proof.py'),'after'],check=True)
ffmpeg='/Users/adnanyonathan/.cache/uv/archive-v0/FAqiNt1vNS62llSz/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18);motion={};videos={}
for sex in ['male','female']:
 clip=after/f'{sex}_idle_3s.mp4'
 subprocess.run([ffmpeg,'-y','-loglevel','error','-framerate','30','-i',str(after/'raw'/f'{sex}_idle/%04d.png'),'-frames:v','90','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(clip)],check=True)
 v=subprocess.run([ffmpeg,'-i',str(clip),'-f','null','-'],capture_output=True,text=True)
 videos[sex]={'decode_exit':v.returncode,'duration':re.search(r'Duration: ([0-9:.]+)',v.stderr).group(1),'last_frame_count':re.findall(r'frame=\s*(\d+)',v.stderr)[-1]}
 board=Image.new('RGB',(1200,1488),'#ece8df');draw=ImageDraw.Draw(board)
 for col,frame in enumerate([0,25,27,29,60,89]):
  im=Image.open(after/'raw'/f'{sex}_idle/{frame:04}.png');x=(col%3)*400;y=(col//3)*744
  board.paste(im.resize((400,469),Image.Resampling.LANCZOS),(x,y+32));draw.text((x+8,y+8),f'{sex} / frame {frame} / {frame/30:.3f}s',fill='black',font=font)
  board.paste(im.crop((150,270,450,350)).resize((400,107),Image.Resampling.LANCZOS),(x,y+510))
  board.paste(im.crop((175,475,430,548)).resize((400,115),Image.Resampling.LANCZOS),(x,y+625))
 board.save(proof/f'{sex}_motion_contact.png')
 rows=list(csv.DictReader((after/'raw'/f'{sex}_idle/trace.csv').open()))
 motion[sex]={'frames':len(rows),'frame_rate':30,'duration_seconds':3,'actual_max_shape_weights':{k:max(float(row[k]) for row in rows) for k in ['bodyFullBlink','bodyHalfBlink','faceGazeRight','faceGazeLeft','faceBrowUp','faceBrowDown']},'method':'90 deterministic Idle samples exercising the production deformation path, not spontaneous scheduling.'}
 old=Image.open(r/'pass1-after'/f'{sex}_front_sheet.png');new=Image.open(after/f'{sex}_front_sheet.png')
 progress=Image.new('RGB',(1635,750),'#ece8df');progress.paste(new.crop((0,0,545,750)),(0,0));progress.paste(old.crop((545,0,1090,750)),(545,0));progress.paste(new.crop((545,0,1090,750)),(1090,0));d=ImageDraw.Draw(progress)
 for i,label in enumerate(['LOCKED REFERENCE','PREVIOUS CANDIDATE','CURRENT CANDIDATE']):
  d.rectangle((i*545,0,(i+1)*545,50),fill='#ece8df');d.text((i*545+20,20),sex.upper()+' / '+label,fill='black',font=font)
 progress.save(proof/f'{sex}_progress.png')
(proof/'motion.json').write_text(json.dumps(motion,indent=2));(proof/'video-verification.json').write_text(json.dumps(videos,indent=2))
def errors(p):return [re.sub(r'\(\d+,\d+\)','(line)',line.strip()) for line in p.read_text().splitlines() if re.search(r'error CS\d+',line)]
baseline=r/'ear-check/baseline-check.log'
b,a=errors(baseline),errors(after/'check.log')
def failures(p):return sorted(line for line in p.read_text().splitlines() if line.startswith('FAIL '))
bf,af=failures(baseline),failures(after/'check.log')
comparison={'baseline_error_count':len(b),'after_error_count':len(a),'new_errors':sorted(set(a)-set(b)),'removed_errors':sorted(set(b)-set(a)),'after_errors':a,'baseline_test_failures':bf,'after_test_failures':af,'new_test_failures':sorted(set(af)-set(bf)),'baseline_test_summary':baseline.read_text().splitlines()[-1],'after_test_summary':(after/'check.log').read_text().splitlines()[-1],'script_exit':1,'command':'Unity/Tools/check.sh (zsh shebang)','baseline_method':'Same updated check script and current shared C# sources in a scratch project; only the two ear C# files substituted with their preserved pre-ear versions. Live project files untouched.'}
(r/'proof/check-comparison.json').write_text(json.dumps(comparison,indent=2))
source=json.loads((repo/'work/full-visual-overhaul/face-match-after.source.json').read_text());staged=subprocess.check_output(['git','diff','--cached','--name-only'],text=True).splitlines();(r/'proof/staged-files.txt').write_text('\n'.join(staged)+'\n')
log=(repo/'work/full-visual-overhaul/face-match-after.log').read_text();invariants=[x for x in log.splitlines() if '[HeroFaceReferenceFit]' in x and 'moved=' in x];(proof/'geometry.txt').write_text('\n'.join(invariants)+'\n')
verification={'staged_files':staged,'only_face_files':all(any(x in p for x in ['HeroFaceMatchCapture','HeroFaceSkin','HeroBlinkNormalField','HeroFaceReferenceFit','HeroHeadSurface','HeroOriginalSeamAnatomy','HeroSkinNormals','MatchHeroFacePerformance']) for p in staged),'staged_source_matches_final_capture':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest()==source[p] for p in staged if p in source},'unity_capture':json.loads((after/'queue.json.results.json').read_text())}
(r/'proof/source-verification.json').write_text(json.dumps(verification,indent=2))
old=json.loads((r/'pass1-after/proof/skin-patches.json').read_text())['measurements'];new=json.loads((proof/'skin-patches.json').read_text())['measurements']
result={sex:{'previous_mean_cheek_deltaE76':round(sum(x['deltaE76'] for x in old if x['hero']==sex and 'cheek' in x['patch'])/2,2),'current_mean_cheek_deltaE76':round(sum(x['deltaE76'] for x in new if x['hero']==sex and 'cheek' in x['patch'])/2,2)} for sex in ['male','female']}
result['method']='Two fixed 5x5-pixel cheek patches per hero in crown/chin-registered front views. CIE76 includes shading and albedo; not a whole-face quality score.'
(proof/'continuation-comparison.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'checks':comparison,'video':videos,'cheek_comparison':result,'source_matches':verification['staged_source_matches_final_capture']},indent=2))
