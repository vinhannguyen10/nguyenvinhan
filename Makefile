IMAGE ?= hpcq-gpu.sif
MPI_IMAGE ?= hpcq-mpi.sif
CUDAQ_IMAGE ?= hpcq-cudaq.sif
DEF ?= containers/apptainer-gpu-qiskit.def
OUT ?= results
DOCKER_IMAGE ?= hpcq-gpu:dev

.PHONY: test validate build build-mpi build-cudaq run-gpu run-suite run-cpu run-full-cpu run-full-apptainer run-ai run-quantum comparison collect-gpu collect-mpi collect-slurm docker-build docker-build-cpu docker-run sbom scan security summarize clean

test:
	PYTHONPATH=src python -m pytest

validate: test
	PYTHONPATH=src bash scripts/validate_project.sh

build:
	apptainer build $(IMAGE) $(DEF)

build-mpi:
	apptainer build $(MPI_IMAGE) containers/apptainer-hpc-mpi.def

build-cudaq:
	apptainer build $(CUDAQ_IMAGE) containers/apptainer-cudaq.def

run-gpu:
	apptainer exec --nv --bind $(PWD):/workspace --pwd /workspace $(IMAGE) python3 -m hpcq.gpu_check --output $(OUT)/gpu_check.json

run-suite:
	apptainer exec --nv --bind $(PWD):/workspace --pwd /workspace $(IMAGE) python3 -m hpcq.run_suite --output-dir $(OUT) --device gpu --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy

run-cpu:
	PYTHONPATH=src python -m hpcq.run_suite --output-dir $(OUT)/local_cpu --device cpu --matrix-size 512 --qiskit-qubits 8 --qiskit-depth 2 --no-gpu-check --include-qaoa

run-full-cpu:
	PYTHONPATH=src bash benchmarks/run_full_cpu.sh $(OUT)/full_cpu

run-full-apptainer:
	bash benchmarks/run_full_apptainer_gpu.sh $(IMAGE) $(OUT)/full_apptainer_gpu

run-ai:
	PYTHONPATH=src python -m hpcq.ai_train_bench --device auto --samples 2048 --epochs 1 --output $(OUT)/ai_tiny_cnn_train.json

run-quantum:
	PYTHONPATH=src python -m hpcq.quantum_suite --output-dir $(OUT)/quantum --device auto --no-pennylane

comparison:
	PYTHONPATH=src bash benchmarks/run_comparison_matrix.sh $(OUT)/comparison

collect-gpu:
	PYTHONPATH=src bash scripts/collect_gpu_evidence.sh $(OUT)/evidence/gpu $(IMAGE)

collect-mpi:
	PYTHONPATH=src bash scripts/collect_mpi_evidence.sh $(OUT)/evidence/mpi $(MPI_IMAGE)

collect-slurm:
	bash scripts/collect_slurm_evidence.sh $(OUT)/evidence/slurm

docker-build:
	docker build -t $(DOCKER_IMAGE) -f containers/Dockerfile.gpu .

docker-build-cpu:
	docker build -t hpcq-cpu:dev -f containers/Dockerfile.cpu .

docker-run:
	docker run --rm --gpus all -v $(PWD):/workspace -w /workspace $(DOCKER_IMAGE) python3 -m hpcq.run_suite --output-dir results/docker --device gpu --include-ai --include-cirq --include-qaoa --include-pennylane --include-energy

sbom:
	bash scripts/generate_sbom.sh . $(OUT)/sbom

scan:
	bash scripts/security_scan.sh . $(OUT)/security

security:
	bash scripts/collect_security_evidence.sh $(OUT)/security .

summarize:
	PYTHONPATH=src python -m hpcq.compare_results $(OUT) --csv $(OUT)/summary.csv --md $(OUT)/summary.md

clean:
	rm -rf results/*.json results/*.jsonl results/*.out results/*.err results/*/ .pytest_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
