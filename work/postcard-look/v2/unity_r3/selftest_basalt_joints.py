#!/usr/bin/env python3
"""Self-test of the round-3 BASALT_JOINTS rules (proof/measure.py basalt_metrics + basalt_shot_ok + basalt_network_ok) on synthetic frames:
  neutral branching network -> PASS;  maroon network -> FAIL (S);  neutral parallel vertical streaks (the Game-view pattern the review rejected) -> FAIL (vertical share / junctions);  neutral horizontal ladders -> FAIL (rungs).
usage: python3 selftest_basalt_joints.py"""
import sys, numpy as np
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/proof")
import measure as M
from PIL import Image, ImageDraw
rng = np.random.default_rng(7)
W, H = 900, 700

class FakeShot:
    def __init__(self, img):
        self.px = np.asarray(img).astype(np.uint8)
    def idmask(self, cat):
        return np.ones(self.px.shape[:2], bool) if cat == "basalt" else None

def base(color):
    im = Image.new("RGB", (W, H), color)
    return im

def network(im, n=140):
    """Voronoi-edge-like crack network: random polylines with branches, 2 px wide, orange."""
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H); ang = rng.uniform(0, np.pi)
        for seg in range(rng.integers(4, 9)):
            L = rng.uniform(8, 22); x2, y2 = x + L * np.cos(ang), y + L * np.sin(ang)
            d.line([(x, y), (x2, y2)], fill=(230, 95, 25), width=2)
            if rng.random() < .5:       # branch
                a2 = ang + rng.choice([-1, 1]) * rng.uniform(.5, 1.2); d.line([(x2, y2), (x2 + 12 * np.cos(a2), y2 + 12 * np.sin(a2))], fill=(230, 95, 25), width=2)
            x, y = x2, y2; ang += rng.uniform(-.5, .5)
    return im

def streaks(im, n=160):
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H - 20); L = rng.uniform(8, 16)
        d.line([(x, y), (x + rng.uniform(-.6, .6), y + L)], fill=(230, 95, 25), width=2)
    return im

def ladders(im, n=160):
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(0, W - 30), rng.uniform(0, H); L = rng.uniform(10, 24)
        d.line([(x, y), (x + L, y + rng.uniform(-1, 1))], fill=(230, 95, 25), width=2)
    return im

def verdict(name, img, expect):
    sh = FakeShot(img); b = M.basalt_metrics(sh)
    sk, cl = b.get("glow_skeleton_px", 0), b.get("glow_junction_clusters", 0)
    ok = M.basalt_shot_ok(b) and M.basalt_network_ok(sk, cl)
    rate = 100.0 * cl / max(sk, 1)
    print(f"SELFTEST {name}: S {b['base_s']:.2f} vertical {b.get('glow_vertical_line_share', 0) * 100:.0f}% rungs {b.get('glow_horizontal_rung_share', 0) * 100:.0f}% blob {b.get('glow_blob_share', 0) * 100:.0f}% junctions {rate:.2f}/100 skel px -> {'PASS' if ok else 'FAIL'}; expected {'PASS' if expect else 'FAIL'} {'OK' if ok == expect else 'UNEXPECTED'}")
    return ok == expect

res = [
    verdict("neutral_branching_network", network(base((34, 31, 33))), True),
    verdict("maroon_branching_network", network(base((56, 28, 26))), False),
    verdict("neutral_parallel_vertical_streaks", streaks(base((34, 31, 33))), False),
    verdict("neutral_horizontal_ladders", ladders(base((34, 31, 33))), False),
]
print("SELFTEST_BASALT_JOINTS", "ALL AS EXPECTED" if all(res) else "UNEXPECTED RESULT")
sys.exit(0 if all(res) else 1)
