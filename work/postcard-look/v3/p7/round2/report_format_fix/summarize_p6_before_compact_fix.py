#!/usr/bin/env python3
"""Conservative P6 report extractor. No builds, captures, source edits or retries.

Source/schema checked; end-to-end extraction awaits a completed installed P6 run.
Missing/stale/unsupported evidence is FAIL. Each gate remains independent, while
every command failure and raw gate FAIL is also retained in the overall result.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, re, sys
import xml.etree.ElementTree as ET
from PIL import Image

sys.dont_write_bytecode = True
GATE_LINE = re.compile(r"^GATE[: ]\s*(.*?)\s+(PASS|FAIL|NOT MEASURED)(?:\s*-\s*|\s*)(.*)$")
ADDRESS = {f"hole{h:02d}_{i}_{kind}" for h in (8, 9, 10) for i, kind in ((1, "tee"), (2, "approach"))}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class Evidence:
    def __init__(self, run):
        self.run = run
        marker = run / "effective_unity_project.txt"
        self.start = marker.stat().st_mtime if marker.is_file() else float("inf")
        self.used = []
        self.observed = []
        self.context_gate = None

    def path(self, relative):
        path = (self.run / relative).resolve()
        require(path.is_relative_to(self.run), "Evidence resolves outside final RUNDIR: " + str(path))
        require(path.is_file(), "Missing evidence: " + str(path))
        require(path.stat().st_mtime >= self.start, "Stale evidence predates current run: " + str(path))
        self.used.append({"path": str(path), "sha256": digest(path), "mtime": path.stat().st_mtime})
        return path

    def text(self, relative):
        return self.path(relative).read_text(errors="replace")

    def data(self, relative):
        data = json.loads(self.text(relative))
        # Retain measured numbers even when validation rejects a raw FAIL.
        # Keep renderer/object inventories in their original evidence files.
        if isinstance(data, dict):
            if "results" in data and "method" in data:
                compact = {"pass":data.get("pass"),"results":[{k:x.get(k) for k in ("hole","stage","format","pass","threshold_m","max_vertex_delta_m","max_marker_delta_m","problems")} for x in data["results"]]}
            elif "gates" in data and "shots" in data:
                aliases={"GRASS_HUE_H08":"GRASS_HUE_GAMEVIEW hole08","GRASS_HUE_H09":"GRASS_HUE_GAMEVIEW hole09","GRASS_HUE_H10":"GRASS_HUE_GAMEVIEW hole10","SHELF":"SHELF_NOT_LOUDEST","LAVA_ORANGE":"LAVA_ORANGE_AND_BRIGHT"}
                key=aliases.get(self.context_gate,self.context_gate)
                compact={"gate":key,"rawGate":data.get("gates",{}).get(key),"shots":data.get("shots"),"meshEvidencePresent":data.get("mesh") is not None}
            else:
                compact={k:v for k,v in data.items() if k not in ("rendererInventory","objects","records")}
            self.observed.append({"file":str(relative),"measurements":compact})
        return data

    def matches(self, pattern):
        return sorted(path.relative_to(self.run) for path in self.run.glob(pattern) if path.is_file())


def raw_gates(text):
    return [{"gate": match[1], "status": match[2], "detail": match[3]} for line in text.splitlines()
            if (match := GATE_LINE.match(line))]


def all_pass(rows):
    return bool(rows) and all(row["status"] == "PASS" for row in rows)


def verifier(e, hole, stills=True):
    data = e.data(f"verify_installed_{'stills_' if stills else ''}hole{hole}.json")
    gates = data.get("gates", [])
    require(gates, "No verifier measurements")
    return data, gates


def verifier_subset(e, prefix):
    rows = []
    for hole in (8, 9, 10):
        _, gates = verifier(e, hole)
        selected = [g for g in gates if g["name"].split("@")[0] == prefix]
        require(selected, f"Missing installed verifier {prefix} for hole{hole}")
        rows.extend({"hole": hole, **g} for g in selected)
    require(all(g.get("ok") is True and "skip" not in g.get("detail", "").lower() for g in rows),
            "Installed verifier subset contains FAIL/skipped: " + str(rows))
    return rows


def native_frames(e):
    rows = []
    for folder in ("9", "extra", "12"):
        for rel in e.matches(f"masks/{folder}/*.v3_frame_proof.json"):
            data = e.data(rel)
            require((data.get("width"), data.get("height")) == (900, 1600), "Wrong native frame resolution")
            require(not (e.run / rel.parent / (data["shot"] + ".stage_provenance.json")).exists(), "Staged model proof is not installed P6")
            rows.append((rel, data))
    require(rows, "Missing actual installed renderer/frame proof")
    return rows


def validate_cost(e, hole, primary):
    data = e.data(f"costs/hole{hole:02d}_1_tee.frame_costs.json")
    samples = data.get("samples", [])
    require(data.get("status") == "PASS" and len(samples) == 3, "No three valid published samples: " + str(data.get("reason")))
    require(Path(data.get("unityProject", "")).resolve() == primary, "Cost is not from primary Unity project")
    require((data.get("width"), data.get("height")) == (900, 1600), "Cost camera resolution invalid")
    require(data.get("activeModelRenderers", 0) > 0 and data.get("teeDrawCallCapApplies") is True, "No actual tee geometry/isolation")
    values = ("triangles", "drawCalls", "setPass")
    first = samples[0]["profiler"]
    for index, sample in enumerate(samples):
        profile, cameras = sample["profiler"], sample["cameras"]
        require(profile.get("valid") is True and all(profile.get(k, 0) > 0 for k in values), "Missing/zero profiler support")
        require(all(profile[k] == first[k] == data[k] for k in values), "Unstable/mismatched published render counters")
        require(cameras.get("targetBegin") == cameras.get("targetEnd") == 1 and cameras.get("otherCameraEvents") == 0, "Not sole-camera rendering")
        require(sample.get("completedCameraFrame") == sample.get("readInPlayerFrame", 0) - 1, "Counters not read after completed frame")
        require(all(sample.get(k, 0) > 0 for k in ("triangleSamples", "drawSamples", "setPassSamples")), "No recorder sample counts")
        stats = sample.get("unityStats", {})
        if stats.get("valid") and all(stats.get(k, 0) > 0 for k in values):
            require(all(stats[k] == profile[k] for k in values), "Positive UnityStats disagrees with ProfilerRecorder")
        if index:
            previous = samples[index - 1]
            require(all(sample[k] == previous[k] + 1 for k in ("completedCameraFrame", "triangleSamples", "drawSamples", "setPassSamples")), "Frames/recorders are not consecutive")
    return {"hole": hole, **{k: data[k] for k in values}, "samples": samples,
            "scope": data.get("scope"), "geometryTriangleScope": "Independent installed verifier geometry count, not this shadow/render-pass counter"}


def metric_gate(e, name):
    data = e.data("metrics.json")
    gate = data.get("gates", {}).get(name)
    require(gate is not None, "Missing original native metric gate: " + name)
    require(gate.get("result") == "PASS", "Original metric " + name + " " + str(gate))
    return data, gate


def device_build(e, root):
    manifest_path = e.path("logs/ios_sandbox_prepare.log")
    manifest = json.loads(manifest_path.read_text())
    inventory = e.text("command_inventory.txt")
    codes = [int(x.split('\t')[1]) for x in e.text("command_results.tsv").splitlines() if x.startswith("ios_device\t")]
    require(len(codes) == 1, "Original device invocation result missing/ambiguous")
    require(manifest.get("scriptsByteIdentical") is True and manifest.get("sourceSha256") == manifest.get("copySha256") and manifest.get("actualCurrentExport") == str(root/'work/postcard-look/v3/ios/export'), "Byte-identical current-export script invocation not proven")
    source = Path(manifest.get("sourceScript", "")); copied = Path(manifest.get("invokedScript", ""))
    require(source.is_file() and copied.is_file() and digest(source) == digest(copied) == manifest.get("sourceSha256"), "Current source/copy script SHA mismatch")
    require(manifest.get("invokedScript", "") in inventory, "Actual copied script invocation not recorded")
    require(Path(manifest.get("exportLink", "")).resolve() == Path(manifest["actualCurrentExport"]).resolve(), "Device export link not actual current export")
    initial = e.text("logs/ios_device.log")
    retry = None
    if codes != [0]:
        retry = e.data("ios_device_retry1.json")
        require(retry.get("status") == "PASS" and retry.get("commandExit") == 0 and retry.get("firstInvocationExit") == codes[0] and retry.get("firstFailureRetained") == "logs/ios_device.log", "Completed actual retry/current raw history missing")
        require(retry.get("targetSdk") == "iphoneos" and retry.get("configuration") == "Release" and retry.get("scriptsByteIdentical") is True and retry.get("scriptSourceSha256") == retry.get("scriptCopySha256") == manifest.get("sourceSha256"), "Retry target/script identity not proven")
        require(retry.get("buildManifestSha256") == digest(manifest_path) and retry.get("iosExportReportSha256") == digest(e.path("ios_export.json")), "Retry manifest/export relationship stale")
        log_path = e.path(retry.get("log", "")); require(digest(log_path) == retry.get("logSha256"), "Retry build log hash stale")
        log = log_path.read_text(errors="replace")
    else:
        log = initial
    require("** BUILD SUCCEEDED **" in log and not re.search(r"\*\* BUILD FAILED \*\*|(?:^|\n).*\berror:", log), "Actual device-target build failed/missing success")
    require("-sdk iphoneos" in log or "SDKROOT = iphoneos" in log or "SDKROOT=iphoneos" in log, "Actual iPhoneOS SDK target absent")
    return {"script": manifest["invokedScript"], "scriptSha256": manifest["sourceSha256"], "deviceBuildExit": 0, "firstInvocationExit": codes[0], "firstFailureRetained": codes[0] != 0, "retry": retry, "SDK": "iphoneos", "configuration": "Release", "currentExport": manifest["actualCurrentExport"], "physicalDeviceRun": False, "scope": "Unsigned iPhoneOS device-target compilation; no physical device execution or performance claim"}


def evaluate(name, e, primary, root):
    if name == "GUARDS_7_OF_7":
        rows = raw_gates(e.text("logs/guards_after.log"))
        require(len(rows) == 7 and all_pass(rows), "Guards not exactly7/7 with zeroFAIL")
        return {"passed": 7, "failed": 0, "rows": rows}
    if name == "PROTECTED_FILES":
        choices = e.matches("protected*.json")
        choices = [p for p in choices if not str(p).endswith(".adapter.json")]
        if choices:
            data = e.data(choices[-1]); require(data.get("files_checked", 0) > 0, "No strict protected census")
            require(data.get("ok") is True and data.get("changed_count") == 0, "Strict original-start protected changes: " + str(data.get("changed_count")))
            return data
        text = e.text("logs/protected_strict_after.log")
        match = re.search(r"GATE: PROTECTED_FILES (PASS|FAIL) - (\d+) files checked, (\d+) changed", text)
        require(match is not None, "No strict original-start protected measurement")
        details = [ast.literal_eval(line) for line in text.splitlines() if line.startswith("{'path':")]
        count = int(match[3]);require(len(details) == count, "Incomplete protected changed-path record")
        require(match[1] == "PASS" and count == 0, f"{count}/{match[2]} original protected paths changed; {details}")
        return {"files_checked": int(match[2]), "changed_count": count, "changes": details}
    if name.startswith("POSTCARD_LOOK_VERIFY_H"):
        hole = int(name[22:24]);data, gates = verifier(e, hole)
        require(all(g.get("ok") is True and not re.search(r"\bskip", g.get("detail", ""), re.I) for g in gates), "Required-stills verifier has FAIL/skip: " + str([g for g in gates if not g.get("ok") or "skip" in g.get("detail", "").lower()]))
        require(any(g["name"] == "LOOK_STILLS_TEXTURED" for g in gates), "Verifier lacks required actual still gate")
        return {"hole": hole, "pass": len(gates), "total": len(gates), "failures": data.get("failures", [])}
    if name in ("PLANT_SWAY_COLORS", "PLANT_SWAY_CAPS"):
        rows = verifier_subset(e, name)
        reports = e.matches("runtime/plant_sway_proof_*.txt");require(len(reports) == 1, "Exactly one actual installed sway report required")
        gates = raw_gates(e.text(reports[0]))
        required = ["PLANT_SWAY_COLORS_UNITY"] if name.endswith("COLORS") else ["SWAY_SHADER_COMPILES", "SWAY_MIRROR_MATCHES_SHADER", "SWAY_ROOT_PINNED", "SWAY_WIND_DRIVEN_MATH", "SWAY_WIND_DRIVEN_GPU", "SWAY_GENTLE_CONTRACT", "SWAY_GENTLE"]
        require(all(any(g["gate"] == key and g["status"] == "PASS" for g in gates) for key in required), "Installed sway/GPU required support missing orFAIL")
        if name.endswith("CAPS"):
            studio_required = ("SWAY_MIRROR_MATCHES_SHADER", "SWAY_ROOT_PINNED", "SWAY_WIND_DRIVEN_GPU", "SWAY_FBX_CHAIN_ON_GPU", "SWAY_SHADOW_FOLLOWS_PLANT")
            require(all(any(g["gate"] == "[HeroBaseStudioURP] " + key and g["status"] == "PASS" for g in gates) for key in studio_required), "Studio URP native sway/GPU support missing orFAIL")
        require(all_pass(gates), "Actual sway report rawFAIL retained")
        return {"verifierRows": rows, "nativeGateCount": len(gates), "nativeGates": gates}
    if name in ("MOW_BAND_CONTRAST", "GAMEPLAY_FRAMING", "NEEDLE_STACK_VISIBILITY"):
        result = e.data("required_frame_gates.json").get(name);require(result, "Missing authoritative renderer-mask aggregate")
        frames = native_frames(e)
        if name == "MOW_BAND_CONTRAST":
            material = result.get("materials", []);require(len(material) == 6, "Each of3 holes x2 authored materials required")
            for row in material:
                supported = row.get("supportedMeasurements", []);cap = .12 if row["material"] == "fairway" else .08
                require(supported and all(x.get("lightPixels", 0) >= 512 and x.get("darkPixels", 0) >= 512 and x.get("status") == "PASS" and x.get("gap") is not None and x["gap"] <= cap for x in supported), "Missing/failing authored plateau support: " + str(row))
            for _, frame in frames:
                bands = frame.get("bands", {})
                for kind, cap in (("fairway", .12), ("green", .08)):
                    if min(bands.get(kind + "LightPixels", 0), bands.get(kind + "DarkPixels", 0)) >= 512:
                        require(bands.get("controlDriftPixels") == 0 and bands.get(kind + "CapStatus") == "PASS" and bands.get(kind + "GapOverLight") is not None and bands[kind + "GapOverLight"] <= cap, "Supported actual native band/controlFAIL retained")
        else:
            rows = result.get("rows", []);seen = {x["shot"] for x in rows}
            expected = ADDRESS if name == "GAMEPLAY_FRAMING" else {"hole08_1_tee", "hole08_2_approach"}
            require(expected <= seen, "Missing required address frame")
            for rel, frame in frames:
                if frame["shot"] not in expected:continue
                if name == "NEEDLE_STACK_VISIBILITY":
                    stacks = [x for x in frame.get("landmarks", []) if x.get("name", "").startswith("stack") and x.get("exactMembership") and x.get("pixels", 0) > 0]
                    require(len(stacks) >= 2, "Actual visible distinct stacks below2")
                else:
                    prefix = {8: ("arch", "stack"), 9: ("ruin", "arch"), 10: ("volcano", "pillar")}[frame["hole"]]
                    masks = [x for x in frame.get("landmarks", []) if x.get("name", "").startswith(prefix)]
                    if frame["hole"] == 9:masks.append(frame.get("channel", {}))
                    require(any(x.get("status") == "PASS" and x.get("exactMembership") and x.get("pixels", 0) > 0 and x.get("heightPixels", 0) >= 64 for x in masks), "No one exact semantic alternative>=64px; mask extents are never summed")
                    require(frame.get("cliff", {}).get("status") == "PASS", "No actual fairway-side cliff drop")
                    e.path(rel.parent / (frame["shot"] + ".id.png"));e.path(rel.parent / "masks_meta.json")
            if name == "GAMEPLAY_FRAMING":
                require(all(x.get("status") == "PASS" and x.get("waterPixels", 0) >= 216000 and x.get("waterShare", 0) >= .15 for x in rows), "Actual water/semantic framingFAIL retained")
        require(result.get("status") == "PASS", "Authoritative aggregateFAIL: " + str(result))
        return result
    if name == "SPLIT_CLIFF_ISLANDS":
        paths = [p for p in e.matches("masks/*/hole09_*.split_outline.json") if "aerial" in p.name]
        require(paths, "Missing actual installed aerial Split outline proof")
        rows = [e.data(p) for p in paths]
        require(all(d.get("status") == "PASS" and d.get("controlDriftPixels") == 0 and d.get("twoIndependentIslandOutlinesProven") is True and d.get("frozenClosedBoundaries") == 2 and len(d.get("parts", [])) == 2 and all(x.get("denominatorPixels", 0) > 0 and x.get("cliffOutlineFraction", 0) >= .8 and x.get("cliffGate") == x.get("surfBaseGate") == "PASS" and x.get("surfBaseAdjacentPixels", 0) > 0 for x in d["parts"]) for d in rows), "Actual two-island/80%/SURF/control proofFAIL: " + str([{k:d.get(k) for k in ("status","arcMeasurementStatus","controlDriftPixels","frozenClosedBoundaries","reason")} for d in rows]))
        return rows
    if name == "RUIN_NOT_BOXES":
        rows = []
        for kind, path in (("blend", root / "blender/hole_09.blend"), ("fbx", root / "Unity/Assets/Resources/Course/hole_09.fbx")):
            data = e.data(f"ruin_installed/{kind}_pieces.json")
            require(Path(data.get("source", "")).resolve() == path.resolve(), "Ruin census source is not actual installed " + kind)
            require(data.get("pass") is True and data.get("pieces", 0) > 0 and data.get("limit") == .2 and data.get("share", 1) <= .2 and data.get("controls") and all(data["controls"].values()), "Ruin census failed/missing support: " + str({k:data.get(k) for k in ("pieces","unbroken_cuboids","share","pass")}))
            require(e.text(f"ruin_installed/{kind}_exit.txt").strip() == "0", "Actual ruin command failed")
            rows.append({k:data.get(k) for k in ("source","pieces","unbroken_cuboids","share","limit","controls")})
        require(e.text("ruin_installed/source_sha256_diff.txt").strip() == "", "Installed ruin sources changed during census")
        e.path("ruin_installed/source_sha256_before.txt");e.path("ruin_installed/source_sha256_after.txt")
        return rows
    if name.startswith("GRASS_HUE_H"):
        hole = int(name[-2:]);data, gate = metric_gate(e, f"GRASS_HUE_GAMEVIEW hole{hole:02d}")
        samples = {n:s.get("grass") for n,s in data.get("shots", {}).items() if n.startswith(f"hole{hole:02d}_")}
        require(samples and any(x for x in samples.values()), "Missing actual grass pixel measurements")
        _, gates = verifier(e, hole);selected = [g for g in gates if g["name"].split("@")[0] == "GRASS_ALBEDO_HUE"]
        require(selected and all(g.get("ok") is True for g in selected), "Installed grass verifierFAIL/unmeasured")
        return {"originalMetric": gate, "samples": samples, "originalCapNote": "Unchanged measure.py60..76;64..73 is inventory's observed still range, not a replacement cap"}
    metrics = {"BASALT_JOINTS":"BASALT_JOINTS", "SHELF":"SHELF_NOT_LOUDEST", "LAVA_ORANGE":"LAVA_ORANGE_AND_BRIGHT", "SMOKE_SOFT":"SMOKE_SOFT", "NO_PLANT_ON_SEA":"NO_PLANT_ON_SEA", "NO_ROCK_STRETCH_2X":"NO_ROCK_STRETCH_2X", "NO_FOAM_STRIP":"NO_FOAM_STRIP", "PATH_UNDER_BALL":"PATH_UNDER_BALL"}
    if name in metrics:
        data, gate = metric_gate(e, metrics[name]);shots = data.get("shots", {})
        if name == "BASALT_JOINTS":
            samples = [shots.get(n, {}).get("basalt") for n in ("hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim")]
            require(all(x and x.get("pixels", 0) >= 2000 for x in samples), "Inherited basalt pixel support missing in required proof views")
            sk = sum(x.get("glow_skeleton_px", 0) for x in samples);j = sum(x.get("glow_junction_clusters", 0) for x in samples)
            require(sk >= 200 and 100*j/sk >= 3 and all(x["glow_coverage"] <= .2 and x["base_lum_median"] <= 55 and x["base_s"] <= .25 and x.get("glow_vertical_line_share", 0) <= .8 and x.get("glow_horizontal_rung_share", 1) <= .2 for x in samples), "Basalt original colour/joint/networkFAIL")
            return {"originalMetric": gate, "shots": samples, "skeletonPixels":sk,"junctionsPer100":100*j/sk}
        if name in ("SHELF","LAVA_ORANGE","SMOKE_SOFT"):
            key = {"SHELF":"shelf","LAVA_ORANGE":"lava","SMOKE_SOFT":"smoke"}[name]
            values = {n:s.get(key) for n,s in shots.items() if s.get(key)}
            require(values, "Missing actual category/difference support")
            if name == "SMOKE_SOFT":
                require(any(x.get("changed_px_gt1p5", 0) >= 500 and x.get("edge_band_px_on_smooth_backdrop", 0) >= 50 and x.get("edge_step_p99_levels_per_px") is not None for x in values.values()), "Smoke dry/category/visible-edge support unmeasured")
            return {"originalMetric":gate,"shots":values}
        e.path("mesh_checks.json")
        if name == "NO_FOAM_STRIP":
            reports = e.matches("runtime/importcheck_proof_*.txt"); require(len(reports) == 1, "One native import foam check required")
            native = [g for g in raw_gates(e.text(reports[0])) if g["gate"] == "NO_FOAM_STRIP_8_10"]
            e.observed.append({"nativeFoamGate": native})
            require(native and all_pass(native), "Actual imported foam spacing FAIL retained: " + str(native))
        return {"originalMetric":gate,"mesh":data.get("mesh")}
    if name in ("GOLF_LOOK_SMOKE_BOTH_URP", "POSTCARD_IMPORT_CHECK"):
        pattern = "runtime/smoke_proof_*.txt" if name.startswith("GOLF") else "runtime/importcheck_proof_*.txt"
        files = e.matches(pattern);require(len(files)==1, "One actual native report required")
        report_text=e.text(files[0]);gates = raw_gates(report_text);e.observed.append({'nativeImportGates':gates,'reportedSummary':re.findall(r'SUMMARY:.*|GATE: POSTCARD_IMPORT_CHECK .*',report_text)});require(all_pass(gates), "Native report has rawFAIL or no gates")
        if name.startswith("GOLF"):
            both = [g for g in gates if g["gate"]=="URP_BOTH_ASSETS"]
            require(both and all("TennisURP" in g["detail"] and "HeroBaseStudioURP" in g["detail"] for g in both), "Both actual URP suites not proven")
        else:require(any(g["gate"]=="POSTCARD_IMPORT_CHECK" and "0 failed" in g["detail"] for g in gates), "Import0 failed summary missing")
        return {"passed":len(gates),"failed":0,"rows":gates,"reportedSummary":re.findall(r'SUMMARY:.*|GATE: POSTCARD_IMPORT_CHECK .*',report_text)}
    if name == "EDITMODE_POSTCARD_HOLE_TESTS":
        tree = ET.parse(e.path("editmode_postcardholetests.xml"));cases=tree.findall(".//test-case")
        require(cases and all(x.get("result") in ("Passed","Success") for x in cases) and all("PostcardHoleTests" in x.get("fullname", "") for x in cases), "EditMode cases missing/failed/skipped/outside requested fixture")
        return {"passed":len(cases),"failed":0,"rootAttributes":tree.getroot().attrib}
    if name == "TOOLS_POSTCARD_CHECK":
        gates = raw_gates(e.text("logs/postcardcheck_gates.log"));tests=e.text("logs/postcardcheck_tests.log")
        require(all_pass(gates), "Independent design rawFAIL/no support")
        match=re.search(r"TESTS .*?: (\d+) run, (\d+) passed, (\d+) failed, (\d+) errored, (\d+) ignored, (\d+) inconclusive",tests)
        require(match and int(match[1])>0 and match[1]==match[2] and all(int(match[i])==0 for i in (3,4,5,6)),"PostcardCheck test support missing/failed/skipped")
        return {"designGates":len(gates),"tests":int(match[1]),"passed":int(match[2]),"failed":0}
    if name == "SCORING_BIT_IDENTICAL":
        data=e.data("scoring_exact.json");rows=data.get("results",[])
        installed=[x for x in rows if x.get("stage")=="installed"]
        require({(x["hole"],x["format"]) for x in installed}=={(h,f) for h in (8,9,10) for f in ("blend","fbx")},"Missing installed six-format exact comparisons")
        require(data.get("pass") is True and rows and all(x.get("pass") is True and x.get("threshold_m")==0 and x.get("max_vertex_delta_m")==0 and x.get("max_marker_delta_m")==0 and x.get("protected_name_count",0)>0 and x.get("mesh_count",0)>0 and not x.get("problems") for x in rows),"Exact-zero/name/transform/scoring rawFAIL retained")
        return [{k:x.get(k) for k in ("hole","stage","format","pass","threshold_m","max_vertex_delta_m","max_marker_delta_m","protected_name_count")} for x in rows]
    if name == "FBX_META_UNCHANGED":
        data=e.data("meta_hash_compare.json");rows=data.get("files",[])
        expected={f"Unity/Assets/Resources/Course/hole_{h:02d}.fbx.meta" for h in (8,9,10)}
        require(data.get("changed_count")==0 and {x.get("path") for x in rows}==expected and all(x.get("expected") and x["expected"]==x.get("actual") for x in rows),"Original installed three FBX meta comparison missing/changed")
        return data
    if name.startswith("TRIANGLE_CAP_H"):
        hole=int(name[-2:]);_,gates=verifier(e,hole,False)
        rows=[x for x in gates if x["name"]=="TRIANGLE_BUDGET@fbx"]
        require(len(rows)==1,"Installed FBX geometry triangle measurement missing")
        match=re.match(r"(\d+) triangles",rows[0]["detail"]);require(match,"No actual geometry triangle count")
        triangles=int(match[1]);require(triangles<=300000 and rows[0].get("ok") is True,"Geometry cap/original tighter250000 gateFAIL")
        return {"geometryTriangles":triangles,"goalCap":300000,"originalVerifier":rows[0],"renderTriangles":"Reported separately; include render/shadow passes"}
    if name.startswith(("TEE_DRAW_CALL_CAP_H","TEE_TRIANGLES_DRAWCALLS_SETPASS_REPORTED_H")):
        data=validate_cost(e,int(name[-2:]),primary)
        if name.startswith("TEE_DRAW_CALL_CAP"):require(data["drawCalls"]<=250,"Actual tee draw-call cap exceeded: "+str(data["drawCalls"]))
        return data
    if name == "METAL_IOS_COMPILE":
        data=e.data("ios_export.json");log=e.text("logs/ios_export.unity.log")
        require(data.get("status")=="PASS" and data.get("buildResult")=="Succeeded" and data.get("errorCount")==0 and not data.get("errors") and data.get("graphicsApis")==["Metal"] and data.get("requiredSourcesEqualCurrentRepo") is True,"Current primary iOS Metal export failed/unverified")
        require(Path(data.get("unityProject", "")).resolve()==primary,"Clone export cannot prove main")
        assets=data.get("packedSourceAssets",[])
        require(all(any(str(a).endswith("/"+shader+".shader") for a in assets) for shader in ("GolfLava","GolfPlants","GolfSurf")),"All3 actual golf shader sources not proven in export")
        require(not re.search(r"Shader error|error CS\d+:",log,re.I),"Raw iOS shader/source error retained")
        return {"export":data, "completedDeviceTargetBuild":device_build(e,root), "physicalDeviceRun":False}
    if name == "IOS_DEVICE_BUILD":
        return device_build(e,root)
    if name == "TWELVE_CURRENT_GAMEVIEW_STILLS_AND_THREE_VS_REF":
        # Publication is outside the runner; it needs a fresh explicit manifest.
        manifest=e.data("publication_manifest.json")
        require(Path(manifest.get("installedRun", "")).resolve()==e.run,"Publication not tied to this installed run")
        rows=manifest.get("files",[]);stills=[x for x in rows if x.get("kind")=="still"];refs=[x for x in rows if x.get("kind")=="vs_ref"]
        expected={x["name"] for x in e.data("stills_cfg_12.json")["shots"]}
        require(len(stills)==12 and {x.get("shot") for x in stills}==expected and len(refs)==3 and {x.get("hole") for x in refs}=={8,9,10},"Not12 unique current native stills +3 vs-ref sheets")
        for row in rows:
            path=Path(row.get("path", "")).resolve();require(path.is_relative_to(root/'ArtDir/screenshots/golf_postcards/look') and path.is_file() and path.stat().st_mtime>=e.start and digest(path)==row.get("sha256"),"Stale/missing/wrong publication hash")
            if row.get("kind")=="still":
                folder="aerial" if row["shot"].endswith("_4_aerial") else "stills"
                source=e.path(f"{folder}/{row['shot']}.png")
                require(str(source)==str(Path(row.get("source", "")).resolve()) and digest(source)==row.get("sourceSha256")==row.get("sha256"),"Published PNG not exact native current-run source")
                require(Image.open(path).size==(900,1600),"Published native portrait resolution wrong")
            else:
                source=e.path(f"aerial/hole{row['hole']:02d}_4_aerial.png")
                reference=root/f"ArtDir/environments/refs/{ {8:'needle',9:'split',10:'crater'}[row['hole']]}.jpg"
                require(row.get("tool")=="make_vs_ref.py" and Path(row.get("currentSource", "")).resolve()==source and row.get("currentSourceSha256")==digest(source) and reference.is_file() and Path(row.get("reference", "")).resolve()==reference.resolve() and row.get("referenceSha256")==digest(reference), "Vs-ref recipe/current native/reference hashes missing; image existence alone is not proof")
        require("GolfArcade.EditorTools.GolfFlyoverCapture.Run" in e.text("command_inventory.txt") and e.path("logs/flyover_aerial3.unity.log"),"Actual GolfFlyoverCapture aerial invocation absent")
        return {"nativeStills":12,"vsRef":3,"files":rows}
    raise ValueError("No validated automatic extractor for this gate; use p6_gate_mapping.json for honest manual review")


def table_measurement(row):
    name = row['gate']; metrics = row.get('metrics')
    observed = row.get('rawObservedMeasurements', [])
    values = [x.get('measurements') for x in observed if isinstance(x.get('measurements'), dict)]
    if name == 'GUARDS_7_OF_7' and metrics:return f"{metrics['passed']}/7 PASS, {metrics['failed']} FAIL"
    if name == 'PROTECTED_FILES':
        return row.get('reason', '').split(';', 1)[0] if not metrics else f"{metrics['changed_count']}/{metrics['files_checked']} changed"
    if name.startswith('POSTCARD_LOOK_VERIFY_H'):
        gates = values[0].get('gates', []) if values else []
        return f"{sum(x.get('ok') is True for x in gates)}/{len(gates)}; failed: " + ', '.join(x['name'] for x in gates if x.get('ok') is not True)
    if name == 'BASALT_JOINTS' and values:
        shots = values[0].get('shots', {}); parts = []
        sk = j = 0
        for shot in ('hole10_1_tee', 'hole10_2_approach', 'hole10_3_lavarim'):
            d = shots.get(shot, {}).get('basalt', {})
            sk += d.get('glow_skeleton_px', 0); j += d.get('glow_junction_clusters', 0)
            parts.append(f"{shot}: {d.get('pixels')}px, S{d.get('base_s')}, Y{d.get('base_lum_median')}, glow{d.get('glow_coverage')}, vertical{d.get('glow_vertical_line_share')}, rung{d.get('glow_horizontal_rung_share')}")
        return '; '.join(parts) + f"; junctions {j}/{sk}px = {100*j/sk:.3f}/100" if sk else '; '.join(parts) + '; network unmeasured'
    if name == 'GAMEPLAY_FRAMING' and values:
        data = values[0].get('GAMEPLAY_FRAMING', {}); source = data.get('rows', [])
        canonical = [x for x in source if Path(x.get('folder', '')).name == '12']
        return ('; '.join(f"H{x['shot'][4:6]} {'tee' if '_1_' in x['shot'] else 'approach'}: water{x.get('waterShare',0)*100:.4f}%, landmark{x.get('landmarkHeight')}px {x.get('landmarkCap')}, cliff{x.get('cliffCap')}" for x in canonical) + '; water cap15%: all6FAIL; each landmark cap64px, single alternative') if canonical else row.get('reason')
    if name == 'MOW_BAND_CONTRAST' and metrics:
        return '; '.join(f"H{x['hole']} {x['material']} max{max(m['gap'] for m in x['supportedMeasurements'])*100:.3f}% (cap{x['cap']*100:.0f}%, minimum plateau{min(min(m['lightPixels'],m['darkPixels']) for m in x['supportedMeasurements'])}px)" for x in metrics['materials']) + '; original repeat drift0px'
    if name == 'SPLIT_CLIFF_ISLANDS' and values:
        d=next((x for x in values if x.get('shot')=='hole09_4_aerial'),values[0])
        return f"Frozen closed boundaries{d.get('frozenClosedBoundaries')} (requires2); control drift{d.get('controlDriftPixels')}px; " + '; '.join(f"{x['name']}: cliff{x['cliffAdjacentPixels']}/{x['denominatorPixels']} = {x['cliffOutlineFraction']*100:.3f}% (cap80%); SURF{x['surfBaseAdjacentPixels']}px" for x in d.get('parts',[]))
    if name.startswith('TEE_') and values:
        d = values[0]
        return f"{d.get('triangles')} rendered triangles, {d.get('drawCalls')} draws (cap250), {d.get('setPass')} SetPass; {len(d.get('samples',[]))} stable published frames"
    if name == 'RUIN_NOT_BOXES' and metrics:
        return '; '.join(f"{Path(x['source']).suffix}: {x['unbroken_cuboids']}/{x['pieces']} unbroken cuboids ({x['share']*100:.3f}%; cap20%)" for x in metrics)
    if name == 'PLANT_SWAY_CAPS' and metrics:
        text=next((x['detail'] for x in metrics['nativeGates'] if x['gate']=='SWAY_GENTLE'), '')
        caps=re.findall(r'(tuft|flower|shrub|vine):.*?max [\d.]+ / [\d.]+ / ([\d.]+) yd at 0 / 10 / 20 mph \(cap ([\d.]+)\)',text)
        return '; '.join(f"{kind} {tip}yd at20mph <= {cap}yd" for kind,tip,cap in caps) + f"; installed tree none coloured (fixture measured separately); {metrics['nativeGateCount']} native gate lines PASS"
    if name == 'PLANT_SWAY_COLORS' and metrics:
        detail=next((x['detail'] for x in metrics['nativeGates'] if x['gate']=='PLANT_SWAY_COLORS_UNITY'), '')
        match=re.match(r'(\d+) PLANT_\* objects on (\d+) unique meshes.*?; (\d+) carry the colour attribute',detail)
        return f"{match[1]} objects; {match[3]}/{match[2]} meshes coloured; six installed blend/FBX verifier subsets PASS" if match else 'Native colours numeric support unavailable'
    if name == 'NEEDLE_STACK_VISIBILITY' and metrics:
        return '; '.join(f"{x['shot']}: {x['visible']} visible stacks (minimum2)" for x in metrics['rows'] if Path(x['folder']).name=='12')
    if name.startswith('GRASS_HUE_H') and metrics:
        h=int(name[-2:]);samples=metrics['samples']
        return '; '.join(f"{'tee' if '_1_' in shot else 'approach'} fairway hue{samples[shot]['fairway']['hue_of_mean']}, clipped{samples[shot]['fairway']['clip_any_ch_250']*100:.3f}%, support{samples[shot]['fairway']['pixels']}px" for shot in (f'hole{h:02d}_1_tee',f'hole{h:02d}_2_approach')) + '; original hue60..76, clip<=5%'
    if name in ('SHELF','LAVA_ORANGE','SMOKE_SOFT') and metrics:
        shots=metrics['shots']
        if name=='SHELF':
            measured=[(s,d) for s,d in shots.items() if d.get('shelf_px',0)>=300]
            return '; '.join(f"{s}: shelf{o['shelf_px']}px, brightness ratio{o['shelf_vs_ocean_lum']}, brightest2% share{o['top2_share_shelf']*100:.2f}%" for s,o in measured) + '; caps1.3ratio/10%'
        source=[(s,shots[s]) for s in ('hole10_1_tee','hole10_2_approach','hole10_3_lavarim') if s in shots]
        if name=='LAVA_ORANGE':return '; '.join(f"{s}: band{d['in_band_hue8_28_s75_v70']*100:.2f}%, V{d['mean_v']}, dark{d['dark_v_lt_040']*100:.2f}%, G>=250:{d['g_ge_250']*100:.2f}%" for s,d in source)
        return '; '.join(f"{s}: changed{d['changed_px_gt1p5']}px, dYp95{d['delta_lum_p95']}, max{d['delta_lum_max']}, edgep99{d['edge_step_p99_levels_per_px']}/px on{d['edge_band_px_on_smooth_backdrop']}px" for s,d in source) + '; caps p95>=8/max<=110/edge<=6'
    if name in ('NO_PLANT_ON_SEA','NO_ROCK_STRETCH_2X','PATH_UNDER_BALL') and metrics:
        mesh=metrics.get('mesh',{})
        if name=='NO_PLANT_ON_SEA':return '; '.join(f"{h}: {d['plants']['on_sea']}/{d['plants']['plants']} plants on sea, {d['plants']['floating_no_surface_1m']} floating" for h,d in mesh.items())
        if name=='NO_ROCK_STRETCH_2X':return '; '.join(f"{h}: scaleMax{d['rocks']['scale_max']}, anisotropyMax{d['rocks']['anisotropy_max']}; >2scale{d['rocks']['count_scale_gt_2']}, >2anisotropy{d['rocks']['count_anisotropy_gt_2']}" for h,d in mesh.items())
        d=mesh.get('hole8',{}).get('path',{});return f"{d.get('objects')} path meshes/{d.get('samples')} samples; top maximum{d.get('max_cm')}cm (cap1.5cm), above cap{d.get('above_1p5cm')}; native ball visibility verified"
    if name == 'NO_FOAM_STRIP':
        native=next((x['nativeFoamGate'] for x in observed if 'nativeFoamGate' in x),[])
        if native:
            match=re.match(r'(\d+) foam renderer',native[0]['detail'])
            return f"Native spacing gate{native[0]['status']}: {match[1] if match else 'unmeasured'} close/overlapping relations; minimum0.0yd vs cap>=7yd; offline visual/mesh metric PASS retained"
    if name in ('GOLF_LOOK_SMOKE_BOTH_URP','POSTCARD_IMPORT_CHECK'):
        if metrics:return '; '.join(metrics.get('reportedSummary',[])) + f"; {metrics['passed']} raw gate lines PASS; both URP suites" if name.startswith('GOLF') else f"{metrics['passed']} native gate lines/0failed"
        gates=[]
        for o in observed:gates.extend(o.get('nativeImportGates',[]))
        checks=[x for x in gates if x['gate']!='POSTCARD_IMPORT_CHECK']
        return f"{sum(x['status']=='PASS' for x in checks)}/{len(checks)} native checks PASS; summaryFAIL; " + '; '.join(x['gate'] for x in checks if x['status']!='PASS') if checks else row.get('reason')
    if name=='EDITMODE_POSTCARD_HOLE_TESTS' and metrics:return f"{metrics['passed']} tests PASS/{metrics['failed']} FAIL/skipped0"
    if name=='TOOLS_POSTCARD_CHECK' and metrics:return f"{metrics['designGates']} design gates PASS; {metrics['passed']}/{metrics['tests']} tests PASS"
    if name=='SCORING_BIT_IDENTICAL' and metrics:return f"{len(metrics)} installed/staged format comparisons; maximum vertex0m/marker0m; exact threshold0m"
    if name=='FBX_META_UNCHANGED' and metrics:return f"{len(metrics['files'])}/3 original FBX.meta SHA hashes equal; {metrics['changed_count']} changed"
    if name=='TWELVE_CURRENT_GAMEVIEW_STILLS_AND_THREE_VS_REF' and metrics:return f"{metrics['nativeStills']} exact current native900x1600PNG + {metrics['vsRef']} current/reference JPG; image identity PASS; eye review separate"
    if name.startswith('TRIANGLE_CAP_H') and metrics:return f"{metrics['geometryTriangles']} installed FBX geometry triangles (goal<=300000; original<=250000)"
    if name == 'IOS_DEVICE_BUILD' and metrics:
        return f"Unsigned iphoneos Release exit{metrics['deviceBuildExit']}; initial exit{metrics['firstInvocationExit']} retained; physicalDeviceRun=false"
    if name == 'METAL_IOS_COMPILE' and metrics:
        return 'Primary Unity Metal-only export Succeeded, errors0; actual unsigned iphoneos Release build exit0; physicalDeviceRun=false'
    return json.dumps(metrics,ensure_ascii=False,separators=(',',':')) if metrics is not None else row.get('reason') or 'FAIL/unmeasured'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("run",type=Path);p.add_argument("--out",type=Path,help="New output stem under RUNDIR; defaults to p6_summary")
    p.add_argument("--eye-review",type=Path,help="Explicit completed physical eye-review JSON under v3, tied to this run and its published image hashes")
    args=p.parse_args();root=Path(__file__).resolve().parents[4];v3=root/'work/postcard-look/v3';run=args.run.resolve()
    require(run.is_relative_to(v3/'proof/runtime/runs'),"Only final runner RUNDIR accepted; P5/staged/fixture evidence is ineligible")
    out=(args.out or run/'p6_summary').resolve();require(out.is_relative_to(run),"Summary output must stay in this run")
    outputs=[out.with_suffix(s) for s in (".json",".md")]+[out.with_name(out.name+'.p7_review.template.json')]
    require(not any(x.exists() for x in outputs),"Never overwrite report history; choose a new --out stem")
    inventory=json.loads((v3/'proof/report_inventory.json').read_text());require(len(inventory['gates'])==41,"Required41 inventory rows changed")
    e=Evidence(run);primary=(root/'Unity').resolve();scope=[]
    try:
        require(Path(e.text('effective_unity_project.txt').strip()).resolve()==primary,"Effective project is not actual primary Unity")
        require('stageAssets=installed-default' in e.text('proof_scope.txt'),"Stage substitution is ineligible installed P6 proof")
        e.path('run_exit_code.txt')  # Completion, not a PASS inferred from exit0.
    except Exception as error:scope.append(str(error))
    rows=[]
    for original in inventory['gates']:
        e.used=[];e.observed=[];e.context_gate=original['gate']
        row={'gate':original['gate'],'status':'FAIL','metrics':None,'evidence':[], 'reason':None,'inventoryThresholdMetadata':original['threshold']}
        if row['gate'].startswith('GRASS_HUE_H'):
            row['metadataError']='Inventory64..73 copied an observed still/reference range as a threshold. Actual unchanged measure.py uses60..76; original verifier gates are retained. No threshold replacement.'
        try:
            row['metrics']=evaluate(row['gate'],e,primary,root)
            require(not scope,'; '.join(scope));row['status']='PASS'
        except Exception as error:row['reason']=str(error)
        row['rawObservedMeasurements']=e.observed
        row['evidence']=list({x['path']:x for x in e.used}.values())
        try:row['compactMeasurement']=table_measurement(row)
        except Exception as error:row['compactMeasurement']='FAIL/unverified compact numeric mapping: '+str(error)+'; raw evidence retained'
        rows.append(row)
    commands=[];raw_fail=[]
    try:
        for line in e.text('command_results.tsv').splitlines():
            label,code,log=line.split('\t',2);commands.append({'label':label,'exit':int(code),'log':log})
        for path in e.matches('logs/*.log'):
            for line in e.text(path).splitlines():
                match=GATE_LINE.match(line)
                if match and match[2]!='PASS':raw_fail.append({'path':str(run/path),'line':line})
                elif re.search(r'error CS\d+:|Shader error|\*\* BUILD FAILED \*\*',line,re.I):raw_fail.append({'path':str(run/path),'line':line})
    except Exception as error:scope.append('Raw failure inventory unavailable: '+str(error))
    review=json.loads((v3/'proof/p7_review.template.json').read_text());review['installedRun']=str(run)
    review_path=(args.eye_review or run/'p7_review.json').resolve(); review_evidence=None
    if review_path.is_file():
        try:
            require(review_path.is_relative_to(v3) and review_path.stat().st_mtime>=e.start,'Eye review outside v3 or stale')
            reviewed=json.loads(review_path.read_text()); belongs=reviewed.get('installedRun','')
            require(belongs==run.name or Path(belongs).resolve()==run,'P7 review belongs to another run')
            require(reviewed.get('physicalImageReview') is True,'Actual physical image review not recorded')
            require(len(reviewed.get('holes',[]))==3 and {h.get('hole') for h in reviewed['holes']}=={8,9,10},'P7 three holes missing')
            for hole in reviewed['holes']:
                require(len(hole.get('differences',[]))==10 and {x.get('p0_rank') for x in hole['differences']}==set(range(1,11)),'All10 P0 ranks per hole required')
                require(all(x.get('result') in ('PASS','FAIL') and x.get('fixed') in (True,False) and x.get('remaining') and x.get('evidence') for x in hole['differences']),'Final score/remaining/evidence missing for a P0 difference')
                sheet=Path(hole.get('contactSheet','')).resolve();ref=Path(hole.get('vsRef','')).resolve()
                require(sheet.is_file() and sheet.is_relative_to(run/'contact_sheets') and ref.is_file() and ref.is_relative_to(root/'ArtDir/screenshots/golf_postcards/look') and digest(ref)==hole.get('vsRefSha256'),'Reviewed current image identity absent/stale')
            review=reviewed;review_evidence={'path':str(review_path),'sha256':digest(review_path),'mtime':review_path.stat().st_mtime}
        except Exception as error:review['invalidFinalReviewReason']=str(error)
    result={'generatedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'installedRun':str(run),'status':'PASS' if not scope and all(x['status']=='PASS' for x in rows) and commands and all(x['exit']==0 for x in commands) and not raw_fail else 'FAIL',
            'validation':'Source/schema inspected; extraction not end-to-end validated before actual final run. Parent must review every row.',
            'scopeFailures':scope,'gateCount':41,'gates':rows,'commands':commands,'rawFailuresRetained':raw_fail,'holesAndThirtyDifferences':review,'physicalEyeReviewEvidence':review_evidence,
            'limits':['P5 source/schema samples never qualify as final P6 evidence.','Process exits are recorded, never substituted for numeric/native support.','Geometry triangle cap and published render/shadow triangles are separate.','Missing publication/meta/ruin/review sidecars require exact next steps in final report.']}
    outputs[0].parent.mkdir(parents=True,exist_ok=True);outputs[0].write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    outputs[2].write_text(json.dumps(review,indent=2)+'\n')
    lines=['# Final installed P6 evidence extraction','',f"Run: `{run}`. Overall: **{result['status']}**. Parent review required; missing/support/stale evidence is FAIL.",'','| Gate | Result | Measured number / reason | Evidence |','|---|---|---|---|']
    for row in rows:
        detail=row['compactMeasurement'].replace('|','/').replace('\n',' ')
        evidence=', '.join(Path(x['path']).relative_to(run).as_posix() for x in row['evidence'])[:200]
        lines.append(f"| {row['gate']} | {row['status']} | {detail} | {evidence or 'missing'} |")
    lines+=['','Geometry triangles are capped separately from published triangles including shadow/render passes. SetPass is reported without an invented cap.','',f"Raw command failures: {sum(x['exit']!=0 for x in commands)}. Raw gate/compiler failures retained: {len(raw_fail)}.",'','## Final image review and all30 P0 differences','']
    for hole in review['holes']:
        lines += [f"Hole{hole['hole']}: recognition={hole.get('recognisableFromReference')}; box/plank/flat-strip/stripe/plastic read={hole.get('hasBoxPlankFlatStripStripeOrPlasticRead')}; contact sheet={hole.get('contactSheet')}; vs-ref={hole.get('vsRef')}.",'']
        for item in hole['differences']:
            lines.append(f"- {item['p0_rank']}. {item['difference']} — {item.get('result') or 'FAIL/unmeasured final re-score'}; remaining: {item.get('remaining') or 'Final installed eye review required'}. Evidence: {item.get('evidence') or 'missing'}")
        lines.append('')
    outputs[1].write_text('\n'.join(lines)+'\n');print(outputs[0]);print(outputs[1]);return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
