"""repair round 2 contact sheet (Blender EEVEE previews, NOT Game view): tee frame before / after, the first-cut sliver wedge before / after, the pad from three aerial views after."""
from PIL import Image, ImageDraw
def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle((0, 0, im.width, 18), fill=(0, 0, 0)); d.text((6, 3), t, fill=(255, 255, 255)); return im
W = 1500
a = Image.open("pv_before/hole10_tee.png").convert("RGB"); b = Image.open("pv_after/hole10_tee.png").convert("RGB")
tw = 450
a2, b2 = a.resize((tw, 800)), b.resize((tw, 800))
w1 = Image.open("pv_before/uv_wedge.png").convert("RGB").resize((600, 400)); w2 = Image.open("pv_after/uv_wedge.png").convert("RGB").resize((600, 400))
x1 = Image.open("pv_before/uv_wedge2.png").convert("RGB").resize((600, 400)); x2 = Image.open("pv_after/uv_wedge2.png").convert("RGB").resize((600, 400))
p1 = Image.open("pv_after/uv_pad.png").convert("RGB").resize((500, 333)); p2 = Image.open("pv_after/uv_pad_side.png").convert("RGB").resize((500, 333)); p3 = Image.open("pv_after/uv_pad_front.png").convert("RGB").resize((500, 333))
S = Image.new("RGB", (W, 800 + 800 + 333 + 40), (20, 20, 20))
S.paste(lab(a2, "tee frame BEFORE (no pad edge)"), (0, 0)); S.paste(lab(b2, "tee frame AFTER (flagstone kerb at the pad edge)"), (tw, 0))
S.paste(lab(w1, "FIRSTCUT wedge BEFORE (3 slivers, 103 m2, 26:1)"), (2 * tw, 0)); S.paste(lab(w2, "AFTER (one similarity per cluster, 1.0:1)"), (2 * tw + 600 - 0 if False else 2 * tw, 400))
S.paste(lab(x1, "second view BEFORE"), (2 * tw, 800)); S.paste(lab(x2, "second view AFTER"), (2 * tw + 0, 1200)) if False else None
S2 = Image.new("RGB", (W, 800 + 333 + 20), (20, 20, 20))
S2.paste(lab(a2, "tee frame BEFORE (no pad edge)"), (0, 0)); S2.paste(lab(b2, "tee frame AFTER (flagstone kerb at the pad edge)"), (tw, 0))
S2.paste(lab(w1, "FIRSTCUT sliver wedge BEFORE (3 triangles, 103 m2, up to 26:1)"), (2 * tw, 0)); S2.paste(lab(w2, "AFTER (one similarity per cluster, ratio 1.0)"), (2 * tw, 400))
S2.paste(lab(p1, "pad AFTER: back-left aerial"), (0, 800 + 10)); S2.paste(lab(p2, "pad AFTER: side"), (500, 800 + 10)); S2.paste(lab(p3, "pad AFTER: front"), (1000, 800 + 10))
S2 = S2.crop((0, 0, 2 * tw + 600, 800 + 343))
S2.save("sheet_repair_r2.jpg", quality=88); print(S2.size)
