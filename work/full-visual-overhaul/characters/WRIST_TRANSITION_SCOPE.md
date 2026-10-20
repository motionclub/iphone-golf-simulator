# Wrist transition source scope and provenance

The human user explicitly requested “also animation changes and skeleton changes” and
“an entire full overhaul, of literally everything visually,” then instructed “proceed
with full implementation.” This includes fixing hand and wrist geometry/deformation.

The +35 mm hand-local cut in diagnostics/rebuild_hands.py and rebuild_hands_v3.py was
an agent implementation technique used to isolate original wrist skinning after prior
rebuild artifacts. It is not in AGENTS.md, the user request, or a skill. AGENTS.md locks
base character identity/plates; its earlier clothing/rig deferral was expressly expanded
by the current user request. No user instruction fixes a cut at +35 mm.

The parent’s current implementation scope says: “Original wrist exact constraints need
not preserve malformed hand envelope—named rig/contact positions preserve, forearm
exterior outside wrist transition preserve; can redistribute Skin normals/weights and
source inside hand/wrist transition if actual continuity verified.” This is a technical
interpretation within the existing full-overhaul authorization, not new human approval.

Proposed source experiment retains the forearm exterior below hand-local −25 mm,
including its exact cut-ring coordinates and four bone influences, and rebuilds only
hand/wrist geometry beyond that transition. All head/body outside the local hand region,
53/54 bone names/parents, source physics contacts, and authoritative base_lock files stay
unchanged. The editable candidate is a separate Premium_*_ContinuousHandsV3.blend and
scratch FBXs; no live Unity asset will be installed without actual rendered review.
The experiment is reversible and its touched region will be measured against the old source.
