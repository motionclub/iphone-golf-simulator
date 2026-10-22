#!/usr/bin/env python3
"""POSTCARD_LOOK area I: measurements from the PIXELS of the Game-view stills (and the installed FBXs at mesh level) -> proof/metrics.json + proof/METRICS.md.

usage: python3 measure.py            (system python3: numpy + Pillow)

Inputs
  ArtDir/screenshots/golf_postcards/look/hole0N_k_*.png   the 9 proof stills (PostcardLookStills, active quality asset)
  proof/masks/9/*   proof/masks/extra/*                   PostcardProofMasks: per shot full.png (same frame), id.png (every material slot = a flat colour: exact per-material masks),
                                                          group diff masks (shelf, ocean, surf, fall, lava, smoke, plant, rock, ball), smoke / lava dry frames, masks_meta.json
  proof/extra/*.png                                       aerials + path-ball shot (measurement only, not proof shots)
  proof/mesh_checks.json                                  installed_mesh_checks.py (Blender, installed FBX)
Every number written here is read from those files; thresholds are the ones in THRESH below (the user's lines, the runtime gates' own limits, or stated).
"""
import json, math, os, sys, glob, collections
import numpy as np
from PIL import Image

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
P = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_default'
ART = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round1/runtime_adapter_check_default/stills'
W, H = 900, 1600

SHOTS9 = ["hole08_1_tee", "hole08_2_approach", "hole08_3_arch", "hole09_1_tee", "hole09_2_approach", "hole09_3_ruin", "hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim"]
EXTRAS = ["hole08_4_pathball", "hole08_aerial", "hole09_aerial", "hole10_aerial"]
HOLE_OF = lambda n: int(n[4:6])

THRESH = dict(
    grass_hue=(60.0, 76.0),          # fairway / green: the stills' 64..73 with the runtime gate's +-4 (RUNTIME.md v2.5: fairway / green 60..76)
    rough_hue=(54.0, 76.0),          # rough band of the same gate
    grass_clip_max=0.05,             # share of grass pixels with a channel >= 250 (golf key light must not clip the albedo)
    flat_win=8, flat_sd=0.006, block_sd=0.003, flat_max=0.15, lower=0.60,   # postcard_look_verify STILL_TH (LOOK_STILLS_TEXTURED)
    lum_sd_min=12.0,                 # luminance sd (0..255) of the lower 60 %: the flat baseline holes measure below this (see baseline rows)
    shelf_top2_max=0.10, shelf_vs_sea_max=1.3, shelf_hue=(170.0, 205.0),   # GolfLookProbe PROBE_SHELF_NOT_LOUDEST (<= 10 % of the brightest 2 %, <= 1.3 x the open sea beside it)
    lava_band=0.85, lava_gclip_max=0.05, lava_dark_max=0.15, lava_meanV_min=0.70,   # runtime LAVA_ORANGE_NO_BLOOM (>= 85 % in band, <= 5 % G >= 250) + the brief: mostly bright, not dark cells
    basalt_glow_cov_max=0.20, basalt_median_lum_max=55.0, basalt_vert_share_min=0.50, basalt_rung_share_max=0.20,   # runtime BASALT_GLOW_ORANGE coverage <= 20 %, lit wall median <= 55; joints: vertical lines (basalt_vert_share_min is NOT applied since round 3: basalt_shot_ok)
    # v2 repair round 3 2026-10-05 (review, high, hole 10): the gate PASSED a maroon basalt (mean S .54-.59) whose glow was 89-98 % parallel vertical 2 px streaks with no branching joints, because it had no saturation
    # ceiling and its only structure rule ASKED for vertical lines. Added (coverage, median luminance and rungs above are unchanged; the vertical FLOOR above is no longer applied, see basalt_shot_ok): non-glow mean S <= .25 (crater.jpg basalt (26,25,29) S .10, (39,32,34) S .18, 'left wall mid' (63,50,49) S .21);
    # vertical-line share <= .80 (a streak-only pattern is 89-98 %, branching joints are not all vertical); joint network: Zhang-Suen skeleton junction clusters per 100 skeleton px of the glow (all proof shots together) >= 3.0
    # (the crater.jpg wall crops measure 8.3-8.8 per 100 px, the streaky Game-view basalt .6-2.4; v2/unity_r3/branch_probe.py).
    basalt_base_s_max=0.25, basalt_vert_share_max=0.80, basalt_junction_per100_min=3.0,
    smoke_edge_p99_max=6.0, smoke_dp95_min=8.0, smoke_dmax_max=110.0, smoke_px_min=500,   # runtime SMOKE_SOFT: edge step p99 <= 6 levels/px, visible (>= 8), never a ball
    ball_visible_min=0.90,
    path_max_cm=1.5,                 # DRESS_PATH_* up-facing top <= 1.5 cm over the play surface (hole builder PATH_UNDER_BALL)
)


# ----------------------------------------------------------------------------- helpers
def load(path):
    return np.asarray(Image.open(path).convert("RGB"))


def rgb2hsv(a):
    a = a.astype(np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-9
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6
    h[gm] = (b - r)[gm] / d[gm] + 2
    h[bm] = (r - g)[bm] / d[bm] + 4
    h = h * 60.0
    s = np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0.0)
    return h, s, mx


def mean_hsv(rgb_mean):
    h, s, v = rgb2hsv(np.array(rgb_mean, dtype=np.float64).reshape(1, 1, 3))
    return float(h[0, 0]), float(s[0, 0]), float(v[0, 0])


def circ_mean_deg(h):
    r = np.deg2rad(h)
    return float(np.rad2deg(math.atan2(np.sin(r).mean(), np.cos(r).mean())) % 360)


def lum255(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def flat_share(lum01, win=8, flat_sd=0.006, block_sd=0.003):
    Hh, Ww = lum01.shape
    h2, w2 = Hh // win, Ww // win
    a = lum01[:h2 * win, :w2 * win].reshape(h2, win, w2, win)
    sd = a.std(axis=(1, 3))
    b = a.reshape(h2, win // 4, 4, w2, win // 4, 4).mean(axis=(2, 5))
    bsd = b.std(axis=(1, 3))
    flat = (sd < flat_sd) | (bsd < block_sd)
    return float(flat.mean()), float(np.median(sd)), int(flat.size)


def components(mask, min_px=1):
    """4-connected components of a boolean mask -> list of (pixel count, ys, xs). Pure numpy/python BFS on the true pixels only."""
    ys, xs = np.nonzero(mask)
    idx = {(int(y), int(x)): i for i, (y, x) in enumerate(zip(ys, xs))}
    seen = np.zeros(len(ys), bool)
    out = []
    ylist, xlist = ys.tolist(), xs.tolist()
    for i in range(len(ys)):
        if seen[i]:
            continue
        stack = [i]; seen[i] = True; comp = []
        while stack:
            j = stack.pop(); comp.append(j)
            y, x = ylist[j], xlist[j]
            for k in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                t = idx.get(k)
                if t is not None and not seen[t]:
                    seen[t] = True; stack.append(t)
        if len(comp) >= min_px:
            c = np.array(comp)
            out.append((len(comp), ys[c], xs[c]))
    return out


def comp_shape(ys, xs):
    """(elongation = sqrt(l1 / l2), angle of the major axis from vertical in degrees 0..90, bbox height, bbox width)"""
    if len(ys) < 3:
        return 1.0, 45.0, int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1)
    c = np.cov(np.vstack([xs.astype(float), ys.astype(float)]))
    ev, evec = np.linalg.eigh(c)
    l2, l1 = max(ev[0], 1e-6), max(ev[1], 1e-6)
    v = evec[:, 1]                       # (x, y) of the major axis
    ang = math.degrees(math.atan2(abs(v[0]), abs(v[1])))       # 0 = vertical, 90 = horizontal
    return math.sqrt(l1 / l2), ang, int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1)


