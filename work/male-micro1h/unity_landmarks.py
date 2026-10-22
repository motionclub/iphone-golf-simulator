"""Overlay plate-derived landmarks on the Unity face_front capture.  python3 unity_landmarks.py out.png"""
import sys
from PIL import Image, ImageDraw
from pathlib import Path
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
K = 0.0013043874429196725; TOP = 1.7046599388122559; CX = 227.6
im = Image.open(R / 'ArtDir/hero/base_lock/proof/male_form_d/unity/face_front.png').convert('RGB')
size = 0.16; ppm = 360 / size; zc = 1.565
def P(col, row):
    x = (col - CX) * K; z = TOP - (row - 76) * K
    return 640 + x * ppm, 360 - (z - zc) * ppm
d = ImageDraw.Draw(im, 'RGBA')
pts = {'irisL': (199.5, 167.8), 'irisR': (255.7, 167.8), 'eyeOutL': (184.5, 168.7), 'eyeInL': (212.5, 169.6), 'eyeInR': (243.0, 169.6), 'eyeOutR': (270.6, 168.7),
       'browInL': (214.7, 148.3), 'browTailL': (175.6, 158.0), 'browInR': (240.5, 148.3), 'browTailR': (279.6, 158.0),
       'noseTip': (227.6, 198.0), 'alaL': (208.4, 203.0), 'alaR': (246.0, 203.0), 'subnasale': (227.6, 209.0),
       'mouthL': (199.8, 224.3), 'mouthR': (255.5, 223.6), 'seam': (227.6, 227.8), 'lipTop': (227.6, 222.8), 'lipBot': (227.6, 235.5), 'chin': (227.6, 267.0),
       'earTopL': (151.0, 157.4), 'earBotL': (151.0, 212.2)}
for k, (c, r) in pts.items():
    x, y = P(c, r)
    d.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(0, 255, 255, 255), width=2)
    d.line((x - 9, y, x + 9, y), fill=(255, 255, 0, 200)); d.line((x, y - 9, x, y + 9), fill=(255, 255, 0, 200))
im.save(sys.argv[1]); print(im.size)
