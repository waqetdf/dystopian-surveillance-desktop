#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ${1:-} == --test-root ]]; then
  test_root=${2:?Indica un directorio aislado}
  shift 2
  exec python3 tools/deploy.py uninstall --root "$test_root" "$@"
fi
if (( EUID == 0 )); then echo 'Ejecuta como usuario normal.' >&2; exit 1; fi
if [[ -x "$HOME/.local/bin/dsd" ]]; then "$HOME/.local/bin/dsd" stop || true; fi
exec python3 tools/deploy.py uninstall "$@"
