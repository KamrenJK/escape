#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/Users/kamrenkhan/Desktop/Research/RESTORE/Project"
ESCAPE_ROOT="${PROJECT_ROOT}/escape"
THALAMUS_ROOT="${PROJECT_ROOT}/Thalamus/source"
PYTHON="${PROJECT_ROOT}/venv-thalamus/bin/python"
SESSION_ID="${ESCAPE_SESSION_ID:-$(date +%Y%m%d_%H%M%S)_$$}"

cd "${ESCAPE_ROOT}"
mkdir -p "${ESCAPE_ROOT}/data/${SESSION_ID}"
export ESCAPE_SESSION_ID="${SESSION_ID}"
export ESCAPE_SESSION_DIR="${ESCAPE_ROOT}/data/${SESSION_ID}"
echo "Escape session: ${ESCAPE_SESSION_ID}"
echo "Data directory: ${ESCAPE_SESSION_DIR}"
export PYTHONPATH="${ESCAPE_ROOT}:${THALAMUS_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
"${PYTHON}" "${ESCAPE_ROOT}/scripts/ensure_thalamus_compat.py" "${THALAMUS_ROOT}"

if [[ "${ESCAPE_USE_NATIVE:-0}" == "1" ]]; then
  exec "${PYTHON}" -m thalamus.task_controller --ext escape_thalamus_ext "$@"
fi

exec "${PYTHON}" -m thalamus.task_controller -y --ext escape_thalamus_ext "$@"
