# Original native adoption 1 — work-only handoff

Resource staging PASS. Full six-export/built-bundle adoption PENDING. No Unity, GPU, physical phone, production asset or project writes were performed in this task. Use accepted OriginalSeamBlinkFinish, Eye13 and skin revision1, not the local fairing experiment.

## Exact integration

`project.yml` includes GolfArcade recursively; its exclusions only remove Custom*/Higgs*/Hero*/Player* character files. All MatchHero_Original*.png files are already permitted. `project-unity.yml` inherits this authority and adds UnityFramework/Data; no YAML change is necessary. The checked-in projects use individual PBX resource entries, so both need `resource-registration.patch` (`git apply -p0`). It adds exactly these shared linear PNG LUTs to CharacterAssets AND the GolfArcade app resource phase:

- MatchHero_OriginalEye_RelativeIris.png (128 square)
- MatchHero_OriginalEye_RelativeSclera.png (128 square)
- MatchHero_OriginalSeam_RelativeSkinPigment.png (64 square)

The three hashes are locked in `accepted-contract.json` against the successfully rendered prior native parity export. These are uncompressed relative multipliers. Do not substitute sRGB-loaded textures, KTX garment data or bake the selected skin into them. Installed final MatchHeroSurfaces repair already handles their linear colour space and tint once.

## Root export and packaging

From repo root, with Unity idle:

```sh
python3 work/reference-rebuild/original-native-adoption1/export-work.py --editor /absolute/path/to/Unity
```

The three serial jobs in `export-configs.json` call MatchHeroLockerExport.Run, RunDistance and RunGolf. They explicitly write only this task's export/ and golden/ folders and pin accepted seam/blink/eyes/skin/continuous-normal flags. Main and distance tennis use MatchHero_<Sex>[ _Distance ]; golf uses GolfKitHero_<Sex>. The party preview uses distance tennis, so adoption requires all six manifests. MH_LOCKER_FACE_PARITY=1 adds the bounded forehand proof track only in tennis; golf `serve` already aliases Drive, while full independent goldens cover all golf motions.

Each export writes JSON, base/Rig LZFSE, 12 tennis practice-swing LZFSE files (golf has exactly0, as shipped), referenced PNGs and fresh golden/emote/blink fixtures. `package-resources.py` walks all six manifests. It copies shipped KTX only when exported/shipped source PNG SHA256 is identical; otherwise it uses the existing TextureConverter Highest/linear/flip-y/alpha-preserve ASTC4x4 atlas or ASTC8x8 normal/mask workflow. No garment bypass or fallback. GolfKit map namespace already exists in the current bundle.

After exports, coordinate GPU ownership and run:

```sh
zsh work/reference-rebuild/original-native-adoption1/run-minimum-checks.sh
```

This packages garment maps, audits all six exact contracts and both staged project resource phases, compiles current installed native runtime, and uses the existing repaired desktop Metal proof. It checks every exported blink CPU golden with the unchanged 0.2mm maximum gate and writes 12 Ready open/full portraits (both sexes × all three variants). Magenta fallback and actual SceneKit compiler failures fail the script; logs are native-runtime.log/native-metal.log. CPU/all-clip XCTest parity remains the existing VisualOverhaulNativeTests gate of 0.5mm.

`package-audit.json` becomes the exact reviewed publication inventory: `resources` are every runtime manifest/blob/map; `source_png_sidecars` preserve the matching uncompressed garment inputs for future exact KTX reuse. Root copies these from work/export to CharacterAssets after its serialized export and parity review; the scripts never publish. Preserve old GolfHero_* assets, unrelated equipment and all existing resource entries. Do not copy generated-cache folders, independent goldens, diagnostic render images or task scripts into the app.

After root installs reviewed assets and patches:

```sh
zsh work/reference-rebuild/original-native-adoption1/build-bundle-check.sh
```

This performs a native iOS Simulator build-for-testing only, without launching any simulator or phone, then hashes every referenced file in the actual built .app against the export. Full GolfArcadeUnity linking still depends on root's current Unity iOS export; its resource phase is independently checked by the same audit.

## Exact tests / backward compatibility

`test-contract-migration.patch` updates three already-registered test files. Accepted Body counts remain exactly Male33705/Female23230 and Face3824/3004; legacy branches retain their exact33196/23683 counts. There is no count-range/tolerance relaxation. Original Body has UV0 + bind xy/z (3 channels); Original Face has UV0 (1), skinning and half/full morphs. Legacy Body2/bare Face0 channels remain valid only under the old manifest metadata. Golf preserves the canonical53 character bones plus its pre-existing trailing Club bone; tennis remains53. Rig weights/rest/bind hierarchy and manifest binary layout are unchanged.

