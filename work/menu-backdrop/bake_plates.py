"""MENU BACKDROP plates: MenuVenueStand's no-post renders (<venue>_y###_raw.png, hero hidden) -> Resources/Menu/Backdrops/<venue>.jpg
(blurred scenery, sharp floor round the line-up's feet: the depth of field the menu camera would see) + <venue>_light.json.

  python3 bake_plates.py <capture dir> <Unity/Assets/Resources/Menu/Backdrops>
"""
import glob, json, os, shutil, sys
import numpy as np
from PIL import Image, ImageFilter

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
W, H = 1920, 1080
# the floor stays sharp in a soft ellipse round the feet (the line-up stands on the bottom fifth, centred; friends to the right)
yy, xx = np.mgrid[0:H, 0:W]
feet = np.clip(1.3 - np.hypot((xx - W * .58) / (W * .34), (yy - H * .90) / (H * .16)), 0, 1)
sharp = np.clip(feet, 0, 1)[..., None]
for raw in sorted(glob.glob(os.path.join(src, '*_raw.png'))):
    venue = os.path.basename(raw).split('_y')[0]
    im = Image.open(raw).convert('RGB')
    soft = np.asarray(im.filter(ImageFilter.GaussianBlur(6)), dtype=np.float32)
    out = soft * (1 - sharp) + np.asarray(im, dtype=np.float32) * sharp
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(os.path.join(dst, venue + '.jpg'), quality=88, optimize=True)
    shutil.copy(raw.replace('_raw.png', '_light.json'), os.path.join(dst, venue + '_light.json'))
    print(venue)
