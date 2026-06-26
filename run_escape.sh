#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/Users/kamrenkhan/Desktop/Research/RESTORE/Project"
ESCAPE_ROOT="${PROJECT_ROOT}/escape"
THALAMUS_ROOT="${PROJECT_ROOT}/Thalamus/source"
PYTHON="${PROJECT_ROOT}/venv-thalamus/bin/python"

cd "${ESCAPE_ROOT}"
export PYTHONPATH="${ESCAPE_ROOT}:${THALAMUS_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON}" -m thalamus.task_controller --ext escape_thalamus_ext "$@"

