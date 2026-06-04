#!/bin/bash
#
# run_radiance_extra.sh — Corre rfluxmtx + dctimestep para una rejilla
# distinta a la de validación, reutilizando el octree ya construido.
#
# Útil para análisis adicionales (UDI, confort temporal, DGPs) que requieren
# rejillas distintas a la 7×9 = 63 puntos del experimento.
#
# Uso:
#   bash scripts/run_radiance_extra.sh <variant> <points_file> <suffix>
#
# Argumentos:
#   variant      — calibrated, jun_optimal, nov_optimal, validation
#   points_file  — archivo de puntos en edificio/points/ (ej. points_480.txt)
#   suffix       — etiqueta para los archivos de salida (ej. 480, dgps)
#
# Salidas (relativo a edificio/):
#   matrices/dc/illum_<variant>_<suffix>.mtx
#   results/dc/annual_<variant>_<suffix>.ill
#
# Pre-requisitos:
#   - octrees/scene_<variant>.oct debe existir (corre run_radiance.sh primero)
#   - skyVectors/nelier_annual.smx debe existir
#

set -e

if [ $# -ne 3 ]; then
    echo "Uso: bash scripts/run_radiance_extra.sh <variant> <points_file> <suffix>" >&2
    echo "Ejemplo: bash scripts/run_radiance_extra.sh jun_optimal points_480.txt 480" >&2
    exit 1
fi

VARIANT="$1"
POINTS_FILE="$2"
SUFFIX="$3"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT/edificio"

OCT="octrees/scene_${VARIANT}.oct"
PTS="points/${POINTS_FILE}"
MTX="matrices/dc/illum_${VARIANT}_${SUFFIX}.mtx"
ILL="results/dc/annual_${VARIANT}_${SUFFIX}.ill"
SMX="skyVectors/nelier_annual.smx"

if [ ! -f "$OCT" ]; then
    echo "ERROR: $OCT no existe. Corre primero: bash scripts/run_radiance.sh $VARIANT" >&2
    exit 1
fi
if [ ! -f "$PTS" ]; then
    echo "ERROR: $PTS no existe." >&2
    exit 1
fi
if [ ! -f "$SMX" ]; then
    echo "ERROR: $SMX no existe. Corre primero: bash scripts/run_radiance.sh" >&2
    exit 1
fi

SENSORS=$(wc -l < "$PTS" | tr -d ' ')

echo "Variant: $VARIANT"
echo "Puntos:  $PTS ($SENSORS sensores)"
echo "Suffix:  $SUFFIX"
echo ""

# rfluxmtx (DC matrix)
if [ ! -f "$MTX" ] || [ "$OCT" -nt "$MTX" ] || [ "$PTS" -nt "$MTX" ]; then
    echo "[1/2] rfluxmtx -ab 5 -ad 10000 -lw 0.0001 -n 8 -y $SENSORS -> $MTX"
    rfluxmtx -faf -ab 5 -ad 10000 -lw 0.0001 -n 8 \
        -I+ -y "$SENSORS" \
        - skyDomes/skyglow.rad \
        -i "$OCT" \
        < "$PTS" \
        > "$MTX" 2>/dev/null
else
    echo "[1/2] skip rfluxmtx: $MTX ya existe"
fi

# dctimestep | rmtxop (annual illuminance)
if [ ! -f "$ILL" ] || [ "$MTX" -nt "$ILL" ] || [ "$SMX" -nt "$ILL" ]; then
    echo "[2/2] dctimestep | rmtxop -> $ILL"
    dctimestep "$MTX" "$SMX" \
        | rmtxop -fa -t -c 47.4 119.9 11.6 - \
        > "$ILL"
else
    echo "[2/2] skip annual: $ILL ya existe"
fi

echo ""
echo "OK: $ILL ($(wc -l < "$ILL") líneas)"
