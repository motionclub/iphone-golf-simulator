"""clips.py <round>: one short, numbered clip per animation from the films of films.sh, and a page to look through them all.
   <round>/clips/NNN_<sport>_<who>_<animation>.mp4 (label burnt in, 30 fps) + a poster picture each, and <round>/clips/index.html.
Tennis point: each hero's animations cut from the real point (first instance of each, a little before and after). Bowling: each
player's deliveries and reactions. Emotes, plaza moves, golf swings: one clip per filmed folder; anything longer than 6 s is cut to
the 6 s with the most movement (the emote or swing itself, not the wait around it)."""
import sys, os, glob, csv, json, subprocess, collections, re
import numpy as np
from PIL import Image

A = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(A, sys.argv[1]); FF = os.path.expanduser("~/tai-films/ffmpeg")
OUT = os.path.join(R, "clips"); os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*")): os.remove(f)
FONT = "/System/Library/Fonts/Helvetica.ttc"; FPS = 30; MAXS = 6.0
clips = []

def ff(*args):
    r = subprocess.run([FF, "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode: print("ffmpeg:", r.stderr[-300:])
    return r.returncode == 0

def esc(t): return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’")

def label_filter(text):
    return (f"drawbox=x=0:y=0:w=iw:h=54:color=0x101218@0.85:t=fill,"
            f"drawtext=fontfile={FONT}:text='{esc(text)}':x=18:y=12:fontsize=30:fontcolor=white")

def add(sport, who, anim, make):
    n = len(clips) + 1; name = f"{n:03d}_{sport}_{who}_{re.sub('[^A-Za-z0-9]+', '_', anim).strip('_')}"
    path = os.path.join(OUT, name + ".mp4"); text = f"{n}  {sport.capitalize()}  -  {who}  -  {anim}"
    if make(path, label_filter(text)):
        ff("-ss", "0.6", "-i", path, "-frames:v", "1", "-vf", "scale=480:-2", os.path.join(OUT, name + ".jpg"))
        clips.append(dict(n=n, sport=sport, who=who, anim=anim, file=name + ".mp4", poster=name + ".jpg"))

def busiest(folder, stream, total):
    """first frame of the MAXS-second window with the most movement in `stream` (pictures every frame at FPS)."""
    want = int(MAXS * FPS)
    if total <= want: return 0
    prev = None; motion = []
    for i in range(total):
        p = os.path.join(folder, f"{stream}_{i:05d}.jpg")
        a = np.asarray(Image.open(p).convert("L").resize((64, 64)), dtype=np.float32) if os.path.exists(p) else prev
        motion.append(0 if prev is None or a is None else float(np.abs(a - prev).mean())); prev = a
    c = np.cumsum([0] + motion); best = max(range(total - want + 1), key=lambda s: c[s + want] - c[s])
    return best

def frames_clip(folder, layout):
    """layout 'joy' = game + front over side + both hands; 'golf' = portrait game + hero close view; 'one' = a single stream f."""
    def make(path, lab):
        streams = {"joy": ["game", "front", "side", "handL", "handR"], "golf": ["game", "hero"], "one": ["f"]}[layout]
        streams = [s for s in streams if os.path.exists(os.path.join(folder, s + "_00000.jpg"))]
        if not streams: return False
        total = min(len(glob.glob(os.path.join(folder, s + "_*.jpg"))) for s in streams)
        start = busiest(folder, "front" if "front" in streams else streams[-1], total); count = min(total - start, int(MAXS * FPS))
        ins = []
        for s in streams: ins += ["-start_number", str(start), "-framerate", str(FPS), "-i", os.path.join(folder, s + "_%05d.jpg")]
        if layout == "joy" and len(streams) == 5:
            fc = ("[0:v]scale=1280:720[g];[1:v]scale=720:720[f];[g][f]hstack[top];[2:v]scale=360:360[s];[3:v]scale=360:360[l];[4:v]scale=360:360[r];"
                  "[s][l][r]hstack=inputs=3,pad=2000:360:(ow-iw)/2:0:color=0x101218[bot];[top][bot]vstack,scale=1440:-2")
        elif len(streams) > 1:
            fc = "".join(f"[{i}:v]scale=-2:720[s{i}];" for i in range(len(streams))) + "".join(f"[s{i}]" for i in range(len(streams))) + f"hstack=inputs={len(streams)}"
        else: fc = "[0:v]scale=1280:-2"
        return ff(*ins, "-filter_complex", fc + f",{lab},setsar=1[v]", "-map", "[v]", "-frames:v", str(count),
                  "-c:v", "libx264", "-preset", "faster", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path)
    return make

def video_clip(src, t0, t1):
    def make(path, lab):
        return ff("-ss", f"{max(0, t0):.3f}", "-to", f"{t1:.3f}", "-i", src, "-vf", f"scale=1440:-2,{lab},fps={FPS},setsar=1", "-an",
                  "-c:v", "libx264", "-preset", "faster", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path)
    return make

def nice(s):
    s = s.replace("Female_", "").replace("Male_", "").replace("ArmCorrected", "").replace("Emote_", "emote ").replace("_", " ")
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s).strip()

# ---- tennis: the real point, each hero's animations (first instance of each; the longest for the ready stance)
tm = os.path.join(R, "tennis_match")
if os.path.exists(os.path.join(tm, "frames.csv")):
    rows = list(csv.DictReader(open(os.path.join(tm, "frames.csv"))))
    for hero, who in (("male", "him"), ("female", "her")):
        r = [x for x in rows if x["hero"] == hero]; runs = collections.defaultdict(list); cur = None; start = 0
        for x in r + [{"tick": str(len(r)), "clip": None}]:
            if x["clip"] != cur:
                if cur: runs[cur].append((start, int(x["tick"]) - 1))
                cur = x["clip"]; start = int(x["tick"])
        order = sorted(runs, key=lambda c: runs[c][0][0])
        for c in order:
            a, b = max(runs[c], key=lambda ab: ab[1] - ab[0]) if "Ready" in c or "Run" in c else runs[c][0]
            pad = 18 if "Run" not in c else 6
            a, b = max(0, a - pad), b + pad
            if b - a < 60: b = a + 60
            if (b - a) / 60 > MAXS: b = a + int(MAXS * 60)
            add("tennis", who, nice(c) + " (real point)", video_clip(os.path.join(tm, "film.mp4"), a / 60, b / 60))
for d, who in (("tennis_emotes_m", "him"), ("tennis_emotes_f", "her")):
    for f in sorted(glob.glob(os.path.join(R, d, "*")), key=lambda p: os.path.getmtime(p)):
        if os.path.isdir(f): add("tennis", who, nice(os.path.basename(f).replace("emote_", "").replace("react_", "reaction ")), frames_clip(f, "joy"))

# ---- golf: every club and the golf film's moves, then the emotes / walk / run
for sex, who in (("male", "him"), ("female", "her")):
    for f in sorted(glob.glob(os.path.join(R, "golf_swing", sex + "_*")), key=os.path.getmtime):
        if f.endswith("_intro") or not os.path.isdir(f): continue
        add("golf", who, nice(os.path.basename(f).split("_", 1)[1]), frames_clip(f, "golf"))
for d, who in (("golf_emotes_m", "him"), ("golf_emotes_f", "her")):
    for f in sorted(glob.glob(os.path.join(R, d, "*")), key=os.path.getmtime):
        if os.path.isdir(f): add("golf", who, nice(os.path.basename(f).replace("result_", "").replace("move_", "")), frames_clip(f, "joy"))

def frames_range(path, lab, a, b):
    return ff("-start_number", str(a), "-framerate", str(FPS), "-i", os.path.join(R, "bowling", "frames", "f_%05d.jpg"), "-frames:v", str(b - a + 1),
              "-vf", f"scale=1280:-2,{lab},setsar=1", "-c:v", "libx264", "-preset", "faster", "-crf", "26", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path)

# ---- bowling: each player's deliveries (the last 5 s up to the release, and a moment after) and reactions
bt = os.path.join(R, "bowling", "timeline.csv")
if os.path.exists(bt):
    rows = list(csv.DictReader(open(bt))); runs = []; cur = None; start = 0
    for x in rows + [{"frame": str(len(rows)), "clip": None, "player": None}]:
        k = (x["player"], x["clip"])
        if k != cur:
            if cur and cur[1]: runs.append((cur[0], cur[1], start, int(x["frame"]) - 1))
            cur = k; start = int(x["frame"])
    seen = set()
    for p, c, a, b in runs:
        if c.startswith("BowlRelease") and (p, c) not in seen:
            seen.add((p, c)); add("bowling", f"player {int(p) + 1}", "delivery, " + nice(c.replace("Bowl", "")), lambda path, lab, a=a, b=b: frames_range(path, lab, max(0, a - 120), b + 15))
        elif c.startswith("BowlReact") and (p, c) not in seen:
            seen.add((p, c)); add("bowling", f"player {int(p) + 1}", nice(c.replace("Bowl", "")), lambda path, lab, a=a, b=b: frames_range(path, lab, max(0, a - 10), b + 20))

# ---- plaza: walk, run, sprint and every emote
for d, who in (("plaza_m", "him"), ("plaza_f", "her")):
    for f in sorted(glob.glob(os.path.join(R, d, "*")), key=os.path.getmtime):
        if os.path.isdir(f): add("plaza", who, nice(os.path.basename(f).replace("hub_", "")), frames_clip(f, "joy"))

# ---- the page: every clip, numbered; hover or click to play
json.dump(clips, open(os.path.join(OUT, "clips.json"), "w"), indent=1)
cards = "".join(f'''<figure data-sport="{c['sport']}"><video src="{c['file']}" poster="{c['poster']}" muted loop playsinline preload="none"></video>
<figcaption><b>{c['n']}</b> {c['sport'].capitalize()} &middot; {c['who']} &middot; {c['anim']}</figcaption></figure>''' for c in clips)
sports = sorted(set(c["sport"] for c in clips), key=["tennis", "golf", "bowling", "plaza"].index)
page = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Animation review</title>
<style>
:root{{--bg:#111318;--card:#1b1e25;--ink:#eef0f4;--mute:#9aa3b2;--accent:#ffd27a}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px -apple-system,Helvetica,sans-serif}}
header{{position:sticky;top:0;background:var(--bg);padding:14px 16px;border-bottom:1px solid #2a2e38;z-index:2}}
h1{{font-size:20px;margin:0 0 8px}} p{{margin:0 0 10px;color:var(--mute)}}
button{{background:var(--card);color:var(--ink);border:1px solid #333a47;border-radius:8px;padding:6px 12px;margin-right:6px;cursor:pointer}}
button.on{{border-color:var(--accent);color:var(--accent)}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;padding:16px}}
figure{{margin:0;background:var(--card);border-radius:10px;overflow:hidden}} video{{width:100%;display:block;background:#000;cursor:pointer}}
figcaption{{padding:8px 10px}} figcaption b{{color:var(--accent);margin-right:6px}}
</style></head><body><header><h1>Every animation, installed game ({len(clips)} clips)</h1>
<p>Hover or tap a clip to play it; click to open it full size. Tell me the numbers that need work.</p>
<button class="on" data-f="all">All</button>{"".join(f'<button data-f="{s}">{s.capitalize()}</button>' for s in sports)}</header>
<main>{cards}</main>
<script>
document.querySelectorAll('video').forEach(v=>{{v.addEventListener('mouseenter',()=>v.play());v.addEventListener('mouseleave',()=>v.pause());
 v.addEventListener('click',()=>{{v.controls=true;v.play();if(v.requestFullscreen)v.requestFullscreen();}});}});
document.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{{document.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
 document.querySelectorAll('figure').forEach(f=>f.style.display=(b.dataset.f==='all'||f.dataset.sport===b.dataset.f)?'':'none');}}));
</script></body></html>'''
open(os.path.join(OUT, "index.html"), "w").write(page)
by = collections.Counter(c["sport"] for c in clips)
print(len(clips), "clips", dict(by), f"{sum(os.path.getsize(os.path.join(OUT, c['file'])) for c in clips) / 1e6:.0f} MB")
