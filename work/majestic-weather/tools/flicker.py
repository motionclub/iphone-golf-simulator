#!/usr/bin/env python3
"""flicker.py <video.mp4> [<video.mp4> ...] — how fast the ground's light changes in a golf weather video.

Frames every 0.1 s from 0.3 s to 4.8 s (Swift AVAssetImageGenerator tool at /private/tmp/claude-501/frames). Region: the
fairway in the lower half of the 1280x720 address view, minus the golfer + ball box. Reports, per 0.1 s step, the mean
absolute luma change (/255) and the share of region pixels that changed by more than 12/255 (a visible band or shadow
edge sweeping past). 10-18 phone report: "insane shadows going everywhere" in the gusty weather."""
import os, subprocess, sys, tempfile
from PIL import Image, ImageChops

FRAMES = "/private/tmp/claude-501/frames"
STEPS = [round(.3 + .1 * i, 2) for i in range(46)]


def luma(path):
    im = Image.open(path).convert("L")
    if im.size != (1280, 720):
        im = im.resize((1280, 720))
    return im


def measure(video):
    tmp = tempfile.mkdtemp(dir=os.path.dirname(FRAMES))
    subprocess.run([FRAMES, video, os.path.join(tmp, "f")] + [str(s) for s in STEPS], check=True)
    frames = [luma(os.path.join(tmp, f"f_{i}.jpg")) for i in range(len(STEPS))]
    box = (0, 400, 1280, 720)
    golfer = (330, 0, 700, 320)   # inside the crop: x 330-700, y 400-720 (golfer, club, ball)
    means, bands = [], []
    for a, b in zip(frames, frames[1:]):
        d = ImageChops.difference(a.crop(box), b.crop(box))
        d.paste(0, golfer)
        px = list(d.getdata()); n = len(px) - (golfer[2] - golfer[0]) * (golfer[3] - golfer[1])
        means.append(sum(px) / n); bands.append(sum(1 for v in px if v > 12) / n)
    return sum(means) / len(means), max(means), sum(bands) / len(bands), max(bands)


if __name__ == "__main__":
    for v in sys.argv[1:]:
        m, mx, b, bx = measure(v)
        print(f"{os.path.basename(os.path.dirname(v))}/{os.path.basename(v)}: mean |dL| per 0.1 s {m:.2f}/255 (max {mx:.2f}); "
              f"pixels changing >12/255: {100 * b:.2f} % (max {100 * bx:.2f} %)")
