#!/bin/bash
# GPU rule: print compute apps with owners; exit 2 if a process owned by someone other than aurnab holds > 1024 MiB.
viol=0
echo "gpu_check $(date -Is)"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
while IFS=, read -r pid mem; do
  pid=$(echo "$pid" | xargs)
  mem=$(echo "$mem" | xargs | sed 's/ MiB//')
  [ -z "$pid" ] && continue
  user=$(ps -o user= -p "$pid" | xargs)
  echo "pid=$pid used_mib=$mem user=${user:-exited}"
  if [ -n "$user" ] && [ "$user" != "aurnab" ] && [ "$mem" -gt 1024 ]; then viol=1; fi
done < <(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader)
if [ $viol = 1 ]; then echo "GPU_RULE: VIOLATION (non-aurnab process > 1024 MiB) -> CPU only"; exit 2; fi
echo "GPU_RULE: OK"
