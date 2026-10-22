"""Texel magnification of the ground in the address-camera stills (system python3). The Fairway/Green/Rough tiles are 1024 px per 10 m (LOOK_CONTRACT section 3).
Address camera (CameraRig.FrameAddress): 2.4 yd above the ball, pitched 21.8 deg down, 60 deg vertical fov, 900x1600 frame.
usage: python3 texel_footprint.py"""
import math
h = 2.4 * 0.9144; pitch = math.radians(21.8); H = 1600; f = (H / 2) / math.tan(math.radians(60) / 2); tex = 10.0 / 1024
def row(y):
    a = pitch + math.atan((y - H / 2) / f); slant = h / math.sin(a); across = slant / f; along = across / math.sin(a)
    return a, slant, across, along
print(f"focal length {f:.1f} px, camera height {h:.3f} m, texel {tex * 1000:.2f} mm")
for y in (400, 490, 600, 800, 843, 1000, 1100, 1300, 1500, 1600):
    a, s, ac, al = row(y)
    print(f"row {y:4d}: {math.degrees(a):4.1f} deg below horizon, ground {h / math.tan(a):5.2f} m away, pixel {ac * 1000:6.2f} mm across / {al * 1000:6.2f} mm along -> one texel = {tex / ac:4.1f} x {tex / al:4.1f} px")
def first(fn):
    for y in range(301, 1600):
        if fn(y) >= 1.0 and fn(y - 1) < 1.0: return y
print("texel >= 1 px across the view from row", first(lambda y: tex / row(y)[2]), "; along the view from row", first(lambda y: tex / row(y)[3]))
