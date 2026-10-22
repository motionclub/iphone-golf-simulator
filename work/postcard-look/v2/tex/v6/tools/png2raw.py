"""system python3 + Pillow: PNG/JPG -> raw uint8 RGB(A) file <out>.raw + <out>.shape (h w c).  usage: png2raw.py in.png out_stem"""
import sys
from PIL import Image
im = Image.open(sys.argv[1])
im = im.convert('RGBA' if im.mode in ('RGBA','LA','P') and 'A' in im.getbands() else 'RGB')
b = im.tobytes()
open(sys.argv[2] + '.raw', 'wb').write(b)
open(sys.argv[2] + '.shape', 'w').write(f"{im.size[1]} {im.size[0]} {len(im.getbands())}")
