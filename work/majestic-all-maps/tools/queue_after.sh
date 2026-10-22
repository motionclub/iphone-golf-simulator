#!/bin/bash
# after-runs (layer on): every player view of the given holes, then the budget of all holes. One heavy job at a time.
D=$(cd "$(dirname "$0")/.." && pwd); cd "$D"
MAM_WITH_LAYER=1 MAM_HOLES=${LOOK_HOLES:-7,8,9,12,15,13,10,21} tools/run_editor.sh MajesticHoleViews g1/views_r1
MAM_WITH_LAYER=1 MAM_CAMS=$D/audit/views_clear tools/run_editor.sh MajesticGolfBudget g0/budget_after_r1
