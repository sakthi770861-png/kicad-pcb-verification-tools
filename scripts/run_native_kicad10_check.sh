#!/usr/bin/env bash
# Run on the user's own machine, with KiCad 10 installed and real source files.
set -euo pipefail
if (( $# != 3 )); then
  echo "Usage: $0 <schematic.kicad_sch> <board.kicad_pcb> <output_directory>" >&2
  exit 2
fi
sch="$1"; pcb="$2"; out="$3"
command -v kicad-cli >/dev/null || { echo "Missing kicad-cli" >&2; exit 2; }
version="$(kicad-cli version)"
case "$version" in 10.*) ;; *) echo "Requires KiCad 10, found: $version" >&2; exit 2 ;; esac
[[ -f "$sch" && -f "$pcb" ]] || { echo "Schematic/PCB input missing" >&2; exit 2; }
mkdir -p "$out"
printf '%s\n' "$version" > "$out/kicad-version.txt"
set +e
kicad-cli sch erc --format json --severity-all --exit-code-violations --output "$out/erc.json" "$sch"
erc_status=$?
kicad-cli pcb drc --format json --severity-all --schematic-parity --exit-code-violations --output "$out/drc.json" "$pcb"
drc_status=$?
set -e
printf 'KiCad version: %s\nERC exit: %s\nDRC exit: %s\n' "$version" "$erc_status" "$drc_status" | tee "$out/cli-status.txt"
[[ -s "$out/erc.json" && -s "$out/drc.json" ]] || exit 1
[[ "$erc_status" == 0 && "$drc_status" == 0 ]] || exit 1
echo 'Native KiCad 10 produced clean reports. Engineering review still required.'