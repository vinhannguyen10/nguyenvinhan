from hpcq.mpi_bench import run_mpi_microbench
from hpcq.nccl_bench import run_torch_distributed_nccl


def test_mpi_benchmark_function_has_stable_import_schema():
    assert callable(run_mpi_microbench)


def test_nccl_benchmark_function_has_stable_import_schema():
    assert callable(run_torch_distributed_nccl)
