# Scenario for Blender installation — 2026-10-15

GATE: INSTALL PASS

- Blender: 5.2.2 LTS, `/Applications/Blender.app`.
- Installed and enabled Scenario 0.11.0 as `bl_ext.Scenario.scenario`.
- Installed through the official remote repository: https://blender.scenario.com/repo/index.json. Blender can offer subsequent updates.
- Independently downloaded the official ZIP and verified SHA-256 against the catalog: `01b91ed6908a9a59ffce6ba7ee1e49c4599c583498cdf37577a61633978929a0`.
- Preferences saved. Output folder: `work/scenario-plugin/generated/` in this project.
- Local authenticated MCP endpoint responded to `tools/list`: 87 tools, at `http://127.0.0.1:9877/mcp`. The preferred port is 9876; the runtime selected 9877. Tokens are intentionally excluded from evidence. No new Codex MCP configuration was added.
- Additional arbitrary Python permission remains disabled.
- Open `work/jaw-sculpt-2026-10-12/Male_JawSculpt.blend` remained unmodified (`bpy.data.is_dirty == false`). No character or Unity asset changes.
- Proof: `scenario-installed.png` and `installation-check.json` beside this report.

GATE: CLOUD GENERATION FAIL

- Scenario API key and secret are not configured. No account connection, upload, paid generation, or live output-quality test was attempted. Installation and local tool enumeration are verified; cloud workflows are not.
- To enable: Blender → Edit → Preferences → Add-ons → Scenario → enter key and secret → Test connection. API access and Creative Units are required. Then use Viewport → N → Scenario.

## Practical uses to evaluate for Party Tennis

1. PBR material sets for separate garment/material experiments. Preserve customizable garment colors with neutral base detail; review generated maps before Unity URP integration.
2. Generate separate props from prompts or references, then manually check topology, scale, silhouette and mobile budget before acceptance.
3. Use scene captures and references for image/video look exploration. Generated imagery is concept evidence, not proof of actual Unity rendering or mesh fidelity.
4. Explore scene-description greybox layouts and 360 environment concepts in separate files when requested.
5. Use local agent tools for scene inspection, capture, quotes, generation tracking, and explicit result import/application after credentials are configured.

The repository labels the extension experimental. Generated hero replacements do not supersede the existing locked identity/silhouette or garment acceptance gates.

Sources: https://github.com/scenario-labs/blender-plugin ; https://github.com/scenario-labs/blender-plugin/blob/main/docs/USER_GUIDE.md ; https://github.com/scenario-labs/blender-plugin/blob/main/docs/KNOWN_LIMITATIONS.md
