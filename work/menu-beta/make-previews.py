from pathlib import Path
import subprocess,json,sys
sys.path.insert(0,str(Path('work/presentation/video-tools/lib/python3.14/site-packages').resolve()))
import imageio_ffmpeg
ff=imageio_ffmpeg.get_ffmpeg_exe()
jobs=[('tennis','skyscraper','work/gameplay-capture/two_points.mp4',3,12),('golf','cliffside','work/presentation/films/editor/L2_L3_L4_golf_full_tv_editor.mp4',1,7)]
for sport,venue,src,start,duration in jobs:
 dst=Path('GolfArcade/Unity/MenuArt')/f'gameplay-{sport}-{venue}.mp4'
 subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',src,'-t',str(duration),'-an','-vf','scale=960:540:force_original_aspect_ratio=decrease,pad=960:540:(ow-iw)/2:(oh-ih)/2,fps=30','-c:v','libx264','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(dst)],check=True)
 subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-ss','2','-i',str(dst),'-frames:v','1',str(Path('work/menu-beta')/f'{sport}-preview.jpg')],check=True)
Path('work/menu-beta/preview-provenance.json').write_text(json.dumps(jobs,indent=2))
