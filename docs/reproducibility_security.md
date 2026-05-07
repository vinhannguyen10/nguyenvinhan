# Reproducibility and security checklist

## Reproducibility

- Store `Dockerfile` and Apptainer `.def` files in version control.
- Save the exact image digest when pulling base images.
- Save `python -m pip freeze` output from inside the final image.
- Save Slurm scripts used for each experiment.
- Save JSON/JSONL result files and summarize them with `hpcq.compare_results`.

## SBOM

Preferred:

```bash
bash scripts/generate_sbom.sh . results/sbom
```

If `syft` is installed, this creates an SPDX JSON SBOM. If not, the script creates fallback manifests.

## Security scanning

Preferred:

```bash
bash scripts/security_scan.sh . results/security
```

Use Trivy or Grype for real vulnerability reports. If neither tool exists, the script writes a clear `SCAN_NOT_RUN.txt` marker.
