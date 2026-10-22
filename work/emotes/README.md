# work/emotes - EMOTES AND INTROS

`NOTE_EMOTES.md` (what, where, findings), `GATE_RESULTS.md` (verdict + every line), `GATE_DEFS_preregistered.md` (the definitions, written before the first run), `WATCH_EMOTES.md` (what the reference clips showed; nothing was downloaded).

Rebuild: `scripts/build_all.sh` (clips -> 12 FBX) -> `scripts/unity_run.sh GolfArcade.EditorTools.EmoteWire.Run <log>` (import + wire, in a clone) -> `EmoteFilm.Run` (EF_OUT, EF_FEMALE) -> `scripts/make_film.py` -> `trace_fbx.py` (Blender) + `check_gates.py` + `check_repo.py` + `supplement.py` + `finalize.py`.
Films: `film/<Name>_<male|female>.mp4` (the in-game clip, front | side), `film/<Name>_<sex>_gamecam.mp4` (the game camera + HUD). Stills: `proof/`.
