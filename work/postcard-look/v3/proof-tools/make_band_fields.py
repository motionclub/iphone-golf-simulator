#!/usr/bin/env python3
"""Proof-only: exact float band fields from the LIVE grass generator, not RGB ranks.

Run after all texture edits. The source hash/parameters are saved beside the fields.
No project/Unity assets are written. Float32 arrays are bottom-left texture order.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys

import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=pathlib.Path)
    p.add_argument("--out", required=True, type=pathlib.Path)
    p.add_argument("--size", type=int, default=1024)
    a = p.parse_args()
    src = a.root / "blender/scripts/golf_look_textures.py"
    sys.path.insert(0, str(src.parent))
    spec = importlib.util.spec_from_file_location("proof_grass_generator", src)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    if not g.BAND_P["on"]:
        raise SystemExit("FAIL: the v9 band generator is disabled; do not infer its replacement")
    a.out.mkdir(parents=True, exist_ok=True)
    u, v = g.grid(a.size, a.size)
    b = g.BAND_P
    fw, _ = g.mow_band(u, v, g.SEEDS["Fairway"], b["fw_K"], b["fw_edge"], b["fw_wob"])
    seed = g.SEEDS["Green"]
    gr = g.sm(-b["gr_edge"], b["gr_edge"], np.cos(2 * np.pi * b["gr_K"] * (u + .004 * g.noise(u, v, 3, 5, seed + 1))))
    cross = g.sm(-.2, .2, np.cos(2 * np.pi * 3 * (v + .004 * g.noise(u, v, 5, 3, seed + 2))))
    # generator grid()/PNG rows are TOP-first (v decreases). Texture2D raw rows
    # are BOTTOM-first: the flip is required to match the imported PNG UV mapping.
    files = {}
    for name, field in (("fairway", fw), ("green", gr), ("green_cross", cross)):
        raw = np.ascontiguousarray(np.flipud(field), dtype="<f4").tobytes()
        path = a.out / (name + ".f32")
        path.write_bytes(raw)
        files[name] = dict(path=str(path.resolve()), sha256=hashlib.sha256(raw).hexdigest())
    meta = dict(generator=str(src.resolve()), generator_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                size=a.size, float_format="little-endian float32", texture_origin="bottom-left",
                parameters=b, seeds={k: g.SEEDS[k] for k in ("Fairway", "Green")}, files=files,
                plateau_light_min=.9, plateau_dark_max=.1,
                role="authored primary band membership only; luminance comes from the same Game-view frame")
    (a.out / "band_fields.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
