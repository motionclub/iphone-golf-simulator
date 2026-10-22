# Frozen round1 aerial capture configs

Prepared before the first round1 capture. All files are under v3. No Unity,
Blender build, production asset or Git writes occurred during preparation.

`proof_cfg_round1.json` and `split_outline_cfg_round1.json` are byte-identical
copies of the original semantic/mask configs. They have no camera fields.
Actual camera values are in `stills_cfg_extra.json`, `stills_cfg_12.json` and
`aerial_cfg_3.json`. Only aerial `pos`, `look`, and `fov` may differ. Names,
hole, kind, ball, aim, putting, all original nine views, green mow support views,
six address views and cost config remain identical.

|Hole|Position before → round1|Look before → round1|FOV before → round1|
|---|---|---|---|
|8|[120,290,-170] → [100,135,-55]|[5,0,170] → [2,6,185]|53 → 57|
|9|[140,360,-200] → [120,185,-65]|[-28,0,230] → [-22,6,230]|53 → 57|
|10|[-130,320,-165] → [-95,175,-105]|[130,0,100] → [145,6,125]|58 → 58|

Eight field differences per each of the three aerial shot configs: 24 total.
The exact field-level differences and original/frozen file hashes are in
capture_config_manifest.json. parse_validation.json and ../runtime_adapter_validation.json
confirm JSON parse, source SHA matching, fixed field scope, frozen SHORE SHA,
unchanged 2px/6px raster support, unchanged semantic bytes, unchanged six cost
frames and equality of all measurement adapters after only run path normalization.
The first scratch comparison incorrectly compared adapters' output paths literally;
that exit1 is retained in ../runtime_adapter_validation_attempt1.txt. It launched
no native gate. The corrected path-normalized check passed.

|Config|Original SHA256|Frozen round1 SHA256|Changed fields|
|---|---|---|---|
|stills_cfg_9.json|95663944afa35c47de63f6bea3e6b3faac633b785580956f2731d250863ab9e2|95663944afa35c47de63f6bea3e6b3faac633b785580956f2731d250863ab9e2|0|
|stills_cfg_extra.json|f77dbde7c1f9e8320451a18da3fa191b17fa685b8912dea798edb5a4f6d3205c|785d975e7bc274ff79611d45761ec644770c7ad8725c03b11f5f181692afc6d0|8|
|stills_cfg_12.json|76169c73f2f69fa745b3ba8ee162cc1676cf4ecb8d5134f64300765cbf0749bd|90eb633addf11aa2e7e958487631a8c73076e654ca57d78dbce72586d1c16fd6|8|
|aerial_cfg_3.json|d9ea844e828cfced7995ec9f6faaaa6f541327cec40ec9330e7ac91c44956b1b|031195bda4edb546dc4bbf9a9a5acb8c54cf5138d7878c7534e5c2a36e11b78e|8|
|proof_cfg_round1.json|90c9a29f5525d1344baeff55e0979a4e1a0697fd7d11e031d5f5e054ae9d7168|90c9a29f5525d1344baeff55e0979a4e1a0697fd7d11e031d5f5e054ae9d7168|0|
|split_outline_cfg_round1.json|3ef2f327157bed35b9549867c58c255d2d8cfd9aad56322432d11aa6fbd6be0d|3ef2f327157bed35b9549867c58c255d2d8cfd9aad56322432d11aa6fbd6be0d|0|
|cost_cfg.json|2fe026a3716966bff0a4b540b5a8e86a4b0459cf8096c7e15380bf1976246fbd|2fe026a3716966bff0a4b540b5a8e86a4b0459cf8096c7e15380bf1976246fbd|0|

The validated optional runtime route uses these inherited environment variables:

```sh
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
V="$R/work/postcard-look/v3"
C="$V/p7/round1/capture_configs"
export GOLF_PROOF_CAPTURE_CONFIG_DIR="$C"
export GOLF_V3_PROOF_CFG="$C/proof_cfg_round1.json"
export GOLF_V3_SPLIT_CFG="$C/split_outline_cfg_round1.json"
```

prepare_runtime.py validates the full frozen manifest and original source hashes
before selecting override shot configs, and writes the source/manifest relationship
to the fresh run's capture_config_manifest.json. The existing run_proof.sh inherits
these variables; it needs no new executable branch. With the capture override
variable unset the original config route remains the default.

The source still config originals have not changed. The default/round1 scratch
adapter runs are runtime_adapter_check_default and runtime_adapter_check_round1.
This is parse/routing validation only; visual thresholds and native gates remain
unmeasured until root executes the final installed run.
