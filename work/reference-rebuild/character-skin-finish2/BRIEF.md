# Existing skin finish candidate 2

WORK ONLY, one candidate plus matched control. No Assets or Unity invocation by this agent. Reuses the current accepted source head and blink-finish weight/shape candidate; no new mesh, normals, skin presets, bone/rest changes or animation edits.

## Most likely flatness sources

Actual Ready and Serve portraits show washed broad midtones with weak clean highlights, strong pink patches on the male cheeks, and poorly separated lip pigment. Code adds wrapped diffuse from every light to full SH ambient; the studio's key/fill plus ACES compress the resulting bright skin values. The pigment swatch's SkinResponse additionally compounds the base cheek tint with up to ~18% green reduction and cuts specular strength to .72. This enhances broad blotches while weakening the shape cue the targets use. Continuous 8mm normals and existing lip/eyelid anatomy also limit definition, but remain unchanged in this material-only candidate.

## Single bounded response

- Opt-in per Body material `VISUAL_CHARACTER_SKIN_FINISH=1`; shader property defaults 0. All eye/brow/equipment/cloth roles retain current response. BaseColor and saved skin tone are untouched.
- Direct skin diffuse energy .84; SH ambient .70; wrap .20. Existing geometry shadows receive a small .12 fill floor, softening their harshest creases. Body rim contribution .45 of current prevents a glowing plastic edge.
- A broad restrained skin specular lobe replaces the sharper varnish lobe on Body only. Regional smoothness .32-.40, direct specular strength .95. No screen-space effect, texture noise, added normal map, sampler, pass or mesh attribute.
- Existing registered cheek/ear/nose pigment becomes a quiet ~3.5-4.5% channel variation; male lower-face tone is slightly cooler and darker, without invented beard hairs.
- OriginalSeam's existing UV0 encodes lip/seam/nostril masks. Shader uses those exact masks with a tighter smooth transfer to reduce diluted pigment halos and strengthen lip separation. This changes pigment response, not lip geometry. The original LUT remains bound and unchanged; the control samples it as before.

## Root integration

Apply MatchHeroLook.cs.patch, TennisCharacter.shader.patch, HeroLighting.hlsl.patch to current files; avoid overwriting whole candidate copies. Existing source hashes are in source-manifest.json. The CharacterShader vertex stage and old HeroCharacterShade function remain byte-exact; candidate branch affects only flagged Body material shading.

Run capture-skin-finish2.json, which has exactly candidate1 vs control0. Both use identical OriginalSeam/Eye13 + BlinkFinish1 source, continuous normals, saved tone/swatches, studio lights, ACES/exposure, pose sampling and camera. Includes Ready front/threequarter/full/Intro plus Serve mid/contact open/full posed portraits. No post, global lighting, world or garment change.

Actual criteria: cleaner forehead/cheek light gradients; restrained broad highlight; natural stronger lip separation; no hard painted mouth line, oily scalp, dark eye sockets, faceting amplification or loss of tone readability. Existing jagged full-blink crease and male half-blink folds remain separate source art failures. Studio A/B does not certify actual game lighting or native parity.

## Source gate

PASS: production sources untouched by this agent; vertex stage exact; existing generic surface lighting exact; opt-in default 0; pigment multipliers stay positive/bounded and broad lobe finite/bounded in numeric sweep. Compilation and actual art review PENDING root serialized capture. No reference-fidelity completion claim.
