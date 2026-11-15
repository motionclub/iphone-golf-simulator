import sys
from PIL import Image, ImageDraw
d0 = sys.argv[1]
cases = [("m", "fistPump"), ("m", "jumpJoy"), ("m", "victory"), ("f", "fistPump"), ("f", "defeat")]
W, H, cols = 150, 175, 15
sheet = Image.new("RGB", (W * cols + 90, H * 10), "white")
d = ImageDraw.Draw(sheet)
r = 0
for sex, clip in cases:
    for e in (0, 1):
        who = "him" if sex == "m" else "her"
        tag = "BEFORE" if e == 0 else "AFTER"
        d.text((4, r * H + 70), f"{who}\n{clip}\n{tag}", fill="black")
        for k in range(cols):
            im = Image.open(f"{d0}/{sex}_{clip}_{e}_{k:02d}.png").convert("RGB").resize((W, H))
            ImageDraw.Draw(im).text((3, 3), f"{k * 0.25:.2f}s", fill="white")
            sheet.paste(im, (90 + k * W, r * H))
        r += 1
sheet.save(sys.argv[2], quality=82)
