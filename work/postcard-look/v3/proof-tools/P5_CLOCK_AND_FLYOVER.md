# Proof driver clock and aerial entrypoint drafts

All physical drafts/output remain under work/postcard-look/v3. No Unity/Xcode run, actual Assets write, install or Git mutation was performed by this agent for this work.

## Native clock diagnosis

Current primary GolfLook.cs uses GolfArcade/TennisWater for LK_WATER and LK_WATER_SHALLOW. The protected TennisWater.shader:35 samples `_Time.y`. GolfSurf/GolfLava are static. Installed PackageCache/com.unity.render-pipelines.universal@a8b4b2fc3560/Runtime/ScriptableRenderer.cs:942,1035,1392 chooses `Application.isPlaying ? Time.time : Time.realtimeSinceStartup`, then SetShaderTimeValues overwrites shader globals per camera. Setting `_Time` before Camera.Render is therefore overwritten. Time.timeScale=0 does not freeze an edit-mode realtime clock.

The P3 native H9 edit-mode captures retained their honest invalid-control FAILs: aerial1005505,tee7823,approach21657 drift pixels. Previous control-repeat PNG was absent; the precise historical changed-pixel category cannot be reconstructed from a no-shadow image. No water-only exclusion, tolerance, smoothing or selected repeat was added.

## Bounded future P5/6 behavior

Only drafts PostcardV3ProofMasks.cs and PostcardV3FrameCosts.cs now save actual previous Time.timeScale after configuring the existing plant proof overrides, set0 in actual Play mode, and restore in Finish finally including errors. The player/frame counter can continue while scaled time is frozen. Actual scoring, camera, TennisWater, URP and runtime sources remain untouched. Original PostcardLookStills still uses its existing behavior.

PostcardV3FrameProof now writes `<shot>.control_repeat.png` and `<shot>.control_drift.png` for every control render, records actual applicationIsPlaying/gameTime/timeScale, and names the diagnostic files in its bands record. Original full RGB bytes are retained. Drift must still equal0 across the whole frame. Authored-band plateau support512px,1px erosion, fairway0.12/green0.08 and all original exclusions/caps are unchanged. No completed native frozen-clock render has yet validated the draft; unresolved drift remains FAIL.

## GolfFlyoverCapture portrait branch

`proof-tools/GolfFlyoverCapture.cs` is a scratch copy of the actual allowed Editor check with one optional Run branch. `GOLF_FLY_STILLS_CFG` plus explicit `GOLF_FLY_OUT` delegates to existing PostcardLookStills.Run, which stores its cfg/out in SessionState before Play mode; the temporary environment values are then restored. The original Cliffside7 movie branch is unchanged. `aerial_cfg_3.json` copies exactly the three `_4_aerial` shots from fixed proof/stills_cfg_12.json, with no camera-coordinate changes.

Parent installation atP5/6: replace ONLY actual Unity/Assets/Editor/GolfFlyoverCapture.cs with this draft; preserve its existing meta. Do not copy this same-named class into PostcardV3Scratch, which would create a duplicate. Install the authorized PostcardV3 helpers through the approved scratch setup or final allowed Editor placement while all heavy processes are closed, then actual Unity compile/import before capture.

The v3 strict runner prepares per-run aerial_cfg_3.json. In installed mode, its stills step first checks that actual GolfFlyoverCapture contains the optional branch; absentbranch=FAIL, with no legacyhole7 substitute. It calls GolfArcade.EditorTools.GolfFlyoverCapture.Run with GOLF_FLY_STILLS_CFG=<run>/aerial_cfg_3.json, GOLF_FLY_OUT=<run>/aerial, GOLF_FLY_W=900,GOLF_FLY_H=1600 and existing GOLF_STILLS_SWAY=0,0,0. Staged P5 mode defers this installed-only call; actual staged full frames remain masks/12. Parent later publishes actual three aerial PNGs and reference sheets to permitted ArtDir names with SHA/date/source provenance.

## Validation and remaining gaps

Offline type compile attempt2 passed all11PostcardV3 drafts against291 actual Unity/.NET/project references and77 original Editor source snapshots (88sources total),0errors. Attempt3 passed the optional flyover branch. Attempt4 passed current11drafts including clock/restoration/repeat diagnostics plus flyover branch,0errors,4 pre-existing Editor-source warnings,0draft warnings; source and references stable during compile. All evidence/commands/snapshotSHAs are under proof-tools/type-compile/attemptN. The first failed argument-classification harness attempt is retained. No offline assembly was executed as Unity code.

Runnerbash-n and every preparedPython AST passed. proof/runtime/adapter-check5 records preparation-only validation: exact comparator repo/output path adaptation, unchanged0threshold and fixed3aerial cfg. Actual installed plant sway, exact installed+finalv3staged comparison and authoritative aggregate_frames.py are now added without dropping any old step.

proof/report_inventory.json maps41 required P6 gates to exact existing files, selectors, raw values and missing final installed evidence. P6 has not run; earlier fixtures/audits/staged captures cannot confer finalPASS. Default runner omitsios, so root must explicitly include it. Actualv2installer must use finalv3sources/libs beforepre/install. Final per-piece ruin classifier, actual Split aerial gate, ArtDir12stills/3vsref publication and final all-required-gate presence review remain necessary. Strict collector retains failures but does not itself guarantee a complete P6 invocation.