Tests now verify selected skin via the material registry tint/heroTint rather than casting the new diffuse LUT to UIColor. They assert the authored skin response exactly (skinFinish Male1/Female2, smoothness .38, no old normal bump), six original face roles (+female IrisIn), and the required LUT bundle presence. Old skin-bump shader tests remain in the legacy branch. The strict all-six test prevents passing while a distance/golf export stays legacy.

Run relevant XCTest targets with VISUAL_GOLDEN_DIR set to this task's fresh golden folder. The patched LockerMirrorTests also use that same variable for both base and emote fixtures. Old golden vertex indices under work/locker-mirror and work/online-lobby cannot validate the new source; do not silently reuse them. The three staged XCTest files parse; XCTest compilation/execution is pending root build. Do not claim the historical full test suite passed.

Old manifests still decode because new Look fields are optional, and the native single-Hero_Blink fallback remains. The accepted two-stage path does not inherit old gaze/decal overlays. No manifest version bump is needed. Asset-loading caches are keyed by variant; restart native presentation after publication to avoid old cached geometry/materials. Unity VISUAL_ORIGINAL_SEAM=0 is an explicit Unity/export-time legacy optout; native JSON does not read that environment flag. Native rollback requires restoring the previous six-manifest/resource snapshot, or separately exporting/registering/resolving legacy manifests. The staged legacy-control profile writes a separate two-hero main-tennis control and never overwrites adoption output; it is not an invented runtime native toggle.

## Runtime warnings / hairstyle diagnosis

reference-face-default26.log:716–748 and766–798 identify StandardCharacterArms.Initialize/Awake during Instantiate(StandardCharacters/standard_<sex>_tennis), TennisActor.Build:248. Its fallback searches golf-era arm renderer names, V4 skin and hand-name renderers. It predates MatchHeroLook/OriginalSeam and cannot be looking for the new material at that point. TennisHeroSetup.Attach:49–51 disables all old actor renderers outside the newly attached match hero. The accepted Body contains its complete skinned arms and does not use StandardCharacterArms. The warning is obsolete hidden-rig material discovery, not evidence of missing first-person/new hero arms. No patch changes that rig's behavior.

The default rival is built with the opposite sex in TennisGame.Start:239 and is not a named roster hairstyle selection. TennisHeroSetup attaches the bald HeroBase, and HeroKit.Apply:65–78 intentionally applies skin/racket/kit while bypassing hair/headwear because old hair was fitted to the old head. Thus bald female rival is current deliberate character policy, not a failed new source hookup. Named roster haircut values are likewise retained but currently ignored. Hair support would be a separate requested source/attachment lane.

## Checks actually run here

PASS: both staged PBX plists; both patches apply-check against current sources; Python syntax; shell syntax; current installed Data/Surfaces/Motion + all-variant NativeParity Swift typecheck; staged XCTest Swift parse. PASS: rehearsal using the existing accepted main-tennis exports—2 variants,58 exact runtime files,25 matching garment-source sidecars, all58 referenced exactly once in BOTH staged resource phases. No fresh distance/golf exports, six-variant renderer run, XCTest execution or actual built-bundle verification yet. These remain hard adoption gates.

Visual defects remain soft lips/face plane fidelity, jagged closed crease and male partial-blink fold. Prior repaired native actual proof passed60 portraits with0 magenta and max error Male.00433mm/Female.01350mm; that is prior evidence, not a six-variant adoption result.

## 2026-10-07 follow-up status

Fresh root exports PASS main41.51s/distance35.07s/golf43.88s. All-six work packaging/audit PASS119 runtime resources/50 garment maps, exact accepted source/LUT hashes. Corrected staged audit to the unchanged existing golf0 versus tennis12 practice-frame contracts. Metal began but was interrupted at root request for the urgent shirt capture (exit130); no all-six native appearance/parity result or production asset adoption. GPU released. ADOPTION_STATUS.json records partial files and pending gates. Extra proof-only Forehand is the final unused tennis rig clip: Male1,317,504/Female1,301,152 decoded tail bytes, repeated for distance (5,237,312 total). Practice swing remains exactly12 frames/1.2s. Keep this proof package separate and remove the extra track via clean MH_LOCKER_FACE_PARITY=0 exports before shipping; no binary surgery or production copy performed here.
