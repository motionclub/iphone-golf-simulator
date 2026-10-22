# Drop-in candidate for the LOOK_FILES failure (PROPOSAL, not applied)

`postcard_look_verify.py` fails `LOOK_FILES@blend` and `LOOK_FILES@fbx` on every hole: Fairway_C.png reaches the lead's floor (luminance sd >= 0.03 in 90 % of the 64 px windows) in 1 % of its
windows (p10 0.0140), Green_C.png in 0 % (p10 0.0101). The textures are the texture owner's (`blender/scripts/golf_look_textures.py` regenerates them) and the floor is the lead's number, so
the hole 9 builder did NOT touch `Unity/Assets/Resources/Course/Look/`. What this folder holds is a measured way to close the line:

* `Fairway_C_midfreq_candidate.png`, `Green_C_midfreq_candidate.png`: the current PNGs with a multiplicative, zero-mean, band-limited (wavelength 6-24 px, built in the frequency domain, so
  it tiles) noise on RGB, amplitude 0.06 (Fairway) and 0.07 (Green). Made by `tools/grass_midfreq_proposal.py` (deterministic seeds 11 / 12).
* `grass_midfreq_proposal.json`: windows reaching sd 0.03 (raw) and the block-averaged check, p10, mean RGB and hue for amplitudes 0.03-0.10.
* `../evidence/grass_proposal_crops.png`: 512 px crops, original | candidate for Fairway, original | candidate for Green.

Measured (the verifier's own window statistic):

| texture | windows >= sd 0.03 now | with candidate | block-averaged check now | with candidate | mean RGB shift | hue |
|---|---|---|---|---|---|---|
| Fairway_C | 1 % (p10 0.0140) | 100 % (p10 0.0359) | 66 % | 93 % | 0.0001 / 0.0006 / 0.0007 | 73.75 -> 73.75 |
| Green_C | 0 % (p10 0.0101) | 100 % (p10 0.0435) | 36 % | 91 % | 0.0006 / 0.0004 / 0.0006 | 72.41 -> 72.41 |

Whole verifier with the two candidates substituted (`postcard_look_verify.py 9 --look-dir work/postcard-look/v2/hole09/round3/proposal_look_dir`, staged hole 9 blend + FBX):
`evidence/look_verify_with_candidate_textures.log`: LOOK_FILES@blend PASS, LOOK_FILES@fbx PASS, ALBEDO_DISTINCT (Fairway vs Green correlation 0.38), GRASS_ALBEDO_HUE (73.6 / 72.4 / 68.1) and
every other line unchanged. The one other FAIL in that run (`LK_TEXTURED@blend`) is an artefact of the scratch folder: the staged blend's images point at the repo Look folder.

To adopt (owner of the textures / lead; no hole rebuild, no reinstall needed): put the same noise step into the Fairway and Green generators in `golf_look_textures.py` (a copy of the two PNGs
would be overwritten by the next regeneration), re-run `postcard_look_verify.py 9` (and 8, 10), and re-calibrate the Game-view grass tint only if the lit mean is judged off (the mean RGB moved by <= 0.0007).
The grain is fine turf-like mottling (see the crops); whether it is too busy for the Switch Sports look is a judgement for the lead, which is why this is not applied.
