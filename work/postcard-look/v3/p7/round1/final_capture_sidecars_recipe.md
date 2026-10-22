# Deferred round1 installed capture and sidecars

Root selects this camera config before the first round1 capture. The recipe has
not been executed. It writes fresh per-run evidence and preserves the first P6
run, raw failures, old source configs, original snapshots and eye scores.

```sh
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
V="$R/work/postcard-look/v3"
C="$V/p7/round1/capture_configs"
FINAL_TAG='p7_round1_installed_1'
FINAL_RUN="$V/proof/runtime/runs/$FINAL_TAG"
export PYTHONDONTWRITEBYTECODE=1
export GOLF_PROOF_CAPTURE_CONFIG_DIR="$C"
export GOLF_V3_PROOF_CFG="$C/proof_cfg_round1.json"
export GOLF_V3_SPLIT_CFG="$C/split_outline_cfg_round1.json"
export GOLF_PROOF_UNITY_PROJECT="$R/Unity"
export GOLF_PROOF_STAGE_ASSETS=''
export PROOF_TAG="$FINAL_TAG"
```

Root may launch the next complete installed runner only after its source/build/
reinstall authorization. Its existing steps remain unchanged. An existing tag
is rejected; choose another fresh tag rather than overwrite history. Actual
Unity/Xcode invocations retain the existing heavy admission wrapper. `ios` is
explicit because the runner default does not include it.

```sh
bash "$V/proof/runtime/run_proof.sh" pre install blender unity stills studio masks costs gates mesh metrics sheets protected report ios
```

After the primary installed run has written run_exit_code.txt, including FAILs,
the following sidecars operate on actual installed inputs. The first command is
plan-only; the second launches two sequential CPU Blender analyses through the
existing heavy_fastwait/unchanged heavy.sh wrappers. Do not outer-wrap the whole
sidecar helper in heavy.sh. None of these commands launches Unity or Xcode.

```sh
python3 "$V/proof/runtime/final_installed_sidecars.py" "$FINAL_RUN" --meta --ruin --plan
python3 "$V/proof/runtime/final_installed_sidecars.py" "$FINAL_RUN" --meta --ruin > "$FINAL_RUN/final_installed_sidecars_round1.log" 2>&1
python3 "$V/proof/runtime/publish_p6.py" "$FINAL_RUN" > "$FINAL_RUN/final_publication_round1.log" 2>&1
python3 "$V/proof/runtime/check_protected_unique.py" --root "$R" --out "$FINAL_RUN/protected_explicit_round1.json" > "$FINAL_RUN/protected_explicit_round1.txt" 2>&1
```

Each helper rejects existing output manifests/census/copy paths. Retain every
returned exit code even if a later command succeeds. Standard filenames such as
meta_hash_compare.json, ruin_installed/* and publication_manifest.json are fresh
because FINAL_RUN is new. The protected adapter changes output/repo paths only;
the original strict checker and start snapshot remain unchanged.

Publication copies the nine original native PNGs plus three actual native aerial
PNGs into the exact ArtDir paths, creates three versus-reference JPGs and the
12-still sheets, and backs up the prior publication. The manifest binds source/
published/reference hashes and source timing. Publication identity PASS does
not imply eye-review or visual-gate PASS.

Root must physically inspect the new three versus-reference sheets and contact
sheets, then write a fresh review under FINAL_RUN tied to its current image
hashes. Recognition, all ten original ranked Phase0 differences per hole and
remaining failures must be answered honestly. Never copy the previous review
into this run as a new measurement. For a fresh template and preliminary rows,
the extractor can run before that review; absent eye measurements remain FAIL.

```sh
python3 "$V/proof/summarize_p6.py" "$FINAL_RUN" --out "$FINAL_RUN/final_report_rows_round1_pre_eye_1"
# After actual physical inspection and a new FINAL_RUN/p7_review.json:
python3 "$V/proof/summarize_p6.py" "$FINAL_RUN" --eye-review "$FINAL_RUN/p7_review.json" --out "$FINAL_RUN/final_report_rows_round1_reviewed_1"
```

The extractor emits exactly41 compact rows and all30 original ranked scores.
Missing, unmeasured, stale or unsupported data remains FAIL. It retains all
native raw FAILs, exact zero scoring, original meta/protected comparisons,
positive frame-published counters, both installed ruin formats and actual
device-build records. It keeps geometry and rendered/shadow triangles distinct.
The final report must include remaining holes and limits without inventing
future PASS or translating the first installed P6 FAIL into success.

Only configuration parsing/routing has been validated so far. Camera config
changes are limited to three aerials; the nine original views, six tee/approach
framing views, all masks, raster support, thresholds and measurement tools stay
unchanged. Native correctness will be measured by the next installed run.
