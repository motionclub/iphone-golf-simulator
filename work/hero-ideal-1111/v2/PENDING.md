# V2 remake — ready to run, blocked by the image service's daily limit

Request (2026-11-11): remake the ideal-hero sheets, but with our own more generic faces.

**Status:** both attempts (four submissions) were refused with "You've reached the daily generation limit for your grace period". Nothing was generated and no credits were spent. The face references are uploaded and the prompts below are final, so this can run as soon as the limit resets or the plan is updated.

## Face references (uploaded, built from our own renders)

| Hero | Local file | Media id |
|---|---|---|
| Male | `refs/male_face_ref.jpg` | `a664eeca-695d-49c6-87c3-ab5219487251` |
| Female | `refs/female_face_ref.jpg` | `92fa7204-4841-4d2e-b49a-35c34b46afa6` |

Each is four renders of the current in-game head: one bare-headed in menu light, then front, three-quarter and side in the studio.

## Settings

Model `gpt_image_2_6`, 16:9, 2k, quality high, 2.75 credits each. Each request passes two `image_references`: the face sheet first, then the V1 turnaround (`1d44de3d-6459-4539-b8a6-cb1b96a0952f` male, `84d9c66b-9534-4f5b-82d9-09ac33aa85d7` female).

## Prompt, male turnaround

Character turnaround model sheet, four consistent full-body views in a row — front view, 3/4 view, side profile, and back view, evenly spaced, same scale, feet on one ground line, relaxed A-pose with arms slightly away from the body and open relaxed hands, identical original male character on all views, neutral light grey seamless studio background. Recreate the second reference image (the four-view turnaround of a man in a white tennis polo and navy shorts) with the same layout, pose, body proportions, outfit, shoes, wristband, materials and lighting, but REPLACE HIS FACE AND HEAD with the face shown in the first reference image (four renders of the same plain 3D game character head, front, three-quarter and side): copy that face exactly — the same head shape and long jaw, the same normal-sized realistic dark brown eyes that are NOT enlarged, the same thick straight dark eyebrows, the same nose, the same thin closed lips with a neutral calm expression, the same ears, the same smooth medium-tan skin, a plain generic friendly everyman face with no strong personality. He is completely bald with a smooth clean scalp and no hair at all, and he wears the same cap as in the first reference image: a white six-panel baseball cap with thin navy seam piping, small mesh vents and a navy brim, sitting naturally on his head so the bald scalp shows below it at the sides and back. Ignore the clothes and backgrounds in the first reference; use it only for the face, head and cap. Head at natural size for a body about six and a half heads tall, hands and forearms moderate and not oversized. Outfit unchanged: white short-sleeve pique tennis polo with navy collar, two-button placket, navy sleeve cuffs with one thin coral stripe, small plain round blank crest patch on the left chest, navy athletic shorts with a white side stripe, white ribbed ankle socks, clean white low-top court sneakers with a rounded toe lower than the heel, navy heel tab and a thick white sole with a navy outsole line, white wristband on the right wrist. Stylized 3D game character render, smooth satin skin, matte knit fabric with fine weave and real cloth thickness at hems, soft three-point studio lighting with a gentle rim light, high-end real-time game model quality, sharp, single character repeated four times only, no hair, no props, no racket, no text, no labels, no watermark, no logos, no frame borders, no distorted anatomy, no extra fingers

## Prompt, female turnaround

Character turnaround model sheet, four consistent full-body views in a row — front view, 3/4 view, side profile, and back view, evenly spaced, same scale, feet on one ground line, relaxed A-pose with arms slightly away from the body and open relaxed hands, identical original female character on all views, neutral light grey seamless studio background. Recreate the second reference image (the four-view turnaround of a woman in a white sleeveless tennis polo and navy pleated skirt) with the same layout, pose, outfit, shoes, wristband, materials and lighting, but REPLACE HER FACE AND HEAD with the face shown in the first reference image (four renders of the same plain 3D game character head, front, three-quarter and side): copy that face exactly — the same rounded head shape with a small soft chin, the same large round brown eyes with simple lids, the same thin arched dark eyebrows, the same small button nose, the same small closed lips with a neutral calm expression, the same ears, the same smooth medium-brown skin, a plain generic friendly face with no strong personality. She is completely bald with a smooth clean scalp and no hair at all, no ponytail, and she wears the same cap as in the first reference image: a white six-panel baseball cap with thin navy seam piping, small mesh vents and a navy brim, sitting naturally on her head so the bald scalp shows below it at the sides and back. Ignore the clothes and backgrounds in the first reference; use it only for the face, head and cap. Make her arms and legs slimmer and less muscular than in the second reference: toned but slender, with a softly rounded shoulder, a gentle upper arm and a forearm that tapers to the wrist, and smooth athletic legs without bulging muscles. Outfit unchanged: white sleeveless collared tennis polo with navy collar, two-button placket and navy armhole binding, small plain round blank crest patch on the left chest, navy pleated tennis skirt with a flat waistband and one white stripe near the hem, built-in navy shorts just visible, white ribbed ankle socks, clean white low-top court sneakers with a rounded toe lower than the heel, navy heel tab and a thick white sole with a navy outsole line, white wristband on the right wrist. Stylized 3D game character render, smooth satin skin, matte knit fabric with fine weave and real cloth thickness at hems, soft three-point studio lighting with a gentle rim light, high-end real-time game model quality, sharp, single character repeated four times only, no hair, no props, no racket, no text, no labels, no watermark, no logos, no frame borders, no distorted anatomy, no extra fingers

## Then

Once both turnarounds exist, remake the detail, colourway and in-game sheets from them (same prompts as V1, with the new turnaround job ids as references), plus the two sheets V1 never got: faces and expressions, and golf and bowling kits. Seven sheets in total, about 19 credits.

## Hair: decided

Bald under a cap, like our current heroes (chosen 2026-11-11). The prompts above already say so. A second attempt after that choice was refused by the same daily limit.
