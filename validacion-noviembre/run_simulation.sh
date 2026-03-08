#!/bin/bash
#
# run_simulation.sh - November validation simulation (combined calibration)
#
# This script runs the Two-Phase Method simulation with calibrated materials
# for the 63-point validation sensor grid (matching luxmeter measurement positions).
#
# Calibration parameters (combined optimal from 3-parameter grid search):
#   - Glazing transmittance: 0.88 -> 0.76 (accounts for frame obstruction + dirt)
#   - Floor reflectance: 0.30 -> 0.21 (accounts for desk/furniture coverage)
#   - Hallway reflectance: 0.36 -> 0.29 (accounts for hallway furniture/equipment)
#
# Usage: bash run_simulation.sh
#

set -e  # Exit on error

# Change to script directory
cd "$(dirname "$0")"

echo "=============================================="
echo "Radiance Validation Simulation - November"
echo "(Combined Calibration)"
echo "=============================================="
echo ""
echo "Calibration parameters:"
echo "  - Glazing transmittance: 0.76 (from 0.88)"
echo "  - Floor reflectance:     0.21 (from 0.30)"
echo "  - Hallway reflectance:   0.29 (from 0.36)"
echo ""

# ----------------------------------------------
# Step 1: Generate validation sensor grid
# ----------------------------------------------
echo "[Step 1/4] Generating validation sensor grid..."
uv run python generate_sensor_grid.py

# Count sensors for rfluxmtx -y parameter
SENSOR_COUNT=$(wc -l < points_validation.txt | tr -d ' ')
echo "  Sensor count: $SENSOR_COUNT"
echo ""

# ----------------------------------------------
# Step 2: Build octree with calibrated materials
# ----------------------------------------------
echo "[Step 2/4] Building octree with calibrated materials..."
oconv materials.rad scene.rad objects/scene.geom objects/glazing.geom > octrees/scene.oct
echo "  Created: octrees/scene.oct"
echo ""

# ----------------------------------------------
# Step 3: Calculate daylight coefficients
# ----------------------------------------------
echo "[Step 3/4] Calculating daylight coefficients..."
echo "  This may take a few minutes..."
echo "  Parameters: -ab 5 -ad 10000 -lw 0.0001"

rfluxmtx -v -faf -ab 5 -ad 10000 -lw 0.0001 -n 8 \
    -I+ -y "$SENSOR_COUNT" \
    - skyDomes/skyglow.rad \
    -i octrees/scene.oct \
    < points_validation.txt \
    > matrices/dc/illum.mtx

echo "  Created: matrices/dc/illum.mtx"
echo ""

# ----------------------------------------------
# Step 4: Multiply DC x sky matrix
# ----------------------------------------------
echo "[Step 4/4] Generating annual illuminance..."
dctimestep matrices/dc/illum.mtx skyVectors/nelier_annual.smx \
    | rmtxop -fa -t -c 47.4 119.9 11.6 - \
    > results/dc/annual.ill

echo "  Created: results/dc/annual.ill"
echo ""

echo "=============================================="
echo "Simulation complete!"
echo "=============================================="
echo ""
echo "Results:"
echo "  - Octree:             octrees/scene.oct"
echo "  - DC matrix:          matrices/dc/illum.mtx"
echo "  - Annual illuminance: results/dc/annual.ill"
echo ""
echo "Next steps:"
echo "  uv run python visualize_hourly_grid.py --date 2024-11-20 --output nov20.png"
echo "  uv run python create_room_scheme.py"
echo ""
