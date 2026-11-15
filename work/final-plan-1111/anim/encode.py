"""encode.py <round>: the films of films.sh as one labelled video per sport (tennis.mp4, golf.mp4, bowling.mp4, plaza.mp4) and one
overview sheet per sport (<sport>_sheet.jpg: every clip at a few moments, the close view). Each clip: a title card, then the game's own
picture beside the close view of the hero (2000 x 720, 30 fps). Uses the ffmpeg in ~/tai-films (no system ffmpeg on this Mac)."""
import sys, os, glob, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

A = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(A, sys.argv[1]); FF = os.path.expanduser("~/tai-films/ffmpeg")
SEG = os.path.join(R, "_segments"); os.makedirs(SEG, exist_ok=True)
W, H, FPS = 2000, 1080, 30   # (H is set per sport: 1080 with the hand close-ups, 720 without)
font = lambda s: ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", s)

def ff(*args):
    r = subprocess.run([FF, "-y", "-loglevel", "error", *args], capture_output=True, text=True)
    if r.returncode: print("ffmpeg failed:", r.stderr[-400:])
    return r.returncode == 0

def card(path, title, sub=""):
    im = Image.new("RGB", (W, H), (16, 18, 24)); d = ImageDraw.Draw(im)
    d.text((80, H // 2 - 100), title, font=font(64), fill=(255, 255, 255))
    if sub: d.text((80, H // 2), sub, font=font(34), fill=(170, 200, 230))
    im.save(path)

def fit(): return f"scale=w={W}:h={H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x101218,setsar=1,fps={FPS}"

def title_seg(name, title, sub=""):
    png = os.path.join(SEG, name + ".png"); card(png, title, sub); out = os.path.join(SEG, name + ".mp4")
    ff("-loop", "1", "-t", "1.0", "-i", png, "-vf", fit(), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", out)
    return out

def frames_seg(name, folder, streams):
    """streams: picture prefixes in the folder, side by side, each scaled to the film's height."""
    streams = [s for s in streams if os.path.exists(os.path.join(folder, s + "_00000.jpg"))]
    if not streams: return None
    out = os.path.join(SEG, name + ".mp4"); ins = []
    full = [x for x in ("game", "front", "side", "handL", "handR") if os.path.exists(os.path.join(folder, x + "_00000.jpg"))]
    if H == 1080 and len(full) == 5:
        # the game's picture and the front view on top; side view and both hands close up underneath
        for x in full: ins += ["-framerate", str(FPS), "-i", os.path.join(folder, x + "_%05d.jpg")]
        fc = ("[0:v]scale=1280:720[g];[1:v]scale=720:720[f];[g][f]hstack[top];[2:v]scale=360:360[s];[3:v]scale=360:360[l];[4:v]scale=360:360[r];"
              f"[s][l][r]hstack=inputs=3,pad=2000:360:(ow-iw)/2:0:color=0x101218[bot];[top][bot]vstack,setsar=1,fps={FPS}[v]")
        ok = ff(*ins, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", "-shortest", out)
        return out if ok else None
    for s in streams: ins += ["-framerate", str(FPS), "-i", os.path.join(folder, s + "_%05d.jpg")]
    if len(streams) == 1: fc = f"[0:v]{fit()}[v]"
    else: fc = "".join(f"[{i}:v]scale=-2:{H}[s{i}];" for i in range(len(streams))) + "".join(f"[s{i}]" for i in range(len(streams))) + f"hstack=inputs={len(streams)},{fit()}[v]"
    ok = ff(*ins, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-shortest", out)
    return out if ok else None

def video_seg(name, src):
    out = os.path.join(SEG, name + ".mp4")
    return out if ff("-i", src, "-vf", fit(), "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", out) else None

def by_time(folders):
    def t(f):
        g = sorted(glob.glob(os.path.join(f, "*_00000.jpg"))); return os.path.getmtime(g[0]) if g else 0
    return sorted([f for f in folders if t(f)], key=t)

def nice(s): return s.replace("_", " ").replace("emote ", "emote: ").replace("react ", "reaction: ").replace("result ", "emote: ").replace("hub ", "")

sheets = {}
ONLY = set(sys.argv[2:])
def collect(sport, parts, height=1080):
    global H
    if ONLY and sport not in ONLY: return
    H = height
    segs = []; cells = []
    for kind, label, path, streams in parts:
        if kind == "video" and os.path.exists(path):
            segs += [title_seg(f"{sport}_{len(segs)}_t", label), video_seg(f"{sport}_{len(segs)}_v", path)]
        elif kind == "frames":
            v = frames_seg(f"{sport}_{len(segs)}_v", path, streams)
            if v:
                segs += [title_seg(f"{sport}_{len(segs)}_t", label), v]
                close = next((s for s in ["handR", "hero"] + streams[1:] + streams[:1] if os.path.exists(os.path.join(path, s + "_00000.jpg"))), None)
                n = len(glob.glob(os.path.join(path, close + "_*.jpg"))) if close else 0
                if n: cells.append((label, [os.path.join(path, f"{close}_{int(n * k):05d}.jpg") for k in (.2, .45, .7, .9)]))
    segs = [s for s in segs if s]
    if not segs: print(sport, "nothing filmed"); return
    lst = os.path.join(SEG, sport + ".txt"); open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    out = os.path.join(R, sport + ".mp4"); ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out)
    print(sport, out, f"{os.path.getsize(out) / 1e6:.1f} MB" if os.path.exists(out) else "FAILED")
    sheets[sport] = cells

def jf(sport, who, d):   # a JoyFilm output folder: every clip folder in the order filmed
    d = os.path.join(R, d)
    return [("frames", f"{sport}  -  {who}  -  {nice(os.path.basename(f))}", f, ["game", "front"]) for f in by_time(glob.glob(os.path.join(d, "*")))] if os.path.isdir(d) else []

collect("tennis", [("video", "Tennis  -  a real point: him (near) against her, both side on", os.path.join(R, "tennis_match", "film.mp4"), None)]
        + jf("Tennis", "him", "tennis_emotes_m") + jf("Tennis", "her", "tennis_emotes_f"))
gs = os.path.join(R, "golf_swing")
collect("golf", [("frames", f"Golf  -  {'her' if os.path.basename(f).startswith('female') else 'him'}  -  {nice(os.path.basename(f).split('_', 1)[1])}", f, ["game", "hero"])
                 for f in by_time(glob.glob(os.path.join(gs, "*male_*"))) if not f.endswith("_intro")]
        + jf("Golf", "him", "golf_emotes_m") + jf("Golf", "her", "golf_emotes_f"))
collect("bowling", [("frames", "Bowling  -  both heroes taking turns", os.path.join(R, "bowling", "frames"), ["f"])], 720)
collect("plaza", jf("Plaza", "him", "plaza_m") + jf("Plaza", "her", "plaza_f"))

# overview sheets: every clip, four moments of the close view
for sport, cells in sheets.items():
    if not cells: continue
    S = 230; lab = 26; cols = 2; rows = (len(cells) + cols - 1) // cols
    im = Image.new("RGB", (cols * (4 * S + 20) + 20, 60 + rows * (S + lab + 10)), (16, 18, 24)); d = ImageDraw.Draw(im)
    d.text((20, 16), f"{sport.capitalize()}: every animation filmed on the installed game (four moments each; the right hand close up where filmed)", font=font(26), fill=(255, 255, 255))
    for i, (label, files) in enumerate(cells):
        x = 20 + (i % cols) * (4 * S + 20); y = 60 + (i // cols) * (S + lab + 10)
        d.text((x, y + 2), label.split("  -  ", 1)[-1], font=font(18), fill=(255, 220, 150))
        for k, f in enumerate(files):
            if os.path.exists(f):
                p = Image.open(f).convert("RGB"); p.thumbnail((S, S)); im.paste(p, (x + k * S + (S - p.width) // 2, y + lab + (S - p.height) // 2))
    out = os.path.join(R, sport + "_sheet.jpg"); im.save(out, quality=86); print(out, im.size)
