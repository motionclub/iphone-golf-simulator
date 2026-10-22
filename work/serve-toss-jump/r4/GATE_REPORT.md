GATE: staged measured serve checks PASS. NOT INSTALLED. Full-sequence human review and post-install validation remain pending.

Five distinct live ReadyIdle entry phases were tested for each hero in fresh scenes. The user approved the walk and dribble in trial7. Subsequent fixes eased the entry turn/body lowering, bounded wrist twist while preserving the palm-down hold, blended the toss arm back to authored motion, and corrected release clearance for the rendered ball radius. This work modified no production files and made no commit. Current celebration changes from another chat are preserved in the fresh install patch.

| Gate | Status | Measured result |
|---|---|---|
| G1 Feet down | PASS | M/F max 0.629/0.579 mm (limit 10) |
| G2 Trophy load | PASS | M/F [70.90707, 70.90717]/[70.71921, 70.71922] degrees; times [1.312903, 1.312903]/[1.278853, 1.278853] s |
| G3 Takeoff | PASS | M/F [1.594016, 1.594016]/[1.594016, 1.594016] s |
| G4 Air/contact | PASS | Both feet clear; front knees below 35 degrees; back foot higher |
| G5 Apex | PASS | M/F [1.761667, 1.761667]/[1.761667, 1.761667] s |
| G6 Landing | PASS | Front touch 1.878333/1.878333 s; settled 1.961667/1.961667 s |
| G7 Entry | PASS | Worst M/F 25.574/25.707 mm across five distinct phases; limit 30 |
| G8 Contact | PASS | Strings delta 13.831/10.685 mm; elbow 172.796/172.443 degrees |
| G9 Smoothness | PASS | Left hand max 126.744/114.336 mm; wrist max 14.5002/14.5001 degrees; racket steps and follow-through pass |
| G10 Clearance | PASS | 0 new or increased pairs; M/F -129/-36 intersecting vertices |
| G11 Foot drift | PASS | M/F 3.836/3.751 mm; limit 5 |
| G12 Times/prefabs | PASS | 0.20/0.70/1.3333334/1.70 s; length 2.5 s; prefab hashes unchanged |
| G13 Scope/control | PASS | User expanded ownership to arm/dribble; only owned runtime paths changed. Replant steps before/after M 4/4, F 3/3. Current LockFeet hunk saved. |
| G14 Proof | PASS | 16 films; all decode start/middle/end; contact sheet and populated live traces included |
| G15 Installed equals tested | PENDING | Not installed. Back up and apply a fresh hunk patch only after full visual approval; then rerun on production. |
| G16 Eye | PENDING | Walk/dribble approved by user (perfect). Full serve changed after that approval and needs review. 26c: Adnan’s eye overrides any agent GATE PASS. |

The measured foot lift was the procedural 65 mm replant arc. Its guard and independent plants reduced the previous approximately 64 mm lift to under 0.63 mm. The new entry smoothing keeps the final stagger and jump/landing targets. Original rollback remains in work/serve-toss-jump/rollback_r3; a fresh rollback will be saved before any installation.

Film paths:
- [serve_r4_female_back.mp4](film/serve_r4_female_back.mp4)
- [serve_r4_female_back_half_speed.mp4](film/serve_r4_female_back_half_speed.mp4)
- [serve_r4_female_front.mp4](film/serve_r4_female_front.mp4)
- [serve_r4_female_front_half_speed.mp4](film/serve_r4_female_front_half_speed.mp4)
- [serve_r4_female_game.mp4](film/serve_r4_female_game.mp4)
- [serve_r4_female_game_half_speed.mp4](film/serve_r4_female_game_half_speed.mp4)
- [serve_r4_female_side.mp4](film/serve_r4_female_side.mp4)
- [serve_r4_female_side_half_speed.mp4](film/serve_r4_female_side_half_speed.mp4)
- [serve_r4_male_back.mp4](film/serve_r4_male_back.mp4)
- [serve_r4_male_back_half_speed.mp4](film/serve_r4_male_back_half_speed.mp4)
- [serve_r4_male_front.mp4](film/serve_r4_male_front.mp4)
- [serve_r4_male_front_half_speed.mp4](film/serve_r4_male_front_half_speed.mp4)
- [serve_r4_male_game.mp4](film/serve_r4_male_game.mp4)
- [serve_r4_male_game_half_speed.mp4](film/serve_r4_male_game_half_speed.mp4)
- [serve_r4_male_side.mp4](film/serve_r4_male_side.mp4)
- [serve_r4_male_side_half_speed.mp4](film/serve_r4_male_side_half_speed.mp4)
