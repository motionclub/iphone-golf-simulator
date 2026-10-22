# Reviewed round2 coordinator handoff

Prepare-only execution has succeeded. No production/source/stage/Assets, Unity or Git mutation was performed. The actual three-target merged plan is `d6d5cfea08948cb1a7a2675c2236b8ddc9c9a87aa4bfbecec873a48ddbb71809`. Coordinator SHA: `feee1e956727f0330e1931abade2b10fa2872aaf089c193a682414ef23871e3f`. Prepared immutable manifest: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v3/p7/round2/coordinator_review_1/manifest.json`; SHA `b37531b4a02150c055a2901e203818e51994b73fe011883141d6f852e72ed242`. Root must inspect these before action.

This manifest records the exact48 established inputs (17 Python and31 PNG), three reviewed source edits (H9 build/look, H10 build), completed physical round2 eye review, source/checker/installer/heavy pins, all prior stages/docs and installed binaries/metas. The root-accepted protected observation remains **FAIL61/1359, raw exit1**. Added27 and five changed prior rows are recorded in `protected_review/delta_from_old34.json`. Exact foreign observation authorizes continuing the process only; no baseline/exemption/threshold is changed.

Use this prepared manifest only while every hash still agrees. If sidecars or a concurrent task change any guarded byte, it refuses; prepare a new fresh directory after root review of the changed inputs. Do not overwrite this history. No automatic retry/rollback.

```sh
TASK_PROJECT='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
TASK_COORD="$TASK_PROJECT/work/postcard-look/v3/p7/round2/coordinator.py"
TASK_MANIFEST="$TASK_PROJECT/work/postcard-look/v3/p7/round2/coordinator_review_1/manifest.json"
TASK_MANIFEST_SHA='b37531b4a02150c055a2901e203818e51994b73fe011883141d6f852e72ed242'
TASK_HEAVY="$TASK_PROJECT/work/postcard-look/heavy.sh"

# Run only after current native/sidecars finish and root authorizes production apply.
bash "$TASK_HEAVY" p7-round2-apply python3 "$TASK_COORD" apply --manifest "$TASK_MANIFEST" --manifest-sha "$TASK_MANIFEST_SHA"
bash "$TASK_HEAVY" p7-round2-build python3 "$TASK_COORD" build --manifest "$TASK_MANIFEST" --manifest-sha "$TASK_MANIFEST_SHA"

# Inspect build logs/receipt and supply that exact reviewed SHA printed by build.
bash "$TASK_HEAVY" p7-round2-promote python3 "$TASK_COORD" promote --manifest "$TASK_MANIFEST" --manifest-sha "$TASK_MANIFEST_SHA" --predecessor-sha REVIEWED_BUILD_RECEIPT_SHA

# Inspect promotion receipt and actual INSTALL/list bytes; supply its exact SHA.
bash "$TASK_HEAVY" p7-round2-install python3 "$TASK_COORD" install --manifest "$TASK_MANIFEST" --manifest-sha "$TASK_MANIFEST_SHA" --predecessor-sha REVIEWED_PROMOTE_RECEIPT_SHA
```

Source apply reuses the exact pinned guarded root source helper and a derived plan containing the same target bytes plus coordinator/heavy/physical-review/checker pins. Its prepare composes scratch only. Apply can be omitted if root independently applies the exact reviewed merged plan: build still checks every declared post-apply SHA.

Build archives all three prior stages and docs under the new run before doing work; builds only affected09/10 with default QA enabled (`--no-render --qa`, never `--no-qa`); runs full original hole verifiers and H9 QA; requires every original geometry gate to pass and genuine nonempty exports. H8 is copied unchanged into the scratch candidate. The independent exact comparator executes its **original bytes unchanged** with `__file__` at its original path. Only environment output routing points to the new scratch run; exact12 results include installed+candidate blend/FBX, all names/topology/matrices/markers, threshold0m. Any failure prevents promotion. No triangle/draw/framing/eye PASS is inferred.

H9's previously measured gate stills are deliberately disclosed as reused old binary evidence. The verifier's original image-presence gate may pass on those bytes; this does not pass fresh candidate appearance. Missing H10 still/stat gates are recorded as UNMEASURED, even when the original raw verifier says SKIPPED/PASS. Original measured geometry failures still stop. Fresh full native proof remains mandatory and separate.

Promotion requires the externally reviewed build-receipt SHA, all original inputs unchanged, artifact hashes intact and existing stage/doc hashes unchanged. Only09/10 stages change;08 retains exact bytes. It records all3 current actual lib/PNG/stage/capture lists, correct first six INSTALL digests and the required H9 final PNG list, with old provenance archived. It claims no new H8 builder run.

Installation requires the externally reviewed promotion receipt. It invokes actual unchanged installer routing validation, `install_holes.py pre`, then `install`, original guards before/after and original protected checker before/after. Pre/install nonzero exits stop. Original protected raw exit1 and61 changed files are retained as FAIL; any additional/unreviewed path or hash drift stops. Installed metadata and hole07 bytes remain exact. Action receipt PASS describes copying/guards only; overall goal is still FAIL pending measured thresholds and eyes.

Run the final native proof separately with its current prepared runner/config and a fresh tag. **Do not put that runner inside heavy.sh**: it already acquires heavy around Unity. The coordinator never launches Unity/iOS/network/Git.

Limits: prepared hashes can become stale while another task runs; it intentionally refuses instead of rebasing. Promotion is a sequential archived transaction; an unexpected filesystem error may leave a partial stage/doc update, with the pre-state retained for root recovery and no automatic install. It does not claim a general concurrent-writer compare-and-swap guarantee. Only prepare/AST preflight has run here; actual heavy build/promote/install are root execution, unmeasured until their retained receipts/logs exist.
