from pathlib import Path
import json,re,shutil,csv,hashlib
from PIL import Image,ImageDraw,ImageFont
import numpy as np
root=Path(__file__).resolve().parents[2]
w=Path(__file__).resolve().parent
out=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-2/outputs')
proof=root/'ArtDir/screenshots/golf_course_standard'
out.mkdir(exist_ok=True);proof.mkdir(parents=True,exist_ok=True)
assets=out/'course-review';assets.mkdir(exist_ok=True)
names={7:'Cliffside',12:'Island Carry',13:'The Spiral',14:"The Witch’s Lair",15:'The Steps',16:'Volcano Rim',17:'Frostbite Fjord',18:'Mesa Canyon',19:'Temple Falls',20:'Windmill Links',21:'Obsidian Slab',22:'Ember Causeway',23:'Caldera Crown',8:'Needle · reference',9:'Split · reference',10:'Crater · reference'}
views=['tee','approach','putting','aerial','gameplay'];results=[]
for number,name in names.items():
    stem=f'hole{number:02}'
    before=json.loads((w/f'proof/before/{stem}_audit.json').read_text())
    after=json.loads((w/f'proof/release/{stem}_audit.json').read_text())
    assert after['ground']==before['ground'],str(number)+' collision changed'
    assert after['obstacleHash']==before['obstacleHash'],str(number)+' obstacles changed'
    results.append(dict(hole=number,name=name,colliders=after['colliders'],obstacles=after['obstacleCount'],textures_mib=round(after['textureBytes']/1048576,2),camera_mesh_triangles=after['cameraMeshTriangles'],camera_material_passes=after['cameraMaterialPasses'],editor_aggregate_draws=after['drawCalls'],editor_aggregate_triangles=after['triangles']))
    for stage,folder in [('before','before'),('after','release')]:
        dest=proof/stage;dest.mkdir(exist_ok=True)
        shutil.copy2(w/f'proof/{folder}/{stem}_audit.json',dest)
        for view in views:
            p=w/f'proof/{folder}/{stem}_{view}.png'
            shutil.copy2(p,dest)
            Image.open(p).resize((450,800),Image.Resampling.LANCZOS).save(assets/f'{stem}_{stage}_{view}.jpg',quality=91)
    sheet=Image.new('RGB',(1800,1680),'#101b22');d=ImageDraw.Draw(sheet)
    for i,view in enumerate(['tee','aerial']):
        for j,stage in enumerate(['before','after']):
            image=Image.open(assets/f'{stem}_{stage}_{view}.jpg').resize((450,800))
            x=(i*2+j)*450;sheet.paste(image,(x,50));d.text((x+14,19),f'{name} / {view} / {stage}',fill='white')
    # Compact, two-view sheet; avoid a redundant empty lower half.
    sheet.crop((0,0,1800,850)).save(proof/f'{stem}_comparison.jpg',quality=92)
