#!/usr/bin/env bash
set -euo pipefail
printf quit | nvidia-cuda-mps-control || true
