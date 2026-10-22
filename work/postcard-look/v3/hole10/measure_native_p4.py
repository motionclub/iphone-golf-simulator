#!/usr/bin/env python3
"""Collect staged P4 native RGB/semantic-mask evidence; never launch an application.

The legacy basalt algorithms and thresholds are imported byte-for-byte. Tee and
approach are authoritative, aerials diagnostic. SMOKE/LAVA are FAIL/unmeasured:
FixtureCapture does not supply their original category and dry-frame inputs.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image

MEASURE_SHA256 = "2fe4ca728a0fbc3e0b6d1a2fe07dcc808b6572a82407d5d7d3fb3a22d049fab7"
AUTHORITATIVE = ("hole10_1_tee", "hole10_2_approach")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ExactBasaltShot:
    """Only the interface used by the unchanged basalt_metrics function."""
    def __init__(self, name, rgb, mask):
        self.name = name
        self.hole = 10
        self.px = rgb
        self._mask = mask

    def idmask(self, category):
        if category != "basalt":
            raise ValueError("This shim supplies exact LK_BASALT only")
        return self._mask


def collect_row(folder, name, measure):
    row = {"shot": name, "input": str(folder), "authority": name in AUTHORITATIVE,
           "status": "FAIL", "reason": "Native input not measured", "metrics": None,
           "basaltPixels": None, "files": {}, "semanticControl": None}
    try:
        paths = {"full": folder / (name + ".full.png"),
                 "basalt": folder / (name + ".basalt.png"),
                 "frameProof": folder / (name + ".v3_frame_proof.json")}
        for role, path in paths.items():
            row["files"][role] = {"path": str(path), "exists": path.is_file()}
            if path.is_file():
                row["files"][role].update(bytes=path.stat().st_size, sha256=sha(path))
        missing = [role for role, path in paths.items() if not path.is_file()]
        if missing:
            raise ValueError("Missing native inputs: " + ", ".join(missing))
        proof = json.loads(paths["frameProof"].read_text())
        row["semanticControl"] = {
            key: proof.get(key) for key in ("tool", "unityProject", "unity", "graphicsAPI",
                "shot", "hole", "width", "height", "frame", "cameraPosition", "cameraRotation",
                "fov", "applicationIsPlaying", "gameTime", "timeScale", "fullRgbSha256",
                "idOcclusion", "landmarks", "channel", "basalt", "cliff", "bands", "costs")}
        row["semanticControl"]["rendererInventoryCount"] = len(proof.get("rendererInventory", []))
        if proof.get("shot") != name or proof.get("hole") != 10:
            raise ValueError("Native semantic shot/hole identity mismatch")
        if (proof.get("width"), proof.get("height")) != (900, 1600):
            raise ValueError("Native semantic frame must be 900x1600")
        category = proof.get("basalt") or {}
        if not category.get("exactMembership") or "LK_BASALT" not in category.get("maskKind", ""):
            raise ValueError("No exact LK_BASALT slot-membership provenance")
        if category.get("file") != paths["basalt"].name:
            raise ValueError("Basalt bitmap does not match semantic JSON filename")
        rgb = np.asarray(Image.open(paths["full"]).convert("RGB"), dtype=np.uint8)
        bitmap = np.asarray(Image.open(paths["basalt"]).convert("RGB"), dtype=np.uint8)
        if rgb.shape != (1600, 900, 3) or bitmap.shape != rgb.shape:
            raise ValueError("Native RGB and exact bitmap must both be 900x1600")
        if not np.all(bitmap == bitmap[..., :1]) or not np.isin(bitmap[..., 0], [0, 255]).all():
            raise ValueError("Basalt bitmap is not the exact binary semantic output")
        mask = bitmap[..., 0] > 127
        row["basaltPixels"] = int(mask.sum())
        if category.get("pixels") != row["basaltPixels"]:
            raise ValueError("Exact bitmap pixel count does not match semantic JSON")
        # PNG and Unity GetPixels32 have opposite row origins. Accept either
        # exact byte-order correspondence, with the matched orientation recorded.
        # No colour conversion, gamma adjustment, resize or luminance selection.
        hashes = {"PNG top-to-bottom": hashlib.sha256(rgb.tobytes()).hexdigest(),
                  "Unity bottom-to-top": hashlib.sha256(rgb[::-1].tobytes()).hexdigest()}
        matched = [orientation for orientation, digest in hashes.items()
                   if digest == proof.get("fullRgbSha256")]
        if not matched:
            raise ValueError("Full PNG RGB bytes differ from native captured RGB hash")
        row["fullRgbHashOrientation"] = matched
        metric = measure.basalt_metrics(ExactBasaltShot(name, rgb, mask))
        if metric is None:
            raise ValueError("Unmeasured: exact basalt support below inherited 2000 pixels")
        json.dumps(metric, allow_nan=False)
        row["metrics"] = metric
        row["status"] = "PASS" if measure.basalt_shot_ok(metric) else "FAIL"
        row["reason"] = "Unmodified inherited per-shot basalt thresholds"
    except Exception as error:
        row["status"] = "FAIL"
        row["reason"] = str(error)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, action="append",
                        help="Native FixtureCapture folder; repeat to retain every capture")
    parser.add_argument("--out", type=Path, required=True, help="New JSON result under v3")
    parser.add_argument("--cfg", type=Path, help="Actual fixture camera JSON; defaults to hole10/aerial_cfg.json")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    args = parser.parse_args()
    root = args.root.resolve()
    v3 = root / "work/postcard-look/v3"
    out = args.out.resolve()
    if not out.is_relative_to(v3) or out.exists() or out.with_suffix(".txt").exists():
        raise SystemExit("Result must be a new JSON/txt pair under actual v3")
    cfg_path = (args.cfg or v3 / "hole10/aerial_cfg.json").resolve()
    cfg = json.loads(cfg_path.read_text())
    configured = [shot["name"] for shot in cfg["shots"] if shot["hole"] == 10]
    if len(configured) != len(set(configured)) or not set(AUTHORITATIVE) <= set(configured):
        raise SystemExit("Actual fixture config must contain unique tee and approach shot names")
    source = v3 / "proof/measure.py"
    if sha(source) != MEASURE_SHA256:
        raise SystemExit("Inherited measure.py changed; refusing algorithm/threshold substitution")
    spec = importlib.util.spec_from_file_location("postcard_unchanged_native_measure", source)
    measure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measure)
    rows = []
    for folder in args.input:
        folder = folder.resolve()
        if not folder.is_relative_to(v3):
            raise SystemExit("Native evidence folder must be under actual v3")
        names = set(configured)
        if folder.is_dir():
            for path in folder.glob("*.v3_frame_proof.json"):
                try:
                    proof = json.loads(path.read_text())
                    if proof.get("hole") == 10 and path.name == proof.get("shot", "") + ".v3_frame_proof.json":
                        names.add(proof["shot"])
                except (ValueError, OSError):
                    if path.name.startswith("hole10"):
                        # Retain malformed extra native rows as diagnostic FAIL.
                        names.add(path.name.removesuffix(".v3_frame_proof.json"))
        rows.extend(collect_row(folder, name, measure) for name in sorted(names))
    authoritative = [row for row in rows if row["authority"]]
    sk = sum((row["metrics"] or {}).get("glow_skeleton_px", 0) for row in authoritative)
    junctions = sum((row["metrics"] or {}).get("glow_junction_clusters", 0) for row in authoritative)
    network_ok = measure.basalt_network_ok(sk, junctions)
    measured_every_required = bool(authoritative) and all(row["metrics"] is not None for row in authoritative)
    basalt_pass = measured_every_required and all(row["status"] == "PASS" for row in authoritative) and network_ok
    basalt = {"gate": "BASALT_JOINTS", "status": "PASS" if basalt_pass else "FAIL",
              "authoritativeShots": list(AUTHORITATIVE), "everyRequiredCaptureMeasured": measured_every_required,
              "network": {"status": "PASS" if network_ok else "FAIL", "skeletonPixels": sk,
                          "junctionClusters": junctions, "junctionsPer100Pixels": 100.0 * junctions / sk if sk else 0.0,
                          "minimumSkeletonPixels": 200,
                          "minimumJunctionsPer100Pixels": measure.THRESH["basalt_junction_per100_min"]},
              "rows": rows, "aerialScope": "Retained raw per-shot diagnostic; not added to tee/approach authority or network denominator"}
    unavailable = "FAIL: native FixtureCapture supplies no correct inherited category/difference/dry-frame inputs; actual P5/P6 masks must measure this gate."
    gates = {"BASALT_JOINTS": basalt,
             "SMOKE_SOFT": {"gate": "SMOKE_SOFT", "status": "FAIL", "measured": False, "reason": unavailable},
             "LAVA_ORANGE_AND_BRIGHT": {"gate": "LAVA_ORANGE_AND_BRIGHT", "status": "FAIL", "measured": False, "reason": unavailable}}
    result = {"generatedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "tool": "measure_native_p4", "status": "PASS" if all(g["status"] == "PASS" for g in gates.values()) else "FAIL",
              "scope": "Staged P4 native Game-camera evidence, not final installed P6 proof. Global repeat/control and semantic results are retained separately; their FAILs are not relabelled by a basalt colour/network measurement.",
              "measureSource": {"path": str(source), "sha256": MEASURE_SHA256,
                                "functions": ["basalt_metrics", "basalt_shot_ok", "basalt_network_ok"],
                                "modified": False},
              "thresholds": measure.THRESH, "fixtureCfg": {"path": str(cfg_path), "sha256": sha(cfg_path)},
              "gates": gates}
    if sha(source) != MEASURE_SHA256:
        raise SystemExit("Inherited measure.py changed during collection; no result written")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = [f"GATE: BASALT_JOINTS {basalt['status']} - tee/approach required; {junctions}/{sk} skeleton junctions/pixels = {basalt['network']['junctionsPer100Pixels']:.3f}/100; inherited >=3/100 and >=200px",
             "GATE: SMOKE_SOFT FAIL - native unmeasured; missing inherited correct category/dry inputs",
             "GATE: LAVA_ORANGE_AND_BRIGHT FAIL - native unmeasured; missing inherited correct category/difference inputs"]
    for row in rows:
        metric = row["metrics"]
        detail = (f"basalt={metric['pixels']}px Ymedian={metric['base_lum_median']} S={metric['base_s']} glow={metric['glow_coverage']} vertical={metric.get('glow_vertical_line_share')} rungs={metric.get('glow_horizontal_rung_share')}" if metric else row["reason"])
        lines.append(f"{row['shot']} {row['status']} {'AUTHORITATIVE' if row['authority'] else 'DIAGNOSTIC'} {row['input']}: {detail}")
    out.with_suffix(".txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
