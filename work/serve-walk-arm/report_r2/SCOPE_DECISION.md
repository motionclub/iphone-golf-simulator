# Scope decision needed for G5

The current candidate is not installed. The strict Refeed boundary is still a failed gate.

Prompt 28b says: “If a needed fix lives outside your files, STOP that item and report exactly which file/line and why.” It also locks game timing and permits only the opponent serve-reach path in TennisGame.

At f767, the four player cases have raw wrist speeds of 4.3196–5.6065 m/s. Refeed enters PlayerServeHold at f768. A 3 cm step at 60 Hz permits at most 1.8 m/s; a speed change of at most 0.6 m/s requires at least 3.7196–5.0065 m/s. Both conditions cannot hold on that same first frame. The raw traces retain it and do not mark it exempt.

The earlier baseline-speed proposal is reviewable in PLAYER_DEPTH_SPEED_SCOPE_REQUEST.patch, but it is not sufficient for the first frame. Relevant locked paths are:

- TennisGame.cs:19 — Refeed immediately calls BeginPoint.
- TennisGame.cs:1872 / :1890 — BeginPoint resets the point and enters PlayerServeHold immediately.
- TennisGame.cs:1150 — player baseline return currently uses dt * 4f.
- HeroTennisDriver.cs:500 — the preceding Rally visual pose is outside carry/hold/toss-reach ownership.

The next implementation needs an explicit decision about a safe pre-entry transition and the player return speed, or a revision to the instantaneous-reset contract. A queued Refeed would change request-to-held latency even if normal serve phase constants and contact timing remained unchanged; that exception must be authorized. Broadly altering Rally off-hand motion also needs authorization and a wider visual regression check.

No preceding Rally frame was altered to make this proof pass, no fixture timing was moved, and no gate limit was widened. The candidate patch remains isolated. LEFTY_GAP.md and unsupported LH films remain separate from this decision.
