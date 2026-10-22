"""basalt_gv.py <stills dir> [more dirs] : the integrator's BASALT_JOINTS measurement (v2/proof/measure.py basalt_metrics, basalt_shot_ok, basalt_network_ok) on the hole 10 stills of a dir, with the installed proof masks
(v2/proof/masks/9: the geometry of the shots is the same) and the dir's own frame as the pixels (the mask 'full' frames carry the OLD textures)."""
import sys, os, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/proof')
import measure as M
meta = {s["name"]: s for s in json.load(open(M.P + "/masks/9/masks_meta.json"))["shots"]}
for d in sys.argv[1:]:
    print('=====', d)
    jn_sk = jn_cl = 0; ok_all = True
    for n in ("hole10_1_tee", "hole10_2_approach", "hole10_3_lavarim"):
        p = os.path.join(d, n + ".png")
        if not os.path.exists(p): print(n, 'missing'); continue
        sh = M.Shot(n, p, M.P + "/masks/9", meta[n]); sh.full = None; sh.px = sh.still
        b = M.basalt_metrics(sh)
        ok = M.basalt_shot_ok(b); ok_all &= ok
        jn_sk += b.get("glow_skeleton_px", 0); jn_cl += b.get("glow_junction_clusters", 0)
        print('%-18s basalt %6d px glow %.1f%% comps %3s vert %3.0f%% rung %3.0f%% blob %3.0f%% median h %s w %s | skel %4d junc %3d | S %.3f med lum %.1f | %s' % (n, b['pixels'], 100 * b['glow_coverage'], b.get('glow_components'), 100 * b.get('glow_vertical_line_share', 0), 100 * b.get('glow_horizontal_rung_share', 0), 100 * b.get('glow_blob_share', 0), b.get('glow_component_height_median_px'), b.get('glow_component_width_median_px'), b.get('glow_skeleton_px', 0), b.get('glow_junction_clusters', 0), b['base_s'], b['base_lum_median'], 'ok' if ok else 'FAIL'))
    rate = 100.0 * jn_cl / jn_sk if jn_sk else 0
    print('joint network: %d junctions / %d skeleton px = %.2f per 100 (>= 3.0) %s ; per-shot gates %s => BASALT_JOINTS %s' % (jn_cl, jn_sk, rate, 'ok' if M.basalt_network_ok(jn_sk, jn_cl) else 'FAIL', 'ok' if ok_all else 'FAIL', 'PASS' if ok_all and M.basalt_network_ok(jn_sk, jn_cl) else 'FAIL'))
