#!/bin/bash
# heavy.sh — machine-wide gate for heavy jobs, so parallel chats stop freezing this
# 16 GB Mac. Every Unity and Blender launch from any chat must go through it.
#
#   heavy.sh unity   <command...>   # at most HEAVY_UNITY_SLOTS (default 2) Unity jobs at once
#   heavy.sh blender <command...>   # at most HEAVY_BLENDER_SLOTS (default 2) Blender jobs at once
#   heavy.sh status                 # who holds which slot, and who is waiting
#
# Any job that would run NEXT TO another heavy job also needs >=30 % free and swap < 7.5 GB.
# (10-17: 1 Unity + 2 Blender pushed swap to 12 GB and hit the out-of-memory pop-up.)
# The command waits (polling every 15 s) until a slot of its class is free AND the system
# has at least HEAVY_MIN_FREE_PCT (default 20) % memory free. Then it runs, holding the
# slot until it exits; a slot whose holder died is reclaimed automatically.
# A long-lived Editor (one you keep open and drive with the unity CLI) must also be
# started through here, and it holds its slot until you quit it, so quit it when done.
set -u
ROOT="${HEAVY_ROOT:-$HOME/.heavy-slots}"
mkdir -p "$ROOT"

swap_mb() { sysctl -n vm.swapusage | awk '{gsub("M","",$6); print int($6)}'; }
free_pct() { memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{gsub("%","",$2); print $2+0}'; }

status() {
  for d in "$ROOT"/*/; do
    [ -d "$d" ] || continue
    s=$(basename "$d"); pid=$(cat "$d/pid" 2>/dev/null)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo "$s  held by pid $pid since $(cat "$d/since" 2>/dev/null): $(cat "$d/cmd" 2>/dev/null)"
    else
      echo "$s  stale (holder gone), will be reclaimed"
    fi
  done
  ls "$ROOT"/waiting.* 2>/dev/null | while read -r w; do wp=${w##*.}; if kill -0 "$wp" 2>/dev/null; then echo "waiting: $(cat "$w" 2>/dev/null)"; else rm -f "$w"; fi; done
  echo "memory free: $(free_pct)%  swap used: $(swap_mb) MB"
}

[ "${1:-}" = status ] && { status; exit 0; }
class="${1:-}"; shift || true
case "$class" in
  unity)   slots="${HEAVY_UNITY_SLOTS:-2}" ;;
  blender) slots="${HEAVY_BLENDER_SLOTS:-1}" ;;
  *) echo "usage: heavy.sh unity|blender <command...> | status" >&2; exit 2 ;;
esac
[ $# -gt 0 ] || { echo "heavy.sh: no command given" >&2; exit 2; }

min_free="${HEAVY_MIN_FREE_PCT:-20}"
extra_free="${HEAVY_EXTRA_FREE_PCT:-28}"   # slots beyond the first need this much free memory
max_swap="${HEAVY_MAX_SWAP_MB:-11000}"       # ...and swap use below this (swap growth = thrashing)
waitfile="$ROOT/waiting.$$"
echo "$class: $*" > "$waitfile"
held=""
cleanup() { rm -f "$waitfile"; [ -n "$held" ] && rm -rf "$held"; }
trap cleanup EXIT
trap 'exit 130' INT TERM

announced=0
while :; do
  [ -f "$ROOT/limits" ] && . "$ROOT/limits"
  case "$class" in unity) slots="${HEAVY_UNITY_SLOTS:-$slots}";; blender) slots="${HEAVY_BLENDER_SLOTS:-$slots}";; esac
  max_swap="${HEAVY_MAX_SWAP_MB:-$max_swap}"; extra_free="${HEAVY_EXTRA_FREE_PCT:-$extra_free}"
  for i in $(seq 1 "$slots"); do
    d="$ROOT/$class-$i"
    if [ -d "$d" ]; then
      pid=$(cat "$d/pid" 2>/dev/null)
      if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then rm -rf "$d"; fi
    fi
    need=$min_free; ok_swap=1
    others=$(ls -d "$ROOT"/unity-* "$ROOT"/blender-* 2>/dev/null | wc -l | tr -d " ")
    if [ "$i" -gt 1 ] || [ "$others" -gt 0 ]; then need=$extra_free; [ "$(swap_mb)" -lt "$max_swap" ] || ok_swap=0; fi
    # first come, first served: only the oldest living waiter of this class may take a slot
    oldest=""; prio=""
    for w in $(ls -tr "$ROOT"/waiting.* 2>/dev/null); do wp=${w##*.}; kill -0 "$wp" 2>/dev/null || continue
      case "$(head -c 8 "$w")" in "$class:"*)
        [ -z "$oldest" ] && oldest=$wp
        # fast lane: the oldest waiter whose command matches HEAVY_PRIORITY_PATTERN goes first
        if [ -z "$prio" ] && [ -n "${HEAVY_PRIORITY_PATTERN:-}" ] && grep -qE "$HEAVY_PRIORITY_PATTERN" "$w"; then prio=$wp; fi;;
      esac; done
    [ -n "$prio" ] && oldest=$prio
    [ -n "$oldest" ] && [ "$oldest" != "$$" ] && continue
    # machine-wide cap (Adnan 10-18; 13:30 TEST: 3 total = 2 Unity + 1 Blender): at most HEAVY_TOTAL (default 2) heavy jobs of any kind at once
    [ "$others" -ge "${HEAVY_TOTAL:-3}" ] && continue
    # fairness: a class may take its 2nd slot only when nothing of the other class is waiting
    if [ "$i" -gt 1 ] && [ "$class" != unity ]; then
      starve=0; for w in "$ROOT"/waiting.*; do [ -e "$w" ] || continue; wp=${w##*.}; kill -0 "$wp" 2>/dev/null || continue
        case "$(head -c 8 "$w")" in "$class:"*) ;; *) starve=1; break;; esac; done
      [ $starve = 1 ] && continue
    fi
    if [ $ok_swap = 1 ] && [ "$(free_pct)" -ge "$need" ] && mkdir "$d" 2>/dev/null; then
      echo $$ > "$d/pid"; date "+%H:%M:%S" > "$d/since"; echo "$*" > "$d/cmd"
      held="$d"; break 2
    fi
  done
  if [ $announced = 0 ]; then
    echo "heavy.sh: waiting for a free $class slot / ${min_free}% free memory (see: heavy.sh status)" >&2
    announced=1
  fi
  sleep 15
done
rm -f "$waitfile"
# emergency brake (10-18): if the machine starts thrashing (swap > HEAVY_KILL_SWAP_MB and
# free < HEAVY_KILL_FREE_PCT), the most recently started heavy job stops itself.
"$@" &
child=$!
while kill -0 "$child" 2>/dev/null; do
  sleep 10
  [ -f "$ROOT/limits" ] && . "$ROOT/limits"   # brake thresholds are live too
  sw=$(swap_mb); fr=$(free_pct)
  if { [ "$sw" -gt "${HEAVY_KILL_SWAP_MB:-9000}" ] && [ "$fr" -lt "${HEAVY_KILL_FREE_PCT:-25}" ]; } || [ "$sw" -gt "${HEAVY_HARD_SWAP_MB:-12500}" ]; then
    newest=$(ls -td "$ROOT"/unity-* "$ROOT"/blender-* 2>/dev/null | head -1)
    if [ "$newest" = "$held" ]; then
      echo "heavy.sh: EMERGENCY BRAKE - machine thrashing (swap $(swap_mb) MB, free $(free_pct)%); stopping: $*" >&2
      echo "$(date +%H:%M:%S) braked: $*" >> "$ROOT/brake.log"
      pkill -TERM -P "$child" 2>/dev/null; kill -TERM "$child" 2>/dev/null; sleep 5
      pkill -KILL -P "$child" 2>/dev/null; kill -KILL "$child" 2>/dev/null
      wait "$child" 2>/dev/null; exit 137
    fi
  fi
done
wait "$child"