with (proof/'course-metrics.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=results[0].keys());writer.writeheader();writer.writerows(results)
shutil.copy2(proof/'course-metrics.csv',out/'course-metrics.csv')
noise={}
for n in (8,9,10):
    noise[n]={}
    for view in ['tee','approach','putting','aerial']:
        b=np.array(Image.open(w/f'proof/before/hole{n:02}_{view}.png')).astype(float)
        a=np.array(Image.open(w/f'proof/release/hole{n:02}_{view}.png')).astype(float)
        prev=np.array(Image.open(w/f'proof/final-r2/hole{n:02}_{view}.png')).astype(float)
        diff=np.abs(a-b); repeat=np.abs(a-prev)
        noise[n][view]={'baseline_mae':float(diff.mean()),'baseline_pixels_over_10_pct':float((diff.max(2)>10).mean()*100),'repeat_mae':float(repeat.mean()),'repeat_pixels_over_10_pct':float((repeat.max(2)>10).mean()*100)}
(w/'reference-differences.json').write_text(json.dumps(noise,indent=2))
(proof/'reference-differences.json').write_text(json.dumps(noise,indent=2))
options=''.join(f'<option value="{n:02}">{n} · {name}</option>' for n,name in names.items())
html='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Golf course visual review</title><style>
*{box-sizing:border-box}body{margin:0;background:#111b20;color:#f1f6f4;font:16px system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:32px 24px}h1{font-weight:650;font-size:32px;margin:0 0 10px}p{color:#b9cbc7;line-height:1.5;max-width:900px}.tag{color:#abdc99;font-size:13px;letter-spacing:.08em;text-transform:uppercase}.controls{display:flex;gap:18px;margin:24px 0;flex-wrap:wrap}label{display:grid;gap:8px;font-size:13px}select{font:16px system-ui;color:#f1f6f4;background:#203139;border:1px solid #466057;border-radius:8px;padding:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#203139;border-radius:12px;overflow:hidden}figcaption{padding:12px 16px;font-size:14px}img{display:block;width:100%;height:auto}.note{font-size:13px}a{color:#a9d9f1}#stats{font-size:14px;color:#b9cbc7;margin:18px 0}@media(max-width:600px){main{padding:20px 12px}h1{font-size:24px}.pair{gap:6px}figcaption{padding:10px}}</style></head><body><main>
<div class="tag">Golf simulator · shared course standard</div><h1>Every course, the same surface library.</h1><p>All 13 non-Postcard holes now reuse the Postcard ground, rock, water, lava, and plant systems. Snow, ice, desert, wood, and foliage keep their own textures and lighting. Select a hole and camera to compare the actual Unity renders.</p>
<div class="controls"><label>Hole<select id="hole">OPTIONS</select></label><label>Camera<select id="view"><option>tee</option><option>approach</option><option>putting</option><option>aerial</option><option>gameplay</option></select></label></div>
<div class="pair"><figure><figcaption>Before</figcaption><img id="before" alt="Baseline course render"></figure><figure><figcaption>After</figcaption><img id="after" alt="Upgraded course render"></figure></div><div id="stats"></div>
<p class="note">Gameplay captures now include the HUD; the baseline gameplay captures show the golfer without it. The original layout, collision meshes, and obstacles are preserved. Postcards 8–10 are controls. Flag, water, particles, and other effect clocks can differ between captures.</p><p class="note">Validated on Unity 6000.3.24f1 / Metal / Apple M5. iPhone frame time and iOS app build remain unverified: the phone is offline and this Unity installation has no iOS Build Support. <a href="GATE_RESULTS.md">Read validation results</a> · <a href="GOLF_ALL_COURSES_POSTCARD_STANDARD_PLAN.md">Read the plan</a></p>
<script>const data=METRICS;const hole=document.querySelector('#hole'),view=document.querySelector('#view');function show(){const n=hole.value,v=view.value;for(const stage of ['before','after'])document.querySelector('#'+stage).src=`course-review/hole${n}_${stage}_${v}.jpg`;const d=data.find(r=>r.hole===+n);document.querySelector('#stats').textContent=`${d.colliders} collision meshes unchanged · ${d.obstacles} obstacles unchanged · ${d.textures_mib} MiB referenced course textures. Camera mesh inventory: ${d.camera_mesh_triangles.toLocaleString()} triangles / ${d.camera_material_passes} material passes (excludes shadow passes and characters; not a GPU timing measurement).`;}hole.onchange=view.onchange=show;show();</script></main></body></html>'''
(out/'golf-course-review.html').write_text(html.replace('OPTIONS',options).replace('METRICS',json.dumps(results)))
# A small summary image is convenient in chat.
sheet=Image.new('RGB',(1350,850),'#111b20');d=ImageDraw.Draw(sheet)
for i,n in enumerate([12,17,21]):
    for j,stage in enumerate(['before','after']):
        im=Image.open(assets/f'hole{n:02}_{stage}_aerial.jpg').resize((225,800));x=i*450+j*225;sheet.paste(im,(x,50));d.text((x+8,18),f'{names[n]} / {stage}',fill='white')
sheet.save(out/'golf-course-comparison.jpg',quality=93)
print(json.dumps({'holes':len(results),'original_collision_meshes':sum(r['colliders'] for r in results),'max_course_texture_mib':max(r['textures_mib'] for r in results),'max_camera_mesh_triangles':max(r['camera_mesh_triangles'] for r in results),'max_camera_material_passes':max(r['camera_material_passes'] for r in results)},indent=2))
