#!/bin/bash
#
# render_dgps_views.sh — Genera 3 imágenes para una posición/momento DGPs:
#   1. Vista en perspectiva (rpict + tone mapping)
#   2. Falsecolor de luminancia (cd/m²)
#   3. Detección de fuentes de glare (fisheye + evalglare)
#
# Uso:
#   bash scripts/render_dgps_views.sh <variant> <X> <Y> <Z> <mm> <dd> <hh> <prefix>
#
# Ejemplo (peor posición F2C1 con jun_optimal, 8 de enero 8:00):
#   bash scripts/render_dgps_views.sh jun_optimal 2.45 -9.05 1.20 1 8 8 dgps_f2c1_jan08_8h
#
# Salidas en images/:
#   <prefix>_perspective.png
#   <prefix>_falsecolor.png
#   <prefix>_glare.png
#

set -e

if [ $# -ne 8 ]; then
    echo "Uso: bash scripts/render_dgps_views.sh <variant> <X> <Y> <Z> <mm> <dd> <hh> <prefix>" >&2
    exit 1
fi

VARIANT="$1"
VX="$2"
VY="$3"
VZ="$4"
MM="$5"
DD="$6"
HH="$7"
PREFIX="$8"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT/edificio"

OCT="octrees/scene_${VARIANT}.oct"
IMG_DIR="$ROOT/images"
TMP=$(mktemp -d)
trap "rm -rf $TMP" EXIT

if [ ! -f "$OCT" ]; then
    echo "ERROR: $OCT no existe. Corre primero: bash scripts/run_radiance.sh $VARIANT" >&2
    exit 1
fi

mkdir -p "$IMG_DIR"

echo "Posición: ($VX, $VY, $VZ)  →  mira a +X (pizarrón)"
echo "Fecha:    2024-${MM}-${DD} ${HH}:00 hora local"
echo "Variante: $VARIANT"
echo ""

# ----------------------------------------------------------
# 1. Generar cielo CIE para ese momento (Temixco: 18.85N, 99.14W, m=90 = CST)
# ----------------------------------------------------------
echo "[1/5] Generando cielo CIE para ${MM}/${DD} ${HH}:00 ..."
# gensky: month, day, hour van PRIMERO, luego opciones. +s = cielo soleado con sol explícito.
gensky "$MM" "$DD" "$HH" -a 18.85 -o 99.14 -m 90 +s > "$TMP/sky.rad"

cat >> "$TMP/sky.rad" <<EOF

skyfunc glow sky_glow
0
0
4 1 1 1 0

sky_glow source sky_dome
0
0
4 0 0 1 180

skyfunc glow ground_glow
0
0
4 1 1 1 0

ground_glow source ground
0
0
4 0 0 -1 180
EOF

# ----------------------------------------------------------
# 2. Componer octree con cielo
# ----------------------------------------------------------
echo "[2/5] Componiendo octree con cielo..."
oconv -i "$OCT" "$TMP/sky.rad" > "$TMP/render.oct"

# ----------------------------------------------------------
# 3. Render perspectiva (FOV ~ 90°x70° hacia +X)
# ----------------------------------------------------------
echo "[3/5] Render perspectiva (rpict, ~1-2 min)..."
rpict -vtv \
      -vp $VX $VY $VZ \
      -vd 1 0 0 \
      -vu 0 0 1 \
      -vh 90 -vv 70 \
      -x 1024 -y 768 \
      -ab 3 -ad 1024 -as 256 -aa 0.1 \
      -t 30 \
      "$TMP/render.oct" > "$TMP/perspective.hdr" 2>/dev/null

# Tone mapping para PNG normal
echo "[3b/5] Tone mapping perspectiva..."
pcond -h+ "$TMP/perspective.hdr" | pfilt -1 -e 1 | ra_bmp > "$TMP/perspective.bmp"

# ----------------------------------------------------------
# 4. Falsecolor de luminancia (cd/m²)
# ----------------------------------------------------------
echo "[4/5] Falsecolor (luminancia cd/m²)..."
falsecolor -i "$TMP/perspective.hdr" -s 5000 -log 3 -l "cd/m²" -n 8 \
    > "$TMP/falsecolor.hdr"
ra_bmp "$TMP/falsecolor.hdr" "$TMP/falsecolor.bmp"

# ----------------------------------------------------------
# 5. Render fisheye + evalglare para detectar fuentes de glare
# ----------------------------------------------------------
echo "[5/5] Render fisheye 180° + evalglare..."
rpict -vta \
      -vp $VX $VY $VZ \
      -vd 1 0 0 \
      -vu 0 0 1 \
      -vh 180 -vv 180 \
      -x 800 -y 800 \
      -ab 3 -ad 1024 -as 256 -aa 0.1 \
      -t 30 \
      "$TMP/render.oct" > "$TMP/fisheye.hdr" 2>/dev/null

# evalglare: -d para detectar fuentes, -c <out.hdr> para imagen anotada
evalglare -d -c "$TMP/glare.hdr" "$TMP/fisheye.hdr" > "$TMP/glare_metrics.txt" 2>&1 || \
    cp "$TMP/fisheye.hdr" "$TMP/glare.hdr"

ra_bmp "$TMP/glare.hdr" "$TMP/glare.bmp"

# ----------------------------------------------------------
# Convertir BMP -> PNG con PIL
# ----------------------------------------------------------
echo "Convirtiendo a PNG..."
uv run python << PYEOF
from PIL import Image
import os
tmp = "$TMP"
out = "$IMG_DIR"
prefix = "$PREFIX"
for src, suffix in [
    ("perspective.bmp", "_perspective"),
    ("falsecolor.bmp",  "_falsecolor"),
    ("glare.bmp",       "_glare"),
]:
    src_path = os.path.join(tmp, src)
    if os.path.exists(src_path):
        img = Image.open(src_path)
        out_path = os.path.join(out, f"{prefix}{suffix}.png")
        img.save(out_path, "PNG")
        print(f"  OK: images/{prefix}{suffix}.png")
PYEOF

# Reportar métricas evalglare
if [ -f "$TMP/glare_metrics.txt" ]; then
    echo ""
    echo "--- evalglare métricas ---"
    grep -E "^(dgp|dgi|ugr|cgi|vcp|Lavg|Eveye)" "$TMP/glare_metrics.txt" 2>/dev/null | head -10 || true
fi

echo ""
echo "OK: 3 PNGs en $IMG_DIR/"
