#!/bin/zsh
# GARMENT PIPELINE: run a list of jobs one after another, skipping finished ones (each job resumes from its own checkpoints).
# The machine has restarted several times mid-run; after a restart just run this again:  nohup ./queue.sh jobs.txt > logs/queue.log 2>&1 &
# jobs.txt: one shell command per line; a job is done when its line appears in logs/queue.done.
cd ${0:A:h}; mkdir -p logs; touch logs/queue.done
while IFS= read -r job; do
  [[ -z $job || $job == \#* ]] && continue
  grep -qxF -- "$job" logs/queue.done && continue
  echo "[$(date +%H:%M:%S)] START $job"
  if eval "$job"; then echo "$job" >> logs/queue.done; echo "[$(date +%H:%M:%S)] DONE"; else echo "[$(date +%H:%M:%S)] FAIL $job"; fi
done < ${1:-jobs.txt}
