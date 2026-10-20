"""Build the portable review package from explicit, reviewed runtime evidence."""
from pathlib import Path
import json, html, shutil, hashlib, sys

repo=Path(__file__).resolve().parents[2]
manifest_path=Path(sys.argv[1])
manifest=json.loads(manifest_path.read_text())
out=Path(manifest['output']);out.mkdir(parents=True,exist_ok=True)
(out/'media').mkdir(exist_ok=True)
evidence=[]
def media(path,label):
    src=Path(path)
    if not src.is_absolute():src=repo/src
    if not src.is_file():raise FileNotFoundError(src)
    name=label+src.suffix
    dest=out/'media'/name;shutil.copy2(src,dest)
    evidence.append(dict(label=label,source=str(src),file='media/'+name,sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
    return 'media/'+name
def picture(path,label,caption):
    url=media(path,label)
    return f'<figure><a href="{url}"><img loading="lazy" src="{url}" alt="{html.escape(caption)}"></a><figcaption>{html.escape(caption)}</figcaption></figure>'
sections=[]
for k,item in enumerate(manifest.get('comparisons',[])):
    cards=[]
    for key,caption in [('before','Before · actual game'),('reference','GPT Image art target'),('actual','Implemented · actual game capture')]:
        if item.get(key):cards.append(picture(item[key],f'comparison-{k}-{key}',caption))
    sections.append('<article><h2>'+html.escape(item['title'])+'</h2><p>'+html.escape(item.get('note',''))+'</p><div class="comparison">'+''.join(cards)+'</div></article>')
catalog=[]
for k,item in enumerate(manifest.get('catalog',[])):
    catalog.append(picture(item['path'],f'catalog-{k}',item['title']))
if catalog:sections.append('<article id="catalog"><h2>Complete world catalog</h2><div class="catalog">'+''.join(catalog)+'</div></article>')
films=[]
for k,item in enumerate(manifest.get('films',[])):
    url=media(item['path'],f'film-{k}')
    films.append('<figure><video controls preload="metadata" playsinline src="'+url+'"></video><figcaption>'+html.escape(item['title'])+'</figcaption></figure>')
if films:sections.append('<article id="motion"><h2>Motion at real speed</h2><p>Actual consecutive game frames, encoded at 30 FPS. Diagnostic fixtures are identified in their captions.</p><div class="films">'+''.join(films)+'</div></article>')
notes=''.join('<li>'+html.escape(x)+'</li>' for x in manifest.get('verification',[]))
reports=[]
for k,item in enumerate(manifest.get('reports',[])):
    url=media(item['path'],f'report-{k}')
    reports.append('<li><a href="'+url+'">'+html.escape(item['title'])+'</a></li>')
sections.append('<article id="verification"><h2>Verification</h2><ul>'+notes+'</ul><ul>'+''.join(reports)+'</ul></article>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sports resort · implementation review</title><style>
:root{color-scheme:dark;font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;color:#fff9ee;background:#0a192d}*{box-sizing:border-box}body{margin:0}header,main{max-width:1500px;margin:auto;padding:40px 5vw}header{padding-top:72px;padding-bottom:24px}.eyebrow{color:#65d1d3;text-transform:uppercase;letter-spacing:.15em;font-size:12px;font-weight:800}h1{font-size:clamp(32px,5vw,68px);line-height:1.05;max-width:900px;margin:20px 0}h2{font-size:26px}p{color:#b7cdd3;max-width:950px;line-height:1.6}nav{display:flex;gap:24px;flex-wrap:wrap;margin:28px 0}a{color:#d7f044}article{border-top:1px solid #26415b;padding:28px 0 48px}.comparison{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.catalog,.films{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}figure{margin:0;background:#10243d;border-radius:16px;overflow:hidden}img,video{display:block;width:100%;height:auto;max-height:620px;object-fit:contain;background:#071424}figcaption{padding:16px;font-size:14px;line-height:1.45;color:#b7cdd3}li{margin:12px 0;line-height:1.6}.status{border-left:4px solid #d7f044;padding:12px 18px;background:#10243d;border-radius:0 12px 12px 0}@media(max-width:850px){.comparison,.catalog,.films{grid-template-columns:1fr}header,main{padding:28px 6vw}}
</style><header><div class="eyebrow">Golf + tennis · visual overhaul</div><h1>Sports resort, in the actual game.</h1><p>The GPT Image references show the art direction. The implemented column and videos show runtime evidence, with no painted additions.</p><p class="status">STATUS</p><nav><a href="#catalog">Worlds</a><a href="#motion">Motion</a><a href="#verification">Verification</a><a href="evidence.json">Evidence manifest</a></nav></header><main>SECTIONS</main></html>'''
page=page.replace('STATUS',html.escape(manifest.get('status','In progress · visual and runtime gates remain open'))).replace('SECTIONS',''.join(sections))
(out/'index.html').write_text(page)
(out/'evidence.json').write_text(json.dumps(dict(status=manifest.get('status'),verification=manifest.get('verification',[]),media=evidence),indent=2))
print(str(out/'index.html'))
