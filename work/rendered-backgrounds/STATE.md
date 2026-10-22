# Rendered backgrounds — state (2026-10-17, end of chat 2)

DONE + INSTALLED + STAGED (not committed). `tools/install.sh` put the own files and Blender assets into `Unity/`. For the partly-owned files it staged only the hook lines (index + hook), so other chats' unstaged edits in TennisLook.cs stay unstaged.

- Gates: `GATE_RESULTS.md`, 120/120 PASS on 20 locations. QUALITY is awaiting Adnan. Device PERF is NOT RUN.
- Live venues: `RenderedBackdrop.Live` = resort, skyscraper, volcano, golf, hub.
- Proof images: `proof/` (00–07 sheets, per-venue gates JSON).
- Raw captures: `before/` and `final/`, 1080p PNGs, not staged.
- Rebuild the assets:
  - `blender/clouds/build_clouds.py` (about 20 min, resumable)
  - `blender/cloudsea/build_cloudsea.py` (about 25 min)
  - `blender/karst/build_karst.py --stage all` (about 15 min)
  - then `tools/tighten_clouds.py blender/clouds`
- Recreate the clone: `cp -cR Unity /private/tmp/backgrounds-UnityClone && tools/sync_clone.sh`.
- Open follow-ups are listed at the end of `GATE_RESULTS.md`.
