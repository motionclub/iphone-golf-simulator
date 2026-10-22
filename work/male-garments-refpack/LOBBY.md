# Lobby (SceneKit) parity for the male garments — 2026-10-17 (round 6 re-run 2026-10-18)

**10-18 round 6: PASS** (same tool, same private copy): tennis male luminance ratio 0.960–0.989, mean abs diff 4.9–9.2/255 (24 shots); golf
male 0.923–0.960 / 6.5–8.9 (4 shots). Enclosed shoes + short golf socks show the same in both renderers (lobby/sheets/*_male.png; the 10-17 sheets
are in lobby/sheets_1017). Export: 91 files differ from the repo's CharacterAssets (includes other chats' male face/rig changes), 25 .ktx
(lobby/changed_ktx.txt). Install for the integration chat: unchanged recipe below, after `patches/male_prefabs_r6_p0.patch`.

Made with `tools/lobby_sync.sh` (a private copy of `work/hero-sync/sync_heroes.sh`): `MatchHeroLockerExport` Run / RunDistance / RunGolf from
`~/male-garments-UnityClone` into `lobby/export`, a private copy of `GolfArcade/Unity/CharacterAssets` overlaid in `lobby/assets`, the .ktx the
Swift garment shader samples regenerated for every changed KitV2 map, then Unity `CaptureLobbyParity` vs the app's own SceneKit renderer
(`lobby_render.swift`) from the same cameras. Nothing was copied into the shared `CharacterAssets`.

## Result: PASS
`lobby/sheets/PARITY.md` (per shot: mean colour lobby vs game, luminance ratio, mean abs difference over hero pixels):
- tennis male, 5 looks x 4 framings: luminance ratio 0.960–0.982, mean abs diff 4.7–8.2 / 255 (the same range as the female rows, which this
  work did not touch, i.e. the SceneKit port's usual offset)
- golf male, 4 framings: ratio 0.920–0.963, diff 6.4–9.1
Sheets: `lobby/sheets/tennis_male.png`, `golf_male.png` (+ heads). New shoes, trimmed socks, shorts, collar tip and the golf polo/belt show
the same in both renderers.

## Install (integration chat)
The export also picks up other chats' unrelated changes (female files, male rig / Distance swing clips changed since the last sync), so do NOT copy
`lobby/export` wholesale. After the prefab patch is applied, run the normal `work/hero-sync/sync_heroes.sh` (+ `lobby/compress_maps.py`). The
files that come from this work are the 19 male KitV2 maps + their .ktx (`lobby/changed_ktx.txt`) and the male hero .json/.lzfse meshes
(`lobby/changed_export_male.txt` lists every male file that differs; the rig and Distance swing files in it are not from this work).
