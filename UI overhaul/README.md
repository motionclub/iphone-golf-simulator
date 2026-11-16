# UI overhaul

Open **index.html** in a browser to browse the package locally.

## Included

- **01 Current UI:** 15 latest full UI boards, interactive image gallery, prompts, revisions and review gates. Ten map systems plus selection/loading, character intros, setup/ready/pause, results and power-meter detail.
- **02 Loading art:** all 25 loading artwork images created on November 15, the contact sheet, original brief and seven supporting reference images. `gallery.html` shows the artwork; `out/` contains the original JPGs.
- **03 Power meter:** self-contained adjustable `power-preview.html`, the original fragment and the bundled-renderer export. The primary preview works locally without external libraries or a server.
- **04 Earlier concepts:** 21 previous boards and their prompts/notes. These document exploration; the current UI and latest requirements take precedence.
- **05 Reference maps:** 10 existing map screenshots and three gameplay captures used for UI context.
- **MANIFEST.json:** file paths, sizes and SHA-256 hashes for integrity verification.

## Current direction

Custom sculpted objects specific to each map. Compact corresponding materials for live HUDs and phone controls. Map names stand alone; player identity labels use usernames only. No sport-category labels or YOU/player-role badges. Power meter: small exact percentage with four notches at 25%, 50%, 75% and 100%.

These are mockups and generated artwork, not an implemented UI overhaul or runtime fidelity proof. Game code, scenes, gameplay and production assets were not changed by packaging. Original files were copied without recompressing images. No commits were created.

## Provenance

UI source: `ArtDir/ui/map-intro-concepts-2026-11-15/`.
Loading-art source: `work/daily-hole-in-one/loading-art/`.
Power preview source: the durable visualization created in this chat.
Reference map images: `GolfArcade/Unity/MenuArt/`; gameplay captures: `docs/ui-mockups/phase0_1_proof/`.
