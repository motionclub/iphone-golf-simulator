# Codex task: golf loading-screen art (characters playing on the courses)

Generate 6 images with GPT Image and save them to the exact paths below. **Only make the images.** Do not change any code, project files or other assets. Claude will wire them into the game.

Repo root: `/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator`
All paths below are relative to it.

## What these are for

MotionSports is a stylized 3D party-sports game. These pictures are full-screen backgrounds for the golf loading screens. One shows while a Daily Hole in One round or a golf course loads, and another shows between holes. Each picture shows **one of our two golfers playing golf on one of our three courses**.

On screen, the left side carries the loading text and a progress bar, and a small tip card sits at the top right. Keep the left third calm, and keep the golfer at the right third, clear of the top-right corner.

## Reference images (attach them to every generation)

Folder: `work/daily-hole-in-one/loading-art/refs/`

| File | What it is |
|---|---|
| `character-male.jpg` | **Male golfer, in game.** Navy cap, teal polo, navy trousers, white glove, white-and-navy shoes, tanned skin. |
| `character-female.jpg` | **Female golfer, in game.** Navy cap with a white front panel, peach-salmon polo, navy pleated skirt, white glove, white sneakers. |
| `character-female-turnaround.jpg` | The same female golfer from 8 angles, including a head close-up. Use it for her face and proportions. |
| `course-cliffside.jpg` | **Cliffside course**, the painted art the game already uses. Clifftop greens over a turquoise sea, sea stacks, rock arches, floating islands, pink flower beds. |
| `course-magma.jpg` | **Magma Open course**, the painted art the game already uses. A green fairway ridge through glowing lava rivers, lava waterfalls, dark crater cliffs, dusk sky. |
| `course-wildisles.jpg` | **Wild Isles course**, in game. Faceted pine trees, a wooden lookout tower, flower beds, sand bunker, green with a red flag. |
| `course-wildisles-overview.jpg` | Wild Isles from above: a pine-covered island with stripy fairways in a deep blue sea. |

**Match the characters closely.** They are smooth, soft "plastic toy" stylized 3D figures, like a polished Nintendo/Switch Sports look:
- simple faces;
- clean shapes and slightly chunky proportions;
- not realistic people and not anime;
- outfit colours exactly as listed.

**Match each course's painted look** to `course-cliffside.jpg` and `course-magma.jpg`: rich, saturated, soft painterly 3D, crisp light. Wild Isles must look like the same family of art, even though its reference is an in-game screenshot.

## Output specs (all 6)

- **Size:** 16:9 landscape. Generate at 1536×864 or larger, then save as **1920×1080 JPG**, quality about 90, under 900 KB each.
- **Golfers:** exactly one golfer per image, full body visible, golf club in hand.
- **Anatomy and props:** correct hands (5 fingers, gloved left hand), no warped or stretched limbs, the club in one piece, the ball the size of a real golf ball.
- **No text of any kind:** no logos, letters, numbers, UI, HUD, watermark, or signs with writing.
- **Composition:**
  - left third calm (sky, sea, distant scenery);
  - golfer in the right third, roughly between 15% and 85% of the frame height;
  - nothing important in the top-right 25% × 25% corner;
  - nothing important in the bottom 12% (the progress bar sits there).

## The 6 images

### 1. `out/golf-cliffside-male.jpg`
Refs: `course-cliffside.jpg`, `character-male.jpg`

> Wide 16:9 game loading-screen key art in the exact painted, vibrant stylized-3D style and location of the course reference: a clifftop golf course over a turquoise ocean with tall sea stacks, rock arches, small floating islands and pink flower beds. The male golfer from the character reference (smooth stylized 3D game character, navy cap, teal polo shirt, navy trousers, white golf glove, white and navy shoes) stands on a clifftop tee in the right third of the frame in a powerful full follow-through, club wrapped over his shoulder, watching his golf ball fly in a bright white arc toward an island green with a red flag. Sunny late-morning light, crisp shadows, slightly low cinematic angle. The left third is calm open sky and sea. One golfer only, full body, correct hands. No text, no logos, no UI.

### 2. `out/golf-cliffside-female.jpg`
Refs: `course-cliffside.jpg`, `character-female.jpg`, `character-female-turnaround.jpg`

> Wide 16:9 game loading-screen key art in the exact painted, vibrant stylized-3D style and location of the course reference: an island golf green on a clifftop over a turquoise ocean, tall sea stacks and rock arches behind, pink flower beds. The female golfer from the character references (smooth stylized 3D game character, young woman, navy cap with a white front panel, peach-salmon polo shirt, navy pleated skirt, white golf glove, white sneakers) is in the right third of the frame, putting: putter just through the stroke, eyes following her golf ball rolling across the green toward the cup with a red flag. Warm sunny light, soft shadows. The left third is calm open sky and sea. One golfer only, full body, correct hands. No text, no logos, no UI.

