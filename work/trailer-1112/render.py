#!/usr/bin/env python3
"""Renders the picture in parallel pieces and joins them with the sound.  render.py [--half] [--jobs 4] [--out FILE]"""
import os, sys, json, subprocess, argparse
W = os.path.dirname(os.path.abspath(__file__)); FF = os.path.expanduser("~/tai-films/ffmpeg")
ap = argparse.ArgumentParser(); ap.add_argument("--half", action="store_true"); ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--out", default=os.path.join(W, "MotionSports_Trailer.mp4")); ap.add_argument("--audio", default=os.path.join(W, "stage", "score.wav"))
a = ap.parse_args()
T = json.load(open(os.path.join(W, "timeline.json"))); total = T["total"]; fps = T.get("fps", 24)
n = a.jobs; frames = int(round(total * fps)); cuts = [round(i * frames / n) / fps for i in range(n + 1)]; parts = []; procs = []
os.makedirs(os.path.join(W, "stage", "parts"), exist_ok=True)
for i in range(n):
    p = os.path.join(W, "stage", "parts", f"part{i}.mp4"); parts.append(p)
    cmd = [sys.executable, os.path.join(W, "edit.py"), "--from", str(cuts[i]), "--to", str(cuts[i + 1]), "--out", p] + (["--half"] if a.half else [])
    procs.append(subprocess.Popen(cmd, stdout=subprocess.DEVNULL))
bad = [i for i, p in enumerate(procs) if p.wait() != 0]
if bad: sys.exit("render failed in part(s) %s" % bad)
lst = os.path.join(W, "stage", "parts", "list.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
cmd = [FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst]
if os.path.exists(a.audio): cmd += ["-i", a.audio, "-c:a", "aac", "-b:a", "256k", "-shortest"]
cmd += ["-c:v", "copy", "-movflags", "+faststart", a.out]
subprocess.check_call(cmd); print(a.out, "%.1f s" % total)
