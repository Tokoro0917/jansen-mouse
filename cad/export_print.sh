#!/usr/bin/env bash
# 3D プリント用の STL を cad/print/ に書き出す（docs/printing.md）。
#   ./export_print.sh          # FDM 用（穴を 0.2 mm 大きくする）
#   ./export_print.sh 0        # 光造形・レーザー加工用（穴は設計どおり）
#   ./export_print.sh 0.3      # 穴がきつかったら大きくする
set -euo pipefail
cd "$(dirname "$0")"
CLEAR="${1:-0.2}"
OUT=print
mkdir -p "$OUT"
# 部品名 : 1 台分の数
PARTS=(
  "bar_j:12" "bar_k:12" "bar_c:12" "bar_f:12" "tri_upper:12" "tri_foot:12"
  "web:10" "web_motor:2" "frame:8"
  "print_bridge:1" "print_motor_clamp:1" "print_sensor_holder:4"
  "layout:1"
)
for entry in "${PARTS[@]}"; do
  part="${entry%%:*}"; n="${entry##*:}"
  openscad --hardwarnings -q -D "PART=\"$part\"" -D "FDM_CLEAR=$CLEAR" -o "$OUT/$part.stl" parts.scad
  printf '%-22s x %2s\n' "$part.stl" "$n"
done
echo "書き出し先: $(pwd)/$OUT（穴の拡大 ${CLEAR} mm）。layout.stl は脚 1 本分の 6 部品を並べたもの"