### 3. `out/golf-magma-male.jpg`
Refs: `course-magma.jpg`, `character-male.jpg`

> Wide 16:9 game loading-screen key art in the exact painted, vibrant stylized-3D style and location of the course reference: a volcanic golf course, a bright green fairway ridge winding through glowing orange lava rivers, lava waterfalls pouring from dark crater cliffs, floating embers in a purple dusk sky. The male golfer from the character reference (smooth stylized 3D game character, navy cap, teal polo shirt, navy trousers, white golf glove, white and navy shoes) stands on the green ridge in the right third of the frame mid follow-through with a wedge, his golf ball soaring in a glowing arc over the lava toward a green with a red flag. Warm lava rim light on the golfer. The left third is calm dark crater and sky. One golfer only, full body, correct hands. No text, no logos, no UI.

### 4. `out/golf-magma-female.jpg`
Refs: `course-magma.jpg`, `character-female.jpg`, `character-female-turnaround.jpg`

> Wide 16:9 game loading-screen key art in the exact painted, vibrant stylized-3D style and location of the course reference: a volcanic golf course, a bright green putting green on a rock island ringed by glowing lava rivers, lava waterfalls pouring from dark crater cliffs, embers in a purple dusk sky. The female golfer from the character references (smooth stylized 3D game character, young woman, navy cap with a white front panel, peach-salmon polo shirt, navy pleated skirt, white golf glove, white sneakers) stands on the green in the right third of the frame celebrating with a joyful fist pump, club in her other hand, as her golf ball drops into the cup beside the red flag. Warm lava rim light. The left third is calm dark crater and sky. One golfer only, full body, correct hands. No text, no logos, no UI.

### 5. `out/golf-wildisles-male.jpg`
Refs: `course-wildisles.jpg`, `course-wildisles-overview.jpg`, `character-male.jpg`

> Wide 16:9 game loading-screen key art, painted vibrant stylized-3D game style (rich, saturated, soft painterly 3D like a polished Nintendo sports game), set on the island course of the course references: a lush rolling striped fairway framed by tall faceted pine trees, a wooden lookout tower on the hill, colourful flower beds, a white sand bunker and an elevated green with a red flag, the deep blue sea between the pines, golden late-afternoon sky with soft clouds. The male golfer from the character reference (smooth stylized 3D game character, navy cap, teal polo shirt, navy trousers, white golf glove, white and navy shoes) stands on the fairway in the right third of the frame finishing a crisp chip shot, the golf ball arcing toward the flag. The left third is calm sky and pine silhouettes. One golfer only, full body, correct hands. No text, no logos, no UI, no HUD.

### 6. `out/golf-wildisles-female.jpg`
Refs: `course-wildisles.jpg`, `course-wildisles-overview.jpg`, `character-female.jpg`, `character-female-turnaround.jpg`

> Wide 16:9 game loading-screen key art, painted vibrant stylized-3D game style (rich, saturated, soft painterly 3D like a polished Nintendo sports game), set on the island course of the course references: a lush rolling striped fairway framed by tall faceted pine trees, a wooden lookout tower on the hill, flower beds, an elevated green with a red flag, the sea glimpsed between the pines, bright midday sky with soft clouds. The female golfer from the character references (smooth stylized 3D game character, young woman, navy cap with a white front panel, peach-salmon polo shirt, navy pleated skirt, white golf glove, white sneakers) stands on the fairway in the right third of the frame at the top of a full iron backswing, eyes on the ball. The left third is calm sky and pine silhouettes. One golfer only, full body, correct hands. No text, no logos, no UI, no HUD.

## Check every image before saving (regenerate if any fails)

1. **One golfer only**, and they match their reference: same outfit colours, cap, and soft stylized look. Not a realistic person.
2. **Body and props:** hands have 5 fingers with no fused or extra digits, limbs are not warped or stretched, there is exactly one club and it isn't bent or doubled, and the ball is golf-ball sized.
3. **No text or letters anywhere.**
4. **Composition:**
   - left third calm;
   - golfer in the right third;
   - top-right corner and bottom strip free of anything important.
5. **Course:** clearly the referenced course (sea stacks and arches / lava / pines and lookout tower), in the painted style of the existing Cliffside and Magma art.

## When done

- Save the 6 files to `work/daily-hole-in-one/loading-art/out/` with exactly the names above.
- Make a contact sheet of all six at `work/daily-hole-in-one/loading-art/out/contact-sheet.jpg`.
- Report which images needed regenerating and why.
- Do not commit anything.
