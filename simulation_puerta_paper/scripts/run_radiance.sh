#!/bin/bash
#
# run_radiance.sh — Pipeline Radiance Two-Phase Method (idempotente)
#
# Ejecuta los pasos LENTOS de la simulación (~15-20 min con 8 cores):
#   1. Genera la rejilla de 63 sensores
#   2. Convierte EPW -> WEA y genera sky matrix anual (gendaymtx)
#   3. Para cada variante de materiales:
#        a) Construye octree (oconv)
#        b) Calcula DC matrix (rfluxmtx)
#        c) Genera iluminancia anual (dctimestep | rmtxop)
#
# Variantes:
#   - validation     (materiales originales, tau=0.88, rho_floor=0.30, rho_hall=0.36)
#   - calibrated     (combinado óptimo,      tau=0.76, rho_floor=0.21, rho_hall=0.29)
#   - jun_optimal    (óptimo junio,          tau=0.80, rho_floor=0.17, rho_hall=0.13)
#   - nov_optimal    (óptimo noviembre,      tau=0.70, rho_floor=0.11, rho_hall=0.17)
#
# Idempotencia: cada paso verifica si su salida ya existe y es más reciente que sus
# insumos. Para forzar regeneración total: borra edificio/{octrees,matrices,results}.
#
# Uso:
#   bash scripts/run_radiance.sh            # corre las 4 variantes
#   bash scripts/run_radiance.sh validation # corre solo una variante
#

set -e

# Posicionar en la raíz del folder (portable: NO usa rutas absolutas)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

VARIANTS=("${@:-validation calibrated jun_optimal nov_optimal}")
# (si no se pasa argumento, usa las 4; si se pasa una, usa esa)
if [ $# -eq 0 ]; then
    VARIANTS=(validation calibrated jun_optimal nov_optimal)
else
    VARIANTS=("$@")
fi

echo "=================================================="
echo "Radiance Two-Phase Method — pipeline"
echo "=================================================="
echo "ROOT:     $ROOT"
echo "Variants: ${VARIANTS[*]}"
echo ""

# --- Verificar binarios ---
for bin in oconv rfluxmtx dctimestep rmtxop gendaymtx epw2wea; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        echo "ERROR: '$bin' no está en PATH" >&2
        exit 1
    fi
done

# --- Asegurar carpetas regenerables ---
mkdir -p edificio/octrees edificio/matrices/dc edificio/results/dc edificio/skyVectors

# ====================================================
# Paso 1: Rejilla de sensores (rápido)
# ====================================================
echo "[1/3] Rejilla de sensores"
uv run python scripts/generate_sensor_grid.py
SENSORS=$(wc -l < edificio/points/points_validation.txt | tr -d ' ')
echo ""

# ====================================================
# Paso 2: Sky matrix (rápido, ~10 s)
# ====================================================
echo "[2/3] Sky matrix anual (gendaymtx -m 1)"
EPW=data/weather/nelier_26jun_20novCST.epw
WEA=data/weather/nelier.wea
SMX=edificio/skyVectors/nelier_annual.smx

if [ ! -f "$SMX" ] || [ "$EPW" -nt "$SMX" ]; then
    echo "  epw2wea ..."
    epw2wea "$EPW" "$WEA" > /dev/null
    # OJO: sin -O1. La salida default (-O0, radiancia visible) es la que asume
    # la conversión fotópica de rmtxop (-c 47.4 119.9 11.6 = 179 lm/W).
    # Con -O1 (radiancia solar total) la iluminancia saldría ~55-58% inflada.
    echo "  gendaymtx -m 1 ..."
    gendaymtx -m 1 "$WEA" > "$SMX" 2>/dev/null
    echo "  OK: $SMX"
else
    echo "  skip: $SMX ya existe (más reciente que el EPW)"
fi
echo ""

# ====================================================
# Paso 3: Por cada variante (lento, ~3-5 min/variante)
# ====================================================
echo "[3/3] Por variante: oconv -> rfluxmtx -> dctimestep | rmtxop"
echo ""

run_variant() {
    local variant="$1"
    local mat
    if [ "$variant" = "validation" ]; then
        mat="edificio/materials/materials.rad"
    else
        mat="edificio/materials/materials_${variant}.rad"
    fi
    local oct="edificio/octrees/scene_${variant}.oct"
    local mtx="edificio/matrices/dc/illum_${variant}.mtx"
    local ill="edificio/results/dc/annual_${variant}.ill"

    if [ ! -f "$mat" ]; then
        echo "  [$variant] ERROR: no existe $mat" >&2
        return 1
    fi

    echo "  --- variant: $variant ---"
    echo "  materials: $mat"

    # 3a. Octree
    if [ ! -f "$oct" ] || [ "$mat" -nt "$oct" ] \
        || [ edificio/scene.rad -nt "$oct" ] \
        || [ edificio/objects/scene.geom -nt "$oct" ] \
        || [ edificio/objects/glazing.geom -nt "$oct" ]; then
        echo "    [a] oconv -> $oct"
        ( cd edificio && \
          oconv "../$mat" scene.rad objects/scene.geom objects/glazing.geom \
              > "../$oct" )
    else
        echo "    [a] skip oconv: $oct ya existe"
    fi

    # 3b. DC matrix (lento, ~3-5 min)
    if [ ! -f "$mtx" ] || [ "$oct" -nt "$mtx" ]; then
        echo "    [b] rfluxmtx -ab 5 -ad 10000 -lw 0.0001 -n 8 -y $SENSORS -> $mtx"
        echo "        (lento, ~3-5 min con 8 cores)"
        ( cd edificio && \
          rfluxmtx -faf -ab 5 -ad 10000 -lw 0.0001 -n 8 \
              -I+ -y "$SENSORS" \
              - skyDomes/skyglow.rad \
              -i "../$oct" \
              < points/points_validation.txt \
              > "../$mtx" 2>/dev/null )
    else
        echo "    [b] skip rfluxmtx: $mtx ya existe"
    fi

    # 3c. Iluminancia anual
    if [ ! -f "$ill" ] || [ "$mtx" -nt "$ill" ] || [ "$SMX" -nt "$ill" ]; then
        echo "    [c] dctimestep | rmtxop -c 47.4 119.9 11.6 -> $ill"
        dctimestep "$mtx" "$SMX" \
            | rmtxop -fa -t -c 47.4 119.9 11.6 - \
            > "$ill"
    else
        echo "    [c] skip dctimestep: $ill ya existe"
    fi
    echo ""
}

for v in "${VARIANTS[@]}"; do
    run_variant "$v"
done

echo "=================================================="
echo "Pipeline Radiance completado."
echo "Ahora puedes correr: quarto render index.qmd"
echo "=================================================="
echo ""
echo "Artefactos generados:"
ls -la edificio/octrees/ edificio/matrices/dc/ edificio/results/dc/ edificio/skyVectors/
