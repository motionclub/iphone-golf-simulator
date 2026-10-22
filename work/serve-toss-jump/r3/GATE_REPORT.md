Staged candidate — not installed. No commit.

The passing measurements below use the current production look/prefabs plus a frozen snapshot of the parallel 28b carry runtime. That runtime is not installed in production. With the exact current production runtime and this owned candidate in a private clone, male G7 fails at 51.128 mm (frame 110, clip 0.150439), and G9 wrist twist fails at 37.448° (frame 261, clip 0.325). The staged integration gives 22.028 mm and 12.397°. No production Serve asset or LockFeet hunk has been installed.

Female current-runtime check: entry 48.313 mm, wrist 12.925°.

| Gate | Result | Male | Female |
|---|---|---|---|
| G1 feet down | PASS | 0.629 mm | 0.580 mm |
| G2 load/toss knees | PASS | 71.891–73.992°; toss 32.949° | 71.524–73.220°; toss 33.858° |
| G3 takeoff | PASS | 1.594 s both feet | 1.594 s both feet |
| G4 air/contact knee | PASS | 12.326°; both clear | 12.253°; both clear |
| G5 apex | PASS | 1.762 s | 1.762 s |
| G6 landing | PASS | touch 1.878; settled 1.962 s | touch 1.878; settled 1.962 s |
| G7 entry, five phases | PASS in staged integration | 22.028 mm | 19.149 mm |
| G8 contact kept | PASS | 13.831 mm; elbow 172.796° | 10.684 mm; elbow 172.443° |
| G9 smooth | PASS in staged integration | 149.682 mm left; wrist 12.397° | 131.129 mm left; wrist 11.825° |
| G10 clearance | PASS | 0 new/increased pairs; extra −129 vertices | 0 new/increased pairs; extra −36 vertices |
| G11 foot drift | PASS | 3.985 mm | 3.887 mm |
| G12 times/input scope | PASS in tested snapshot | 0.20/0.70/1.3333334/1.70; length 2.5 | same; prefab unchanged by this task |
| G13 runtime scope | PASS | LockFeet only; replants 4→4 | LockFeet only; replants 2→2 |
| G14 proofs | PASS | 8 decoded live films | 8 decoded live films |
| G15 installed/tested | PENDING — not installed | Production rerun required | Production rerun required |
| G16 human EYE | PENDING | Adnan decides | Adnan decides |

The load peaks lie in 1.279–1.333 s. Both heroes land and squash inside Serve, which exits at 1.978 s. Right-hand peak steps before/contact/after are 114.237/221.184/118.223 mm (male), 111.970/125.727/116.115 mm (female); no follow-through reversals. Contact differences also pass on the final rendered pose: 10.369/10.051 mm. Entry and hand-speed checks include both actor-relative and world motion. The five ReadyIdle phases are 0.583333, 0.150000, 1.900000, 1.466667 and 1.016667 s. Authored entry head/hand centering errors are at most 0.024 mm.

Runtime change: the replant guard removes the procedural Serve step. The toe anchor and shared hip reach correction keep the authored grounded stance reachable through the walk-in turn; the jump releases the lock. Only LockFeet changes; the Serve crossfade stays 0.08 s. The saved hunk was generated against the current production file. Installation must regenerate/re-read it immediately beforehand.

Before/after on the unchanged original candidate:

| Hero | G1 before → minimal guard | G2 before → guard | G3 before → guard | G11 before → guard |
|---|---|---|---|---|
| Male | 67.323 → 12.248 mm | 76.440 → 74.516° | 1.419/1.572 → 1.572/1.472 s | 30.758 → 474.824 mm |
| Female | 67.066 → 10.884 mm | 76.348 → 73.398° | 1.419/1.572 → 1.572/1.572 s | 35.001 → 539.124 mm |

The minimal guard alone did not solve the unreachable walk-in anchors or toe drift. On the unchanged original clip, authored toe drift is below 0.003 mm, while live toe drift was 31–35 mm; that establishes a runtime cause. The final runtime control preserves non-Serve replants 4→4 and 2→2. The finished clips and final lock together give the G1/G11 values above.

Clip changes: sway-centered Ready entry, separate shallow toss and trophy load, grounded feet through the toss, extended contact, earlier front touch and landing squash, continuous tuck/follow-through, steady female palm during windup, forearm roll corrections preserving hand world orientation, female contact stretch, and measured wrist clearance corrections. Marker times, length, rig and other clips were not authored by this task.

Other chats updated the production prefabs during this work. Those changes were preserved and included in the final input snapshot; the tested prefab hashes match that snapshot, and the serve timing values stayed unchanged. This task did not write those prefabs or the parallel carry/runtime code.

Install remains conditional: the parallel owner must supply its approved production carry runtime; rerun every gate with those actual inputs, obtain Adnan’s EYE decision on the matching films, install only the four Serve files and the LockFeet hunk, then rerun every gate on production. If any gate fails, install nothing. Rollback originals remain in work/serve-toss-jump/rollback_r3/ with SHA256SUMS. A change to the tested runtime inputs requires renewed verification and matching review films.

Candidate file hashes:

```text
f055472cef5fa2a4d90b3650bef30381ef13cbb087156433f99cf6dcb152cd41  fbx/Female_Serve.fbx
3bc58e8f34842a989ab02b74645ca3650ade13ff7ae1e665c400f612b02ece4a  fbx/Female_Serve.fbx.meta
b126d4059f225586d0ddff8cb4bf3740c55c1b2cb3449d9cc36ba14033f41b1b  fbx/Male_Serve.fbx
7bd669f74775e9519c4c6bbdf443a4d498247874c6c7400e998b0f052be37474  fbx/Male_Serve.fbx.meta
```

[Film review](REVIEW.md) · [Labeled live keys](proof/live_serve_keys.jpg) · [Candidate archive](staged_candidate.zip) · [Hunk patch](LOCKFEET.patch) · [Measured gate evidence](gate_results_current.json)
