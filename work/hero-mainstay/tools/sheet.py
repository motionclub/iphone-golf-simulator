#!/usr/bin/env python3
"""sheet.py OUT.png COLS CELL IMG... : tile images into a contact sheet, each cell captioned with its file name (no extension)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont

def font(size):
    for p in ("/System/Library/Fonts/Menlo.ttc", "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def main():
    out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    files = sys.argv[4:]
    rows = (len(files) + cols - 1) // cols
    cap = 22
    sheet = Image.new("RGB", (cols * cell, rows * (cell + cap)), (20, 22, 30))
    d = ImageDraw.Draw(sheet); f = font(13)
    for i, p in enumerate(files):
        im = Image.open(p).convert("RGB"); im.thumbnail((cell, cell))
        x, y = (i % cols) * cell, (i // cols) * (cell + cap)
        sheet.paste(im, (x + (cell - im.width) // 2, y + cap))
        d.text((x + 4, y + 4), os.path.splitext(os.path.basename(p))[0][-44:], fill=(235, 235, 235), font=f)
    sheet.save(out); print(out, sheet.size)

if __name__ == "__main__":
    main()
