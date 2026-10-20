# Golf motion and per-shot Ready — 2026-10-06

GATE: Ready is required for every shot and captures a fresh grip — PASS.
GATE: Driver/iron/putter configuration retains the native grip mode — PASS.
GATE: Three practice swings learn comfortable range and speed without spending shots — PASS.
GATE: Practice swings also require Ready and control switching cancels practice state — PASS.
GATE: Checked swings cancel without launching a ball — PASS.
GATE: Motion impact launches without a second animated downswing delay — PASS.
GATE: Swift controller build and UI state tests — PASS.
GATE: Controller screenshots reviewed — PASS (proof/controller-0.png through controller-3.png).

Validation: 48 Unity EditMode tests, 1 gameplay test covering repeated shots with distinct grips,
club changes, calibration and impact timing, and 3 Swift controller tests passed.
Unity evidence: EditMode.xml and PlayMode.xml. Swift evidence: native-tests-final.log and NativeDerived/Logs/Test/.
Three existing legacy test files reference removed character APIs and prevent the unfiltered Unity test assembly
from compiling. They were temporarily isolated for these focused runs, then restored with their metadata.
The full legacy suite is not certified by these runs.

Physical iPhone/AirPlay feel has not been measured. No new phone build was exported or installed.
Screen transport delay remains separate from the eliminated post-detection animation wait.