def zhang_suen(img):
    """Zhang-Suen thinning of a 0/1 array (numpy, whole-array passes). Returns the skeleton as uint8 0/1."""
    img = img.copy().astype(np.uint8)

    def step(img, first):
        Pd = np.pad(img, 1)
        p2 = Pd[:-2, 1:-1]; p3 = Pd[:-2, 2:]; p4 = Pd[1:-1, 2:]; p5 = Pd[2:, 2:]; p6 = Pd[2:, 1:-1]; p7 = Pd[2:, :-2]; p8 = Pd[1:-1, :-2]; p9 = Pd[:-2, :-2]
        nb = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
        seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
        tr = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.uint8) for i in range(8))
        c = ((p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)) if first else ((p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0))
        rm = (img == 1) & (nb >= 2) & (nb <= 6) & (tr == 1) & c
        img[rm] = 0
        return bool(rm.any())
    ch = True
    while ch:
        a = step(img, True); b = step(img, False); ch = a or b
    return img


def skeleton_junctions(mask):
    """(skeleton pixel count, number of 8-connected junction clusters = skeleton pixels with >= 3 skeleton neighbours) of a boolean mask."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return 0, 0
    y0, y1, x0, x1 = max(ys.min() - 2, 0), ys.max() + 3, max(xs.min() - 2, 0), xs.max() + 3
    sk = zhang_suen(mask[y0:y1, x0:x1])
    Pd = np.pad(sk, 1)
    nb = sum(Pd[1 + dy:Pd.shape[0] - 1 + dy, 1 + dx:Pd.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    j = (sk == 1) & (nb >= 3)
    return int(sk.sum()), len(components(j, 1))


# ----------------------------------------------------------------------------- per-shot loading
class Shot:
    def __init__(self, name, still_path, mask_dir, meta):
        self.name = name
        self.hole = HOLE_OF(name)
        self.still = load(still_path)
        self.full = load(f"{mask_dir}/{name}.full.png") if os.path.exists(f"{mask_dir}/{name}.full.png") else None
        self.meta = meta
        self.mask_dir = mask_dir
        self.consistency = None
        if self.full is not None:
            d = np.abs(self.full.astype(int) - self.still.astype(int)).sum(2)
            self.consistency = dict(max_abs_channel_diff=int(np.abs(self.full.astype(int) - self.still.astype(int)).max()), frac_px_sum_diff_gt8=float((d > 8).mean()))
        self.px = self.full if self.full is not None else self.still       # mask-based statistics read the frame the masks were made from
        self._ids = None
        # v2 2026-10-05 (carry-over finding, low: "the arch still's mask frame differs from the proof frame ... animated water, 11.4 % of the frame"): the sea is the tennis shader's own Time-driven swell and moves from
        # run to run, so the consistency is ALSO measured without the water pixels (ocean / shelf / surf / fall ID masks, grown by 2 px for the anti-aliased shoreline): what is left must be identical.
        if self.full is not None and self.consistency is not None:
            wm = None
            for cat in ("ocean", "shelf", "surf", "fall"):
                if cat in (meta or {}).get("id_colors", {}):
                    m = self.idmask(cat)
                    if m is not None:
                        wm = m if wm is None else (wm | m)
            if wm is not None:
                g = wm.copy()
                for _ in range(2):
                    g = g | np.roll(g, 1, 0) | np.roll(g, -1, 0) | np.roll(g, 1, 1) | np.roll(g, -1, 1)
                dd = np.abs(self.full.astype(int) - self.still.astype(int))
                keep = ~g
                self.consistency["water_px_share"] = float(g.mean())
                self.consistency["max_abs_channel_diff_without_water"] = int(dd[keep].max()) if keep.any() else 0
                self.consistency["frac_px_sum_diff_gt8_without_water"] = float((dd.sum(2)[keep] > 8).mean()) if keep.any() else 0.0

    def idmask(self, cat):
        if self._ids is None:
            p = f"{self.mask_dir}/{self.name}.id.png"
            self._ids = load(p).astype(int) if os.path.exists(p) else False
        if self._ids is False:
            return None
        col = np.array(self.meta["id_colors"][cat])
        return np.abs(self._ids - col).max(2) <= 3

    def diffmask(self, grp):
        p = f"{self.mask_dir}/{self.name}.{grp}.png"
        return load(p)[..., 0] > 127 if os.path.exists(p) else None


def build_shots():
    shots = {}
    for key, names, still_dir in (("9", SHOTS9, ART), ("extra", EXTRAS, P + "/extra")):
        md = f"{P}/masks/{key}"
        mp = f"{md}/masks_meta.json"
        if not os.path.exists(mp):
            continue
        meta = {s["name"]: s for s in json.load(open(mp))["shots"]}
        for n in names:
            sp = f"{still_dir}/{n}.png"
            if n in meta and os.path.exists(sp):
                shots[n] = Shot(n, sp, md, meta[n])
        shots["_pipeline_" + key] = json.load(open(mp)).get("pipeline")
    return shots


# ----------------------------------------------------------------------------- metrics
def grass_metrics(sh):
    """central lower third (the PostcardLookStills definition) + the pixels the ID render says are grass (fairway / green / rough / scrub), lower 60 % of the frame"""
    a = sh.still
    reg = a[H - H // 3:H, W // 3:2 * W // 3].reshape(-1, 3).mean(0)
    h, s, v = mean_hsv(reg)
    out = dict(central_lower_third=dict(mean_rgb=[round(float(x), 1) for x in reg], hue=round(h, 1), s=round(s, 3), v=round(v, 3)))
    lower = np.zeros((H, W), bool); lower[int(H * (1 - THRESH["lower"])):, :] = True
    p = sh.px
    hh, ss, vv = rgb2hsv(p)
    for cat in ("fairway", "green", "rough", "scrub"):
        m = sh.idmask(cat)
        if m is None:
            continue
        m = m & lower
        n = int(m.sum())
        if n < 50:
            out[cat] = dict(pixels=n)
            continue
        px = p[m]
        mean = px.mean(0)
        mh, ms, mv = mean_hsv(mean)
        out[cat] = dict(pixels=n, share_of_lower60=round(n / lower.sum(), 4), mean_rgb=[round(float(x), 1) for x in mean], hue_of_mean=round(mh, 1), hue_median=round(float(np.median(hh[m])), 1),
                        hue_p10=round(float(np.percentile(hh[m], 10)), 1), hue_p90=round(float(np.percentile(hh[m], 90)), 1), s=round(ms, 3), v=round(mv, 3),
                        clip_any_ch_250=round(float((px.max(1) >= 250).mean()), 4), clip_g_250=round(float((px[:, 1] >= 250).mean()), 4),
                        share_hue_in_60_76=round(float(((hh[m] >= 60) & (hh[m] <= 76)).mean()), 3))
    return out


def flat_metrics(sh):
    a = sh.still
    lum = lum255(a.astype(float))
    lower = lum[int(H * (1 - THRESH["lower"])):, :]
    fs, msd, nwin = flat_share(lower / 255.0, THRESH["flat_win"], THRESH["flat_sd"], THRESH["block_sd"])
    out = dict(lower60_lum_sd=round(float(lower.std()), 2), lower60_lum_mean=round(float(lower.mean()), 1), flat_window_share=round(fs, 4), median_window_sd=round(msd, 4), windows=nwin)
    # distinct material kinds really visible (ID render: share of the whole frame)
    kinds = {}
    cats = list(sh.meta["id_colors"].keys())
    for c in cats:
        m = sh.idmask(c)
        if m is not None and m.mean() >= 0.01:
            kinds[c] = round(float(m.mean()), 3)
    out["id_kinds_ge_1pct"] = kinds
    # one flat colour test on the whole frame: k-means-free proxy = number of 16-level RGB cells holding >= 1 % of the pixels
    q = (a // 16).astype(np.int32).reshape(-1, 3)
    key = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    cnt = np.bincount(key, minlength=4096)
    out["colour_cells_ge_1pct"] = int((cnt / key.size >= 0.01).sum())
    out["largest_colour_cell_share"] = round(float(cnt.max() / key.size), 3)
    return out


def hex_of(rgb):
    return "#%02X%02X%02X" % tuple(int(round(x)) for x in rgb)


def shelf_metrics(sh):
    """shelf vs the brightest shapes of the frame. top2 = the brightest 2 % of the pixels (luminance); shelf / surf / waterfall / ocean from the ID render"""
    p = sh.px.astype(float)
    lum = lum255(p)
    cut = float(np.percentile(lum, 98))
    top = lum >= cut
    nt = int(top.sum())
    out = dict(top2_lum_cut=round(cut, 1), top2_px=nt)
    for c in ("shelf", "surf", "fall", "ocean", "lava"):
        m = sh.idmask(c)
        if m is not None:
            out[f"top2_share_{c}"] = round(float((top & m).sum() / nt), 4)
    # sky / whatever is not a model material: pixels the ID render left black (clear colour)
    ids = sh.idmask("fairway")
    out["top2_share_other_or_sky"] = None
    sm = sh.idmask("shelf")
    om = sh.idmask("ocean")
    if sm is not None:
        known = np.zeros((H, W), bool)
        for c in sh.meta["id_colors"]:
            mm = sh.idmask(c)
            if mm is not None:
                known |= mm
        out["top2_share_other_or_sky"] = round(float((top & ~known).sum() / nt), 4)
        n = int(sm.sum())
        out["shelf_px"] = n
        out["shelf_share_of_frame"] = round(n / (W * H), 5)
        if n >= 300:
            sp = p[sm]
            mean = sp.mean(0); mh, ms, mv = mean_hsv(mean)
            out["shelf_mean_rgb"] = [round(float(x), 1) for x in mean]
            out["shelf_hue"] = round(mh, 1); out["shelf_s"] = round(ms, 3); out["shelf_v"] = round(mv, 3)
            out["shelf_lum_mean"] = round(float(lum[sm].mean()), 1); out["shelf_lum_p95"] = round(float(np.percentile(lum[sm], 95)), 1)
            if om is not None and om.sum() > 1000:
                near = om & ~sm
                out["ocean_lum_mean"] = round(float(lum[near].mean()), 1)
                out["ocean_mean_rgb"] = [round(float(x), 1) for x in p[near].mean(0)]
                out["shelf_vs_ocean_lum"] = round(out["shelf_lum_mean"] / max(out["ocean_lum_mean"], 1e-6), 3)
            # "turquoise" pixels anywhere in the frame (hue 165..205, S >= .45): are they the brightest shape?
            hh, ss, vv = rgb2hsv(sh.px)
            tq = (hh >= 165) & (hh <= 205) & (ss >= 0.45)
            out["turquoise_px_share_of_frame"] = round(float(tq.mean()), 4)
            out["top2_share_turquoise"] = round(float((top & tq).sum() / nt), 4)
    # brightest connected blob of the frame: what is it
    return out


def lava_metrics(sh):
    m = sh.idmask("lava")
    if m is None or m.sum() < 500:
        return None
    p = sh.px
    px = p[m].astype(float)
    hh, ss, vv = rgb2hsv(p)
    hm, sm_, vm = hh[m], ss[m], vv[m]
    band = (hm >= 8) & (hm <= 28) & (sm_ >= 0.75) & (vm >= 0.70)
    band_nov = (hm >= 8) & (hm <= 28) & (sm_ >= 0.75)
    mean = px.mean(0); mh, ms, mv = mean_hsv(mean)
    lum = lum255(px)
    out = dict(pixels=int(m.sum()), share_of_frame=round(float(m.mean()), 4), mean_rgb=[round(float(x), 1) for x in mean], mean_hue=round(mh, 1), mean_s=round(ms, 3), mean_v=round(mv, 3),
               in_band_hue8_28_s75_v70=round(float(band.mean()), 4), in_band_hue_s_only=round(float(band_nov.mean()), 4),
               dark_v_lt_040=round(float((vm < 0.40).mean()), 4), dark_v_lt_025=round(float((vm < 0.25).mean()), 4), v_median=round(float(np.median(vm)), 3),
               g_ge_250=round(float((px[:, 1] >= 250).mean()), 4), lum_mean=round(float(lum.mean()), 1), lum_p10=round(float(np.percentile(lum, 10)), 1), lum_p90=round(float(np.percentile(lum, 90)), 1),
               cream_min_ch_ge_230=round(float((px.min(1) >= 230).mean()), 4))
    # dark-cell structure: connected components of the dark pixels of the lava (V < .40); polygon cells = big compact blobs, flow = thin ribbons / flecks
    dark = np.zeros((H, W), bool); dark[m] = vv[m] < 0.40
    comps = components(dark, 4)
    if comps:
        sizes = np.array([c[0] for c in comps])
        elong = np.array([comp_shape(c[1], c[2])[0] for c in comps])
        out["dark_components"] = int(len(comps)); out["dark_largest_px"] = int(sizes.max()); out["dark_median_px"] = int(np.median(sizes))
        out["dark_largest_share_of_lava"] = round(float(sizes.max() / m.sum()), 4)
        big = sizes >= 400
        out["dark_components_ge_400px"] = int(big.sum())
        out["dark_median_elongation"] = round(float(np.median(elong)), 2)
    # lava vs the rest of the frame: is it the bright thing?
    out["frame_lum_mean"] = round(float(lum255(p.astype(float)).mean()), 1)
    return out


def basalt_shot_ok(b):
    """BASALT_JOINTS per proof shot (basalt_metrics dict -> bool). Round 3 (2026-10-05): + non-glow mean S ceiling, + 'not streak-only' (vertical-line share <= .80); the old floor 'glow in vertical lines >= 50 %' is
    dropped: crater.jpg's own wall crops measure 5 / 5 / 37 % by the same classification (a connected branching network is one blob, not a line), so the floor failed the reference and ASKED for the streak pattern the review
    rejected (89-98 % vertical 2 px streaks). Its job (no ladders, no blobs-only) is kept by 'horizontal rungs <= 20 %' and by the aggregated junction rule below."""
    return bool(b["glow_coverage"] <= THRESH["basalt_glow_cov_max"] and b["base_lum_median"] <= THRESH["basalt_median_lum_max"]
                and b.get("glow_horizontal_rung_share", 1) <= THRESH["basalt_rung_share_max"]
                and b["base_s"] <= THRESH["basalt_base_s_max"] and b.get("glow_vertical_line_share", 0) <= THRESH["basalt_vert_share_max"])


def basalt_network_ok(skeleton_px, junction_clusters):
    """Joint network (all proof shots together): >= 200 skeleton px and >= 3.0 skeleton junction clusters per 100 skeleton px."""
    return bool(skeleton_px >= 200 and 100.0 * junction_clusters / max(skeleton_px, 1) >= THRESH["basalt_junction_per100_min"])


def basalt_metrics(sh):
    m = sh.idmask("basalt")
    if m is None or m.sum() < 2000:
        return None
    p = sh.px
    hh, ss, vv = rgb2hsv(p)
    px = p[m].astype(float)
    lum = lum255(px)
    glow = m & (hh >= 5) & (hh <= 35) & (ss >= 0.55) & (vv >= 0.40)
    base = m & ~glow
    out = dict(pixels=int(m.sum()), share_of_frame=round(float(m.mean()), 4), glow_px=int(glow.sum()), glow_coverage=round(float(glow.sum() / m.sum()), 4))
    bp = p[base].astype(float)
    mean = bp.mean(0); mh, ms, mv = mean_hsv(mean)
    bl = lum255(bp)
    out.update(base_mean_rgb=[round(float(x), 1) for x in mean], base_hue=round(mh, 1), base_s=round(ms, 3), base_v=round(mv, 3), base_lum_median=round(float(np.median(bl)), 1),
               base_lum_p90=round(float(np.percentile(bl, 90)), 1), base_lum_mean=round(float(bl.mean()), 1), base_s_median=round(float(np.median(ss[base])), 3))
    if glow.sum() >= 30:
        gl = p[glow].astype(float)
        out["glow_mean_rgb"] = [round(float(x), 1) for x in gl.mean(0)]
        out["glow_mean_hue"] = round(mean_hsv(gl.mean(0))[0], 1)
        out["glow_cream_share"] = round(float((gl.min(1) >= 230).mean()), 4)
        comps = components(glow, 6)
        tot = sum(c[0] for c in comps) or 1
        vert = rung = blob = 0; heights = []; widths = []
        for n, ys, xs in comps:
            el, ang, bh, bw = comp_shape(ys, xs)
            heights.append(bh); widths.append(bw)
            if el >= 2.5 and ang <= 35:
                vert += n
            elif el >= 2.5 and ang >= 55:
                rung += n
            elif el < 2.0:
                blob += n
        keep = np.zeros_like(glow)
        for n, ys, xs in comps:
            keep[ys, xs] = True
        sk_px, sk_j = skeleton_junctions(keep)
        out.update(glow_skeleton_px=sk_px, glow_junction_clusters=sk_j)
        out.update(glow_components=len(comps), glow_vertical_line_share=round(vert / tot, 3), glow_horizontal_rung_share=round(rung / tot, 3), glow_blob_share=round(blob / tot, 3),
                   glow_component_height_median_px=int(np.median(heights)) if heights else 0, glow_component_width_median_px=int(np.median(widths)) if widths else 0,
                   glow_component_height_p90_px=int(np.percentile(heights, 90)) if heights else 0)
    return out


def smoke_metrics(sh):
    dm = sh.diffmask("smoke")
    dp = f"{sh.mask_dir}/{sh.name}.smoke_dry.png"
    if dm is None or not os.path.exists(dp) or dm.sum() < 100:
        return None
    dry = load(dp).astype(float)
    full = sh.px.astype(float)
    dl = np.abs(lum255(full) - lum255(dry))
    mk = dl > 1.5         # pixels the smoke visibly changes (more than 1.5 levels)
    out = dict(card_diff_mask_px=int(dm.sum()), changed_px_gt1p5=int(mk.sum()), frame_share_changed=round(float(mk.mean()), 4))
    if mk.sum() < THRESH["smoke_px_min"]:
        out["note"] = "fewer than %d pixels changed" % THRESH["smoke_px_min"]
        return out
    v = dl[mk]
    out.update(delta_lum_median=round(float(np.median(v)), 2), delta_lum_p95=round(float(np.percentile(v, 95)), 2), delta_lum_p99=round(float(np.percentile(v, 99)), 2), delta_lum_max=round(float(v.max()), 2))
    # edge step the smoke adds: gradient of the frame minus gradient of the same frame without smoke, on the boundary band of the changed region
    def grad(a):
        l = lum255(a)
        gy, gx = np.gradient(l)
        return np.hypot(gx, gy)
    gf, gd = grad(full), grad(dry)
    pad = np.pad(mk, 1, mode="edge")                      # no wrap-around at the frame border: a frame edge is not a smoke edge
    band = (pad[1:-1, 1:-1] ^ pad[:-2, 1:-1]) | (pad[1:-1, 1:-1] ^ pad[2:, 1:-1]) | (pad[1:-1, 1:-1] ^ pad[1:-1, :-2]) | (pad[1:-1, 1:-1] ^ pad[1:-1, 2:])
    pb = np.pad(band, 1, mode="constant")
    band = band | pb[:-2, 1:-1] | pb[2:, 1:-1] | pb[1:-1, :-2] | pb[1:-1, 2:]
    band[:3, :] = False; band[-3:, :] = False; band[:, :3] = False; band[:, -3:] = False      # gradients at the frame border are one-sided
    step_all = np.abs(gf - gd)[band]
    smooth = band & (gd <= 3.0)             # the smoke's own edge lies on a smooth backdrop; where the changed region ends at a wall / rock silhouette of the DRY frame the boundary is geometry, not smoke
    step = np.abs(gf - gd)[smooth]
    # INFO (repair round 2, 2026-10-05; NOT a gate input): the same edge step on boundary px whose dry-frame gradient stays <= 3 levels/px within 4 px in every direction, i.e. a boundary that is the smoke's own edge
    # and not a wall / lava-ridge silhouette next to it (the gate above keeps its definition; this only separates the two causes when it fails)
    def _maxf(a, r):
        o = a.copy()
        for d in range(1, r + 1):
            o = np.maximum(o, np.maximum(np.roll(a, d, 0), np.roll(a, -d, 0)))
        a2 = o.copy()
        for d in range(1, r + 1):
            o = np.maximum(o, np.maximum(np.roll(a2, d, 1), np.roll(a2, -d, 1)))
        return o
    clean = band & (_maxf(gd, 4) <= 3.0)
    out["edge_clean_backdrop_px"] = int(clean.sum())
    out["edge_step_p99_clean_backdrop_info"] = round(float(np.percentile(np.abs(gf - gd)[clean], 99)), 2) if clean.sum() >= 50 else None
    out["edge_band_px"] = int(band.sum()); out["edge_band_px_on_smooth_backdrop"] = int(smooth.sum())
    out["edge_step_p99_all_boundary"] = round(float(np.percentile(step_all, 99)), 2) if band.sum() else None
    out["edge_step_p99_levels_per_px"] = round(float(np.percentile(step, 99)), 2) if smooth.sum() >= 50 else None
    out["edge_step_max"] = round(float(step.max()), 2) if smooth.sum() >= 50 else None
    # colour of the plume
    sm = full[mk]; out["smoke_pixel_mean_rgb"] = [round(float(x), 1) for x in sm.mean(0)]
    hh, ss, vv = rgb2hsv(full.astype(np.uint8))
    out["plume_mean_s"] = round(float(ss[mk].mean()), 3)
    # translucency (info only, not a gate threshold; repair round 1): how much of the backdrop's own detail (high-pass luminance of the smoke-off frame) still shows through the plume interior.
    # an opaque grey ball would give transmission ~0 and correlation ~0; a wisp keeps the wall / sky structure.
    try:
        from PIL import ImageFilter
        def hp(a):
            im = Image.fromarray(np.clip(lum255(a), 0, 255).astype(np.uint8))
            return lum255(a) - np.asarray(im.filter(ImageFilter.GaussianBlur(3)), dtype=float)
        # interior = changed pixels whose 9x9 neighbourhood is all changed
        k = np.ones(9)
        cs = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 1, mk.astype(float))
        cs = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 0, cs)
        inner = cs >= 80.5
        hd, hf = hp(dry), hp(full)
        # only where the dry frame has detail worth seeing through (local sd > 2 levels)
        det = inner & (np.abs(hd) > 2.0)
        if det.sum() >= 500:
            out["through_px"] = int(det.sum())
            out["through_corr"] = round(float(np.corrcoef(hd[det], hf[det])[0, 1]), 3)
            out["transmission_est"] = round(float(np.dot(hd[det], hf[det]) / np.dot(hd[det], hd[det])), 3)   # regression slope full-detail on dry-detail = 1 - effective alpha
    except Exception as e:                                  # info only
        out["through_err"] = str(e)[:80]
    return out


def ball_metrics(sh):
    b = sh.meta.get("ball")
    if not b or b["radius_px"] < 3 or b["distance_yd"] <= 0:
        return None
    dm = sh.diffmask("ball")
    cx, cyb = b["centre_px"]; cy = H - cyb
    yy, xx = np.mgrid[0:H, 0:W]
    r = b["radius_px"]
    disc = (xx - cx) ** 2 + (yy - cy) ** 2 <= (1.3 * r) ** 2
    vis = int((dm & disc).sum()) if dm is not None else None
    exp = math.pi * r * r
    out = dict(centre_px=[round(cx, 1), round(cy, 1)], radius_px=round(r, 2), expected_px=int(exp), visible_px_in_1p3r_disc=vis, visible_ratio=round(vis / exp, 3) if vis is not None else None)
    # what is the ball sitting on / next to: ID categories in the ring 1.6 r .. 3 r
    ring = ((xx - cx) ** 2 + (yy - cy) ** 2 <= (3 * r) ** 2) & ((xx - cx) ** 2 + (yy - cy) ** 2 >= (1.6 * r) ** 2)
    comp = {}
    for c in sh.meta["id_colors"]:
        m = sh.idmask(c)
        if m is not None and (m & ring).sum() > 0:
            comp[c] = round(float((m & ring).sum() / ring.sum()), 3)
    out["ring_categories"] = comp
    # ball colour vs ground colour contrast (luminance)
    if dm is not None and (dm & disc).sum() > 20:
        l = lum255(sh.px.astype(float))
        out["ball_lum_mean"] = round(float(l[dm & disc].mean()), 1)
        out["ring_lum_mean"] = round(float(l[ring].mean()), 1)
    return out


def surf_metrics(sh):
    """no continuous white surf band: components of the surf mask (diff + ID) in the frame"""
    m = sh.diffmask("surf")
    ids = sh.idmask("surf")
    out = {}
    if ids is not None:
        out["id_surf_px"] = int(ids.sum()); out["id_surf_share_of_frame"] = round(float(ids.mean()), 5)
        comps = components(ids, 20)
        if comps:
            ext = [max(c[1].max() - c[1].min(), c[2].max() - c[2].min()) + 1 for c in comps]
            out["id_surf_components"] = len(comps); out["id_surf_longest_px"] = int(max(ext)); out["id_surf_longest_share_of_frame_h"] = round(float(max(ext) / H), 3)
    if m is not None:
        out["diff_surf_px"] = int(m.sum())
    return out


# ----------------------------------------------------------------------------- gates
GATES = collections.OrderedDict()


def gate(name, ok, detail, numbers=None):
    GATES[name] = dict(result=("PASS" if ok is True else "FAIL" if ok is False else "NOT MEASURED"), detail=detail, numbers=numbers or {})


def main():
    shots = build_shots()
    pipelines = {k: v for k, v in shots.items() if k.startswith("_pipeline_")}
    S = {k: v for k, v in shots.items() if not k.startswith("_pipeline_")}
    stats_path = ART + "/stills_stats.json"
    stats = json.load(open(stats_path)) if os.path.exists(stats_path) else {}
    M = dict(meta=dict(stills_dir=os.path.relpath(ART, R), pipeline_stills=stats.get("pipeline"), quality_level=stats.get("qualityLevel"), unity=stats.get("unity"), pipeline_masks=pipelines,
                       thresholds=THRESH, note="mask-based statistics read masks/<k>/<name>.full.png (the frame the masks were made from); it equals the proof still except for animated water pixels (consistency per shot below)"),
             shots={}, mesh=None, gates=None)
    for n, sh in S.items():
        d = dict(consistency_full_vs_proof_still=sh.consistency)
        d["grass"] = grass_metrics(sh)
        d["flat"] = flat_metrics(sh)
        d["shelf"] = shelf_metrics(sh)
        if sh.hole == 10:
            d["lava"] = lava_metrics(sh); d["basalt"] = basalt_metrics(sh); d["smoke"] = smoke_metrics(sh)
        d["ball"] = ball_metrics(sh)
        d["surf"] = surf_metrics(sh)
        M["shots"][n] = d
        print("measured", n, flush=True)
    mesh = json.load(open(P + "/mesh_checks.json")) if os.path.exists(P + "/mesh_checks.json") else None
    M["mesh"] = mesh

    # baseline flat stills for contrast (jpg from the paused pass, flat colour materials)
    base = {}
    for f in sorted(glob.glob(R + "/work/postcard-look/baseline/hole*_*.jpg")):
        a = np.asarray(Image.open(f).convert("RGB").resize((W, H)))
        lum = lum255(a.astype(float))
        lower = lum[int(H * 0.4):]
        fs, msd, _ = flat_share(lower / 255.0)
        qq = (a // 16).astype(np.int32).reshape(-1, 3); kk = qq[:, 0] * 256 + qq[:, 1] * 16 + qq[:, 2]
        base[os.path.basename(f)] = dict(lower60_lum_sd=round(float(lower.std()), 2), flat_window_share=round(fs, 3), largest_colour_cell_share=round(float(np.bincount(kk, minlength=4096).max() / kk.size), 3))
    M["baseline_flat_stills"] = base

    # ---------------- GRASS_HUE_GAMEVIEW per hole
    for hole in (8, 9, 10):
        rows, ok_all = [], True
        for n in sorted(k for k in S if S[k].hole == hole and (k.endswith("_tee") or k.endswith("_approach"))):
            g = M["shots"][n]["grass"]
            cl = g["central_lower_third"]
            fg = [g[c] for c in ("fairway", "green") if c in g and g[c].get("pixels", 0) >= 50]
            lo, hi = THRESH["grass_hue"]
            ok = lo <= cl["hue"] <= hi
            line = f"{n}: central lower third mean {hex_of(cl['mean_rgb'])} h{cl['hue']} S{cl['s']} V{cl['v']}"
            if fg:
                tot = sum(x["pixels"] for x in fg)
                hue_m = sum(x["hue_of_mean"] * x["pixels"] for x in fg) / tot
                clip = sum(x["clip_any_ch_250"] * x["pixels"] for x in fg) / tot
                ok = ok and lo <= hue_m <= hi and clip <= THRESH["grass_clip_max"]
                line += f"; fairway+green px {tot} mean hue {hue_m:.1f} (median " + "/".join(str(x["hue_median"]) for x in fg) + f"), clipped(any ch>=250) {clip * 100:.1f}%"
            else:
                ok = False; line += "; no fairway/green pixels"
            rows.append(line); ok_all = ok_all and ok
        rough_txt = []
        for n in sorted(k for k in S if S[k].hole == hole):
            g = M["shots"][n]["grass"]
            for c in ("rough", "scrub"):
                if c in g and g[c].get("pixels", 0) >= 2000:
                    rough_txt.append(f"{n} {c} {g[c]['pixels']}px h{g[c]['hue_of_mean']} S{g[c]['s']} V{g[c]['v']}")
        gate(f"GRASS_HUE_GAMEVIEW hole{hole:02d}", ok_all, "; ".join(rows) + f"; target fairway/green h{THRESH['grass_hue'][0]:.0f}..{THRESH['grass_hue'][1]:.0f} (stills h64-73), clip <= {THRESH['grass_clip_max'] * 100:.0f}%" + (" | info: " + "; ".join(rough_txt) if rough_txt else ""))

    # ---------------- NOT_FLAT_PER_STILL
    # per still: lower-60% luminance sd >= 12 and no single 16-level colour cell > 50 % of the frame (the flat baseline stills: sd 0.4..6.9); the six address stills (tee / approach) must also meet the
    # LOOK_STILLS_TEXTURED floor of postcard_look_verify (<= 15 % flat 8 px windows in the lower 60 %): it is defined for those two shots per hole; the landmark close-ups are reported, not gated, on it
    rows, ok_all, fails = [], True, []
    for n in SHOTS9:
        if n not in S:
            continue
        f = M["shots"][n]["flat"]
        address = n.endswith("_tee") or n.endswith("_approach")
        c1 = f["lower60_lum_sd"] >= THRESH["lum_sd_min"]
        c2 = f["largest_colour_cell_share"] <= 0.50
        c3 = (f["flat_window_share"] <= THRESH["flat_max"]) if address else True
        ok = c1 and c2 and c3
        if not ok:
            fails.append(n)
        ok_all = ok_all and ok
        why = [] if ok else [w for w, c in (("lum sd < 12", c1), ("one colour cell > 50%", c2), (f"flat windows {f['flat_window_share'] * 100:.1f}% > {THRESH['flat_max'] * 100:.0f}% (LOOK_STILLS_TEXTURED floor)", c3)) if not c]
        rows.append(f"{n}: lower-60% lum sd {f['lower60_lum_sd']}, flat 8px windows {f['flat_window_share'] * 100:.1f}%{'' if address else ' (landmark: info)'}, largest colour cell {f['largest_colour_cell_share'] * 100:.0f}%, {f['colour_cells_ge_1pct']} colour cells >= 1% {'ok' if ok else 'FAIL: ' + '; '.join(why)}")
    bl = "; flat baseline stills for contrast: " + ", ".join(f"{k.split('.')[0]} sd {v['lower60_lum_sd']} flat {v['flat_window_share'] * 100:.0f}% cell {v['largest_colour_cell_share'] * 100:.0f}%" for k, v in list(base.items())[:9])
    gate("NOT_FLAT_PER_STILL", ok_all, f"(sd >= {THRESH['lum_sd_min']:.0f}, largest colour cell <= 50%, address stills flat windows <= {THRESH['flat_max'] * 100:.0f}%; failing: {fails or 'none'}) " + " | ".join(rows) + bl)

    # ---------------- SHELF_NOT_LOUDEST
    rows, ok_all, any_shelf = [], True, False
    for n in ["hole08_aerial", "hole09_aerial"] + SHOTS9[:6]:
        if n not in S:
            continue
        sh_ = M["shots"][n]["shelf"]
        if sh_.get("shelf_px", 0) < 300:
            rows.append(f"{n}: shelf {sh_.get('shelf_px', 0)} px (< 300: not measurable here)")
            continue
        any_shelf = True
        t2 = sh_.get("top2_share_shelf", 0.0)
        ratio = sh_.get("shelf_vs_ocean_lum")
        hue = sh_["shelf_hue"]
        ok = t2 <= THRESH["shelf_top2_max"] and (ratio is None or ratio <= THRESH["shelf_vs_sea_max"]) and sh_.get("top2_share_turquoise", 0) <= THRESH["shelf_top2_max"]
        ok_all = ok_all and ok
        rows.append(f"{n}: shelf {sh_['shelf_px']} px = {sh_['shelf_share_of_frame'] * 100:.2f}% of the frame, mean {hex_of(sh_['shelf_mean_rgb'])} h{hue} V{sh_['shelf_v']} lum {sh_['shelf_lum_mean']}, ocean beside it lum {sh_.get('ocean_lum_mean')}, ratio {ratio}, shelf = {t2 * 100:.1f}% and turquoise = {sh_.get('top2_share_turquoise', 0) * 100:.1f}% of the brightest 2% (lum >= {sh_['top2_lum_cut']}), brightest 2% is sky/other {sh_['top2_share_other_or_sky'] * 100 if sh_['top2_share_other_or_sky'] is not None else 'n/a'}%, surf {sh_.get('top2_share_surf', 0) * 100:.1f}%, ocean {sh_.get('top2_share_ocean', 0) * 100:.1f}% {'ok' if ok else 'FAIL'}")
    gate("SHELF_NOT_LOUDEST", ok_all if any_shelf else None, f"(shelf <= {THRESH['shelf_top2_max'] * 100:.0f}% of the brightest 2%, <= {THRESH['shelf_vs_sea_max']} x the open sea) " + " | ".join(rows))

    # ---------------- LAVA_ORANGE_AND_BRIGHT
    rows, ok_all, n_l = [], True, 0
    for n in ("hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim", "hole10_aerial"):
        if n not in S:
            continue
        l = M["shots"][n].get("lava")
        if not l:
            rows.append(f"{n}: lava < 500 px in frame"); continue
        n_l += 1
        proof = n != "hole10_aerial"
        ok = l["in_band_hue8_28_s75_v70"] >= THRESH["lava_band"] and l["g_ge_250"] <= THRESH["lava_gclip_max"] and l["dark_v_lt_040"] <= THRESH["lava_dark_max"] and l["mean_v"] >= THRESH["lava_meanV_min"]
        if proof or n == "hole10_aerial":
            ok_all = ok_all and ok if proof else ok_all
        rows.append(f"{n}{'' if proof else ' (extra aerial, info)'}: lava {l['pixels']} px ({l['share_of_frame'] * 100:.1f}% of frame) mean {hex_of(l['mean_rgb'])} h{l['mean_hue']} S{l['mean_s']} V{l['mean_v']}, in band (h8-28 S>=.75 V>=.7) {l['in_band_hue8_28_s75_v70'] * 100:.1f}% (h+S only {l['in_band_hue_s_only'] * 100:.1f}%), dark V<.40 {l['dark_v_lt_040'] * 100:.1f}%, G>=250 {l['g_ge_250'] * 100:.1f}%, cream {l['cream_min_ch_ge_230'] * 100:.2f}%, dark components {l.get('dark_components')} largest {l.get('dark_largest_px')} px ({l.get('dark_largest_share_of_lava', 0) * 100:.2f}% of the lava) {'ok' if ok else 'FAIL'}")
    gate("LAVA_ORANGE_AND_BRIGHT", (ok_all if n_l else None), f"(in band >= {THRESH['lava_band'] * 100:.0f}%, G>=250 <= {THRESH['lava_gclip_max'] * 100:.0f}%, dark V<.40 <= {THRESH['lava_dark_max'] * 100:.0f}%, mean V >= {THRESH['lava_meanV_min']}; crater.jpg pool (212,62,14) h15 S.93 V.83) " + " | ".join(rows))

    # ---------------- BASALT_JOINTS
    rows, ok_all, n_b = [], True, 0
    jn_sk = jn_cl = 0
    for n in ("hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim", "hole10_aerial"):
        if n not in S:
            continue
        b = M["shots"][n].get("basalt")
        if not b:
            continue
        n_b += 1
        proof = n != "hole10_aerial"
        ok = basalt_shot_ok(b)      # round 3: colour ceiling + not streak-only (the old vertical-line FLOOR is gone, see basalt_shot_ok)
        if proof:
            ok_all = ok_all and ok
            jn_sk += b.get("glow_skeleton_px", 0); jn_cl += b.get("glow_junction_clusters", 0)
        rows.append(f"{n}{'' if proof else ' (extra aerial, info)'}: basalt {b['pixels']} px, non-glow mean {hex_of(b['base_mean_rgb'])} h{b['base_hue']} S{b['base_s']} V{b['base_v']} median lum {b['base_lum_median']}, glow {b['glow_coverage'] * 100:.1f}% of basalt in {b.get('glow_components')} components (vertical-line {b.get('glow_vertical_line_share', 0) * 100:.0f}%, horizontal-rung {b.get('glow_horizontal_rung_share', 0) * 100:.0f}%, blob {b.get('glow_blob_share', 0) * 100:.0f}%, median height {b.get('glow_component_height_median_px')} px x width {b.get('glow_component_width_median_px')} px), glow mean {hex_of(b['glow_mean_rgb']) if 'glow_mean_rgb' in b else 'n/a'} h{b.get('glow_mean_hue')} {'ok' if ok else 'FAIL'}")
    jn_rate = 100.0 * jn_cl / jn_sk if jn_sk else 0.0
    jn_ok = basalt_network_ok(jn_sk, jn_cl)
    rows.append(f"joint network (all proof shots): {jn_cl} skeleton junction clusters on {jn_sk} skeleton px = {jn_rate:.2f} per 100 px (>= {THRESH['basalt_junction_per100_min']}; crater.jpg wall crops 8.3-8.8) {'ok' if jn_ok else 'FAIL'}")
    gate("BASALT_JOINTS", ((ok_all and jn_ok) if n_b else None), f"(glow <= {THRESH['basalt_glow_cov_max'] * 100:.0f}% of the basalt, non-glow median lum <= {THRESH['basalt_median_lum_max']}, non-glow mean S <= {THRESH['basalt_base_s_max']}, glow in vertical lines <= {THRESH['basalt_vert_share_max'] * 100:.0f}% (not streak-only), horizontal rungs <= {THRESH['basalt_rung_share_max'] * 100:.0f}%, branching joints >= {THRESH['basalt_junction_per100_min']} junctions per 100 skeleton px; crater.jpg basalt (26,25,29) S .10) " + " | ".join(rows))

    # ---------------- SMOKE_SOFT
    rows, ok_all, n_s = [], True, 0
    for n in ("hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim", "hole10_aerial"):
        if n not in S:
            continue
        s = M["shots"][n].get("smoke")
        if not s:
            continue
        if "delta_lum_p95" not in s:
            rows.append(f"{n}: {s.get('note', 'no smoke')} (card mask {s['card_diff_mask_px']} px, changed {s['changed_px_gt1p5']} px)"); continue
        proof = n != "hole10_aerial"
        if s["edge_step_p99_levels_per_px"] is None:
            rows.append(f"{n}: smoke changes {s['changed_px_gt1p5']} px, |dLum| p95 {s['delta_lum_p95']} max {s['delta_lum_max']}, edge not measurable ({s['edge_band_px_on_smooth_backdrop']} boundary px on a smooth backdrop < 50: the changed region ends at wall silhouettes / the frame border; edge step over ALL boundary px p99 {s['edge_step_p99_all_boundary']}), plume mean {hex_of(s['smoke_pixel_mean_rgb'])} (info, not gated)")
            continue
        n_s += 1
        ok = (s["delta_lum_p95"] >= THRESH["smoke_dp95_min"] and s["edge_step_p99_levels_per_px"] <= THRESH["smoke_edge_p99_max"] and s["delta_lum_max"] <= THRESH["smoke_dmax_max"])
        if proof:
            ok_all = ok_all and ok
        rows.append(f"{n}{'' if proof else ' (extra aerial, info)'}: smoke changes {s['changed_px_gt1p5']} px ({s['frame_share_changed'] * 100:.2f}% of frame), |dLum| median {s['delta_lum_median']} p95 {s['delta_lum_p95']} p99 {s['delta_lum_p99']} max {s['delta_lum_max']}, edge step p99 {s['edge_step_p99_levels_per_px']} levels/px over {s['edge_band_px_on_smooth_backdrop']} boundary px on a smooth backdrop (all boundary px: {s['edge_step_p99_all_boundary']}; info, boundary px with a clean backdrop within 4 px: p99 {s.get('edge_step_p99_clean_backdrop_info')} over {s.get('edge_clean_backdrop_px')} px), plume mean {hex_of(s['smoke_pixel_mean_rgb'])}, see-through (info) backdrop detail kept {s.get('transmission_est')} (corr {s.get('through_corr')}, {s.get('through_px')} px) {'ok' if ok else 'FAIL'}")
    gate("SMOKE_SOFT", (ok_all if n_s else None), f"(visible dLum p95 >= {THRESH['smoke_dp95_min']}, max <= {THRESH['smoke_dmax_max']}, edge step p99 <= {THRESH['smoke_edge_p99_max']} levels/px) " + " | ".join(rows))

    # ---------------- mesh level
    if mesh:
        rows, ok_all = [], True
        for h in ("hole8", "hole9", "hole10"):
            pl = mesh[h]["plants"]; vn = mesh[h]["vines"]
            ok = pl["on_sea"] == 0 and pl["no_hit_at_all"] == 0 and pl["floating_no_surface_1m"] == 0
            ok_all = ok_all and ok
            rows.append(f"{h}: {pl['plants']} PLANT_ objects (incl. {vn['count']} vines): {pl['on_sea']} on the sea, {pl['floating_no_surface_1m']} floating (no surface within 1 m under the base), support {mesh[h]['plants_support_by_surface']}" + (f"; vines judged by root: {vn['attached']} attached (root <= 0.6 m from rock/ground), {vn['unattached']} root 0.6..{vn['root_gap_max_m']:.2f} m off {vn['unattached_names']}, lowest vine tip {vn['bottom_above_sea_min_m']:.2f} m above the sea" if vn["count"] else ""))
        gate("NO_PLANT_ON_SEA", ok_all, "installed FBX, ray down from each plant base through every non-plant mesh: " + " | ".join(rows))
        rows, ok_all = [], True
        for h in ("hole8", "hole9", "hole10"):
            r = mesh[h]["rocks"]
            ok = r["count_anisotropy_gt_2"] == 0 and r["count_scale_gt_2"] == 0 and r["count_scale_lt_0p4"] == 0
            ok_all = ok_all and ok
            rows.append(f"{h}: {r['objects']} ROCK_ objects, object scale {r['scale_min']}..{r['scale_max']}, anisotropy max {r['anisotropy_max']} (worst {r['anisotropy_worst'][0][1] if r['anisotropy_worst'] else ''}), > 2x: {r['count_scale_gt_2']} abs / {r['count_anisotropy_gt_2']} aniso, < 0.4: {r['count_scale_lt_0p4']}")
        gate("NO_ROCK_STRETCH_2X", ok_all, "installed FBX object scales (open-shell cliff / wall skins carry their stretch in the vertices: postcard_look_verify NO_ROCK_STRETCH_2X judges those): " + " | ".join(rows))
        rows, ok_all = [], True
        for h in ("hole8", "hole9", "hole10"):
            m = mesh[h]
            ok = not m["foam_named_objects"] and not m["foam_materials"] and not m["legacy_materials"]
            ok_all = ok_all and ok
            sf = m["materials"].get("LK_SURF")
            rows.append(f"{h}: foam-named objects {m['foam_named_objects']}, foam materials {m['foam_materials']}, legacy MAT_ {m['legacy_materials']}, LK_SURF slots {sf}")
        for n in ("hole08_aerial", "hole09_aerial", "hole08_1_tee", "hole09_2_approach"):
            if n in S:
                s = M["shots"][n]["surf"]
                if "id_surf_longest_px" in s:
                    rows.append(f"{n}: surf patches {s['id_surf_components']}, longest {s['id_surf_longest_px']} px = {s['id_surf_longest_share_of_frame_h'] * 100:.1f}% of the frame height, surf {s['id_surf_share_of_frame'] * 100:.2f}% of the frame")
        gate("NO_FOAM_STRIP", ok_all, "installed FBX names / materials + surf patches in the aerials: " + " | ".join(rows))
        h8 = mesh["hole8"]["path"]
        ok_mesh = h8["max_cm"] is not None and h8["max_cm"] <= THRESH["path_max_cm"]
        balls = []
        ok_px = True
        for n in ("hole08_1_tee", "hole08_2_approach", "hole08_4_pathball"):
            if n in S:
                b = M["shots"][n]["ball"]
                if b:
                    ok_px = ok_px and b["visible_ratio"] is not None and b["visible_ratio"] >= THRESH["ball_visible_min"]
                    balls.append(f"{n}: ball radius {b['radius_px']} px, visible {b['visible_px_in_1p3r_disc']} / {b['expected_px']} expected px (ratio {b['visible_ratio']}), ring {b['ring_categories']}, ball lum {b.get('ball_lum_mean')} vs ring {b.get('ring_lum_mean')}")
        gate("PATH_UNDER_BALL", ok_mesh and ok_px, f"installed hole 8 FBX: {h8['objects']} path meshes, {h8['samples']} up-facing vertices, height over the play surface max {h8['max_cm']} cm / p99 {h8['p99_cm']} cm / mean {h8['mean_cm']} cm (limit {THRESH['path_max_cm']} cm, {h8['above_1p5cm']} above; game ball radius {h8['ball_radius_cm']} cm; before: up to 11 cm) | " + " | ".join(balls))
    else:
        for g in ("NO_PLANT_ON_SEA", "NO_ROCK_STRETCH_2X", "NO_FOAM_STRIP", "PATH_UNDER_BALL"):
            gate(g, None, "mesh_checks.json missing")
    M["gates"] = GATES
    json.dump(M, open(P + "/metrics.json", "w"), indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item())
    write_md(M)
    for k, v in GATES.items():
        print(f"GATE: {k} {v['result']} - {v['detail'][:600]}")


def write_md(M):
    L = ["# POSTCARD_LOOK area I: measurements from the Game-view pixels (and the installed FBX)", "",
         f"Stills: `{M['meta']['stills_dir']}` (900x1600, pipeline asset **{M['meta']['pipeline_stills']}**, quality level {M['meta']['quality_level']}, Unity {M['meta']['unity']}). Masks: `proof/masks/` (PostcardProofMasks, same frames; ID render = exact per-material masks).",
         "Mask statistics read `masks/<k>/<name>.full.png`; it equals the proof still except for animated water (table below). Thresholds: `measure.py` THRESH (the user's lines, the runtime gates' own limits). Re-run: `run_proof.sh metrics`.", "",
         "## Gates", "", "| gate | result | numbers |", "|---|---|---|"]
    for k, v in M["gates"].items():
        L.append(f"| {k} | **{v['result']}** | {v['detail'].replace('|', '/')} |")
    L += ["", "## Frame consistency (mask-run frame vs the proof still; the sea moves from run to run, so the right-hand columns leave the water pixels out)", "", "| shot | max channel diff | share of pixels with sum diff > 8 | water share of the frame | max channel diff without water | share > 8 without water |", "|---|---|---|---|---|---|"]
    for n, d in M["shots"].items():
        c = d["consistency_full_vs_proof_still"]
        if c:
            L.append(f"| {n} | {c['max_abs_channel_diff']} | {c['frac_px_sum_diff_gt8'] * 100:.2f}% | " + (f"{c['water_px_share'] * 100:.1f}% | {c['max_abs_channel_diff_without_water']} | {c['frac_px_sum_diff_gt8_without_water'] * 100:.2f}% |" if "water_px_share" in c else "- | - | - |"))
    L += ["", "## Per shot", ""]
    for n, d in M["shots"].items():
        L.append(f"### {n}")
        g = d["grass"]; cl = g["central_lower_third"]
        L.append(f"- central lower third: {hex_of(cl['mean_rgb'])} hue {cl['hue']} S {cl['s']} V {cl['v']}")
        for c in ("fairway", "green", "rough", "scrub"):
            if c in g and g[c].get("pixels", 0) >= 50:
                x = g[c]
                L.append(f"- {c} (ID mask, lower 60%): {x['pixels']} px, mean {hex_of(x['mean_rgb'])} hue {x['hue_of_mean']} (median {x['hue_median']}, p10 {x['hue_p10']}, p90 {x['hue_p90']}) S {x['s']} V {x['v']}, clipped {x['clip_any_ch_250'] * 100:.1f}%")
        f = d["flat"]
        L.append(f"- flatness: lower-60% luminance sd {f['lower60_lum_sd']} (mean {f['lower60_lum_mean']}), flat 8 px windows {f['flat_window_share'] * 100:.1f}%, colour cells >= 1%: {f['colour_cells_ge_1pct']}, largest cell {f['largest_colour_cell_share'] * 100:.0f}%, kinds {f['id_kinds_ge_1pct']}")
        for k in ("shelf", "lava", "basalt", "smoke", "ball", "surf"):
            if d.get(k):
                L.append(f"- {k}: `{json.dumps(d[k], default=str)}`")
        L.append("")
    if M.get("baseline_flat_stills"):
        L += ["## Flat baseline stills (the paused pass, for contrast)", "", "| still | lower-60% lum sd | flat windows |", "|---|---|---|"]
        for k, v in M["baseline_flat_stills"].items():
            L.append(f"| {k} | {v['lower60_lum_sd']} | {v['flat_window_share'] * 100:.0f}% |")
    open(P + "/METRICS.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
