"""HERO_DETAIL textures -> Unity/Assets/Resources/Tennis/HeroDetail/   (system python3: numpy + PIL)

    python3 make_textures.py            # weave + skin normal + the 12 kit seam maps baked by bake_kit.py (maps/*.npy)

  Cloth_Weave.png   256 px RGBA, tiles. R,G = tangent-space normal x,y (0.5 = flat), B = thread break (1 = top of a thread, lower in the
                    gaps between threads and with a small tone difference per yarn), A = height.   8 x 8 threads per tile, plain weave.
  Skin_Soft_N.png   256 px tangent-space normal map (tiles): low-frequency undulation, a soft break in the light and no pores.
  Kit_<Sex>_<Piece>.png  the baked seam / collar / placket / hem maps, in the kit mesh's own UV layout (sRGB-encoded multiplier).
"""
import os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "Unity", "Assets", "Resources", "Tennis", "HeroDetail")
os.makedirs(OUT, exist_ok=True)


def save(arr, name, mode):
    Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(os.path.join(OUT, name), optimize=True)


def normal_from_height(h, strength):
    """Tangent-space normal from a periodic height field (central differences with wrap-around, so the tile stays seamless)."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx, ny, nz = -dx * strength, dy * strength, np.ones_like(h)   # +y up in UV space (row 0 is the top of the PNG)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return nx / l, ny / l, nz / l


def weave(size=256, threads=8, seed=11):
    rng = np.random.default_rng(seed)
    pitch = size // threads
    y, x = np.mgrid[0:size, 0:size].astype(np.float64)
    cu, cv = (x % pitch) / pitch, (y % pitch) / pitch
    i, j = (x // pitch).astype(int), (y // pitch).astype(int)
    over = ((i + j) & 1).astype(np.float64)
    ridge_u, ridge_v = np.sin(np.pi * cu), np.sin(np.pi * cv)
    warp = np.power(ridge_u, 0.65) * (0.55 + 0.45 * np.sqrt(ridge_v))     # vertical thread: crown across u, swells where it crosses over
    weft = np.power(ridge_v, 0.65) * (0.55 + 0.45 * np.sqrt(ridge_u))
    h = over * warp + (1 - over) * weft
    # yarn twist: a faint diagonal ridge running along each thread
    twist_w = 0.06 * np.sin(2 * np.pi * (cv * 3.0 + cu * 0.5)) * ridge_u * over
    twist_f = 0.06 * np.sin(2 * np.pi * (cu * 3.0 + cv * 0.5)) * ridge_v * (1 - over)
    h = h + twist_w + twist_f
    nx, ny, nz = normal_from_height(h, 2.6)
    tone_w = 0.90 + 0.10 * rng.random(threads)       # each yarn is a touch lighter or darker than its neighbours
    tone_f = 0.90 + 0.10 * rng.random(threads)
    tone = over * tone_w[i % threads] + (1 - over) * tone_f[j % threads]
    hn = (h - h.min()) / (h.max() - h.min())
    thread = np.clip((0.50 + 0.50 * hn) * tone, 0, 1)                       # gaps between threads read darker, the crown stays near 1
    rgba = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, thread, hn], -1)
    save(rgba, "Cloth_Weave.png", "RGBA")
    return dict(thread_mean=float(thread.mean()), thread_min=float(thread.min()), tilt_max_deg=float(np.degrees(np.arccos(nz.min()))),
                tilt_rms_deg=float(np.degrees(np.arccos(nz)).mean()))


def skin_soft(size=256, seed=5):
    """Periodic low-pass noise (FFT) -> height -> normal. Wavelengths of a quarter to a half of the tile: with 0.2 m per tile that is 5 to 10 cm."""
    rng = np.random.default_rng(seed)
    f = np.fft.fft2(rng.standard_normal((size, size)))
    fy = np.fft.fftfreq(size)[:, None]; fx = np.fft.fftfreq(size)[None, :]
    k = np.sqrt(fx * fx + fy * fy) * size            # cycles per tile
    band = np.exp(-0.5 * ((k - 3.0) / 1.6) ** 2)      # most energy at ~3 cycles per tile, none at DC and none above ~7
    h = np.real(np.fft.ifft2(f * band)); h /= h.std()
    nx, ny, nz = normal_from_height(h, 0.055 * size / 4)
    g = np.hypot(nx / nz, ny / nz)
    rgb = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5], -1)
    save(rgb, "Skin_Soft_N.png", "RGB")
    return dict(slope_rms=float(np.sqrt((g ** 2).mean())), slope_max=float(g.max()))


def lin2srgb(a):
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * np.power(np.clip(a, 1e-6, 1), 1 / 2.4) - 0.055)


PIECES = [("Kit_Top", "Top"), ("Kit_Bottom", "Bottom"), ("Kit_Shoe_L", "ShoeL"), ("Kit_Shoe_R", "ShoeR"), ("Kit_Sock_L", "SockL"), ("Kit_Sock_R", "SockR")]


def kit_maps():
    made = []
    for sex in ("Male", "Female"):
        for src, tag in PIECES:
            p = os.path.join(HERE, "maps", f"{sex}_{src}.npy")
            if not os.path.exists(p):
                print("missing", p); continue
            a = np.load(p).astype(np.float64)
            s = lin2srgb(a)
            save(np.stack([s, s, s], -1), f"Kit_{sex}_{tag}.png", "RGB")
            made.append((f"Kit_{sex}_{tag}.png", a.shape[0], float(a.min())))
    return made


if __name__ == "__main__":
    print("weave", weave())
    print("skin", skin_soft())
    for m in kit_maps():
        print("kit", m)
