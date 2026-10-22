from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess, hashlib, json, sys, os
C=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/read-artdir-hero-base-lock-parallel')
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
O=C/'outputs/fluidity/manual-review/revision37';O.mkdir(parents=True,exist_ok=True)
hero=sys.argv[1]
camera=os.getenv("EF_VIEW", "front")
frame_dir="manual37_side_frames" if camera=="side" else "manual37_frames"
clips=sys.argv[2:] or ['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
def encode(clip):
 frames=sorted((C/'work'/frame_dir/hero/clip).glob(camera+'_*.png'))
 if not frames:raise RuntimeError('No captured frames: '+clip)
 output=O/f'{hero}_{clip}{"_side" if camera=="side" else ""}.mp4'
 run=subprocess.run([str(R/'work/emotes/scripts/enc'),str(output),'30','720','720',*[str(f) for f in frames]],check=True,text=True,capture_output=True)
 print(clip,run.stdout.strip(),flush=True)
 source=R/'work/emote-fluid/iterations/37/candidate/fbx'/f'{hero.title()}_{clip}.fbx'
 return dict(revision=37,hero=hero,clip=clip,path=str(output),frames=len(frames),fps=30,camera=camera,speed='normal',candidate_fbx_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),status='AWAITING_USER_REVIEW')
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(encode,clips))
manifest=O/f'{hero}_manifest.json'
prior=json.loads(manifest.read_text()) if manifest.exists() else []
rows=[x for x in prior if x['clip'] not in clips or x['camera']!=camera]+rows
manifest.write_text(json.dumps(rows,indent=2)+'\n')
readme=O/'REVIEW.md'
allrows=[]
for f in O.glob('*_manifest.json'):allrows+=json.loads(f.read_text())
readme.write_text('# Revision 37 visual review\n\nActual Unity playback, normal speed. Awaiting Adnan’s feedback. Automated verification stopped at his request. This candidate has not been installed.\n\n'+'\n\n'.join(f'**{x["hero"].title()} {x["clip"]} — {x["camera"]}**\n\n![{x["hero"]} {x["clip"]}]({x["path"]})' for x in allrows)+'\n')
