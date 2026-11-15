import json, subprocess, os, sys
W = os.path.dirname(os.path.abspath(__file__))
def key(f, pos, look, fov=35, roll=0, focusOffset=0): return dict(f=f, pos=pos, look=look, fov=fov, roll=roll, focusOffset=focusOffset)
def cam(name, keys, posAnchor="world", lookAnchor="world", **kw):
    d = dict(name=name, posAnchor=posAnchor, lookAnchor=lookAnchor, keys=keys); d.update(kw); return d
def still(name, pos, look, fov=35, posAnchor="world", lookAnchor="world", **kw): return cam(name, [key(0, pos, look, fov)], posAnchor, lookAnchor, **kw)
def lit(name, pos, look=None, color=(1,1,1), intensity=1, anchor="world", type="spot", **kw):
    d = dict(name=name, type=type, anchor=anchor, pos=list(pos), look=list(look or [0,0,0]), color=list(color), intensity=intensity); d.update(kw); return d
def ev(f, do="call", **kw): d = dict(f=f); d["do"] = do; d.update(kw); return d
def call(f, on, m, *a): return dict(f=f, do="call", on=on, m=m, a=[str(x) for x in a])
def send(cmd, timeout=1200, quiet=False):
    p = subprocess.run([sys.executable, os.path.join(W, "send.py"), "-", str(timeout)], input=json.dumps(cmd), text=True, capture_output=True)
    if not quiet or p.returncode: print(p.stdout[-4000:], p.stderr[-2000:])
    return p.returncode == 0
def take(**kw): return send(dict(op="take", take=kw))
def sheet(paths, out, cols=3, w=640, labels=True):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths]; h = int(w * ims[0].height / ims[0].width); rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * w, rows * h), (0, 0, 0)); d = ImageDraw.Draw(S)
    for i, (im, p) in enumerate(zip(ims, paths)):
        S.paste(im.resize((w, h), Image.LANCZOS), ((i % cols) * w, (i // cols) * h))
        if labels: d.text(((i % cols) * w + 6, (i // cols) * h + 4), os.path.basename(os.path.dirname(p)) + "/" + os.path.basename(p), fill=(255, 255, 0))
    S.save(out, quality=88); return out
