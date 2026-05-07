#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-results/evidence/slurm}
mkdir -p "$OUT"

if ! command -v sbatch >/dev/null 2>&1; then
  echo "Slurm sbatch is not available on this machine." | tee "$OUT/slurm_unavailable.txt"
  exit 0
fi

submit_and_record() {
  local label="$1"
  local script="$2"
  local submit_log="$OUT/${label}_submit.txt"
  echo "Submitting $script" | tee "$submit_log"
  local response
  response=$(sbatch "$script" | tee -a "$submit_log")
  local jobid
  jobid=$(echo "$response" | awk '{print $NF}')
  echo "$jobid" > "$OUT/${label}_jobid.txt"
  echo "Submitted $label as job $jobid"
  scontrol show job "$jobid" > "$OUT/${label}_scontrol_show_job.txt" 2>&1 || true
}

submit_and_record gpu_full slurm/run_full_suite_gpu.sbatch
submit_and_record mpi slurm/run_mpi_bench.sbatch
submit_and_record nccl slurm/run_nccl_torchrun.sbatch
submit_and_record quantum slurm/run_quantum_suite.sbatch

cat > "$OUT/after_jobs_finish_collect_accounting.txt" <<'EOF'
After the jobs finish, run examples like:
  sacct -j $(cat results/evidence/slurm/gpu_full_jobid.txt) --format=JobID,JobName,Partition,AllocCPUS,Elapsed,State,ExitCode,MaxRSS,MaxVMSize
  cp slurm-<JOBID>.out results/evidence/slurm/<label>_slurm.out
EOF
