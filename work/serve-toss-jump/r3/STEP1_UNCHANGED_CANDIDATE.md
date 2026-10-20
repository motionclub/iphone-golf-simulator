# Step 1: unchanged candidate, current runtime input
Only the two-line Serve guard and step-creation condition were changed in the clone. Production runtime remains untouched.

male
G1 max: 67.323 -> 12.248 mm (remaining FAIL)
G2: 76.440 at 1.278853 -> 74.516 at 1.312903
G3 first clearance: {'L': 1.418728, 'R': 1.572265} -> {'L': 1.572265, 'R': 1.471547} (remaining FAIL)
G11 planted world drift: {'mm': 30.75833202564761, 'side': 'R', 'part': 'toe', 'frame': 112, 'clipTime': 0.150893} -> {'mm': 474.8240281409524, 'side': 'R', 'part': 'heel', 'frame': 382, 'clipTime': 1.530292} (FAIL)
Non-Serve completed replants 4 -> 4 (PASS: identical and >0)

female
G1 max: 67.066 -> 10.884 mm (remaining FAIL)
G2: 76.348 at 1.278853 -> 73.398 at 1.329928
G3 first clearance: {'L': 1.418728, 'R': 1.572265} -> {'L': 1.572265, 'R': 1.572265} (remaining FAIL)
G11 planted world drift: {'mm': 35.000892845753675, 'side': 'R', 'part': 'toe', 'frame': 113, 'clipTime': 0.151179} -> {'mm': 539.1235832385743, 'side': 'R', 'part': 'toe', 'frame': 382, 'clipTime': 1.530292} (FAIL)
Non-Serve completed replants 2 -> 2 (PASS: identical and >0)

The guard removes the procedural arc, but contact-assist lunges now expose reach-triggered unlocking and relocking: male right heel stays at its anchor through 1.453222, moves when reach exceeds the old limit at 1.510118, then relocks to the displaced pose at 1.530292. The initial toe pivot remains 31–35 mm. The pure graph replay inherits live hero transforms, so its absolute position is not treated as isolated clip drift. Next: center the entry and grounded stance, finish jump/contact/landing, then quantify residual toe pivot and extend grounded Serve locking only if needed.
