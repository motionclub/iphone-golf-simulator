# Low tennis chase camera — 2026-10-14

GATE: SHOT_A_STARTING_GEOMETRY PASS — 3.5 m behind, 2.5 m high, 0.6 m to the right, 46° lens. Stable shoulder puts the player left of centre for either hand.

GATE: PLAYABLE_TRACKING PASS — camera/aim ease at 9/s, ordinary deep-ball retreat up to 1 m; close lobs and near-player landing cues can add dolly room. Ordinary pitch stays within 10° downward; height tracking retains lobs without a lens switch. Ground ring clears the existing timing HUD. Narrow halves track cross-court balls.

GATE: DEPTH_CUES PASS — thicker unlit landing ring follows the rendered court plane. Ball-only shadow retains a faint opacity floor above 4 m; actor shadows keep their prior behavior.

GATE: MATCH_PHASES PASS — serve/receive/rally/point-result/match-result use chase, with the previous elevated view selected per session. Both split layouts follow the selected mode from each player's end. Chase also follows replay poses; the opening venue introduction remains before play.

GATE: SETTINGS PASS — Settings → Display → Tennis camera offers Chase and Elevated; selection persists and applies to the next match. Native simulator choice, persistence, back and layout checks pass.

GATE: VALIDATION PASS — seven EditMode tests, three PlayMode tests and one native simulator test pass. Captures are real Unity gameplay renders using deterministic shot fixtures and the existing animation sources, not painted mockups. `comparison.jpg` places A_close beside serve, baseline rally, 8 m lob and net volley.

GATE: SCOPE PASS — only camera/settings/depth-cue code, associated regression tests and this proof staged. Concurrent gameplay edits remain outside this patch; no animation/driver source or animation assets staged by this task. No commit created.

Validation used an isolated Unity clone containing committed gameplay plus this camera patch. The shared checkout has other work in progress. Native source references were regenerated only in the isolated test copy; the main project file is untouched. Physical-device play feel is not measured by these editor/simulator checks.
