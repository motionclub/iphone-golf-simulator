# Animation safety and performance — 2026-10-15

User scope: both sports, all heroes, gameplay and emotes. Character identity and customization remain fixed. Stage only; no commits.

Priority: rig-aware body/garment clearance, female wrist/arm correctness, backhand elbow path, then transitions, timing, expressive faces, footwork, reach recoveries, and golf presentation.

Acceptance requires actual Unity pose/game captures and tests. No visual issue is PASS from code inspection alone. Record unresolved cases explicitly in proof/GATE_RESULTS.md.

Checklist: female wave and wrist orientation; tennis backhand elbow; FistPump/ Shock equipment clearance; all emote/point-reset transitions; skirt pushups/kneel/lunge; actual-contact VFX; serve wrist; Thrust timing; emote lengths; reposition feet; emote dust; golf face performance/cap shadow; immediate hole celebration; putt weight; follow-through shaft/neck; grip hands; address/kneel/pushup/run-walk blends; female idle arms; lead-foot pivot; stopped-ball wait; tee opponents idle; contextual reach micro animations.

Concurrent lighting work is reverting character lighting in another chat. Preserve its files and inspect resulting cap lighting in proof.

## Retained implementation

- Shared bone-local torso/head exclusion volumes and two-bone elbow correction, with wrist positions locked during sports contacts. This is an approximate kinematic constraint, not mesh collision or a zero-penetration guarantee.
- Racket exclusion during free emotes; waving wrist flexion limit; pre-contact serve wrist cock.
- Outgoing full-body emote pose retained through point-reset fades; golf pose capture bridges the 90-degree clip-coordinate change.
- Shared emote duration budgets and monotonic Thrust timing; short/wide/slice routing for existing reach clips.
- Impact presentation queued through physics substeps and flushed after the rendered rig; footstep particles suppressed outside rallies.
- Mouth/brow mood targets shared across both sports, neutral head geometry unchanged.
- Golf lead-toe pivot, putt load response, shaft-axis hand spacing, immediate holed-ball reaction, shorter routine result interval, voluntary emotes held until completion, more visible asynchronous gallery idles.

## Identity stop

The female shoulder/axilla defect persists in actual game renders in both sports. Three local weight trials and a torso/arm blending trial failed the silhouette gate. The expensive skirt projection trial also collapsed the layered skirt and took roughly 64–69 ms per sampled pose. None of these trials is installed. The repo's instruction “Stop for Adnan when identity/silhouette drifts” applies to those changes. Preserve the original body, garment meshes and bindings pending a reviewed source correction.

This pass does **not** satisfy the full user checklist. See proof/GATE_RESULTS.md for exact evidence and remaining failures.

## Female continuation

The later continuation supersedes the female shoulder stop above: the retained shoulder/wave correction preserves the exact neutral body and has actual game proof. Skirt candidates remain rejected. See [phase2 acceptance](phase2/proof/GATE_RESULTS.md) and [phase2 plan](phase2/PLAN.md). The original full checklist remains incomplete.
