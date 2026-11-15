#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ ${1:-} == --test-root ]]; then
  test_root=${2:?Indica un directorio aislado}
  shift 2
  exec python3 tools/deploy.py install --root "$test_root" "$@"
fi
if (( EUID == 0 )); then
  echo 'Ejecuta como usuario normal. Solo pacman solicitará privilegios.' >&2
  exit 1
fi
source /etc/os-release
if [[ ${ID:-} != arch && " ${ID_LIKE:-} " != *" arch "* ]]; then
  echo 'Este instalador necesita Arch Linux o una derivada compatible con pacman.' >&2
  exit 1
fi
command -v pacman >/dev/null || { echo 'Falta pacman.' >&2; exit 1; }
if ! command -v Hyprland >/dev/null; then
  echo 'No se detecta Hyprland: se instalará junto con las dependencias.'
fi
packages=(curl hyprland quickshell qt6-declarative qt6-multimedia qt6-wayland qt6-svg ffmpeg python python-secretstorage gnome-keyring ttf-dejavu foot xdg-utils mpv htop)
missing=()
for package in "${packages[@]}"; do
  pacman -Q "$package" >/dev/null 2>&1 || missing+=("$package")
done
if (( ${#missing[@]} )); then
  echo "Dependencias oficiales: ${missing[*]}"
  echo 'Se hará una actualización completa para evitar actualizaciones parciales de Arch.'
  sudo pacman -Syu --needed "${packages[@]}"
fi
deployment_args=()
with_curated_media=0
for argument in "$@"; do
  if [[ "$argument" == --with-curated-media ]]; then with_curated_media=1; else deployment_args+=("$argument"); fi
done
python3 tools/deploy.py install "${deployment_args[@]}"
if (( with_curated_media )); then
  if ! python3 tools/fetch_media.py; then
    echo 'La selección opcional no se pudo descargar. La interfaz está instalada; elige vídeos locales desde Ajustes.' >&2
  fi
fi
python3 tools/doctor.py
echo 'Instalación comprobada. Activa el escritorio dentro de Hyprland con ~/.local/bin/dsd start.'
