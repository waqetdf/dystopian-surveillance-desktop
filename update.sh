#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ${1:-} == --test-root ]]; then
  test_root=${2:?Indica un directorio aislado}
  shift 2
  exec python3 tools/deploy.py install --root "$test_root" "$@"
fi
if [[ -n $(git status --porcelain) ]]; then
  echo 'El árbol tiene cambios locales. Confírmalos o consérvalos antes de actualizar.' >&2
  exit 1
fi
remote=$(git remote get-url origin)
case "$remote" in
  https://github.com/waqetdf/dystopian-surveillance-desktop.git|git@github.com:waqetdf/dystopian-surveillance-desktop.git) ;;
  *) echo "Origen no autorizado: $remote. Verifica y configura el repositorio oficial." >&2; exit 1;;
esac
git fetch origin main --tags
git fsck --no-reflogs
revision=$(git rev-parse origin/main)
git log --oneline HEAD.."$revision"
printf 'Revisión obtenida del origen verificado: %s\nSe conservarán configuración, historial y vídeos personales.\n' "$revision"
read -r -p '¿Instalar esta revisión? [s/N] ' answer
case "$answer" in s|S|si|sí|y|yes) ;; *) exit 0;; esac
git merge --ff-only "$revision"
./install.sh
if [[ -x "$HOME/.local/bin/dsd" ]]; then
  echo 'Actualización instalada. Aplica la nueva versión con ~/.local/bin/dsd restart.'
fi
