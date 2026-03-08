#!/bin/bash
#
# run_simulation_validation_calibrated_november.sh - November-optimized validation simulation
#
# This script runs the Two-Phase Method simulation with materials calibrated
# specifically for November 20 conditions (lower sun angle).
#
# Calibration adjustments (optimized for November 20):
#   - Glazing transmittance: 0.88 -> 0.70
#   - Floor reflectance: 0.30 -> 0.11
#   - Hallway reflectance: 0.36 -> 0.17
#
# Usage: bash run_simulation_validation_calibrated_november.sh
#

set -e  # Exit on error

# Change to script directory
cd "$(dirname "$0")"

echo "======================================================"
echo "Radiance Validation Simulation (CALIBRATED - NOVEMBER)"
echo "======================================================"
echo ""
echo "Calibration parameters (optimized for November 20):"
echo "  - Glazing transmittance: 0.70 (from 0.88)"
echo "  - Floor reflectance:     0.11 (from 0.30)"
echo "  - Hallway reflectance:   0.17 (from 0.36)"
echo ""

# ----------------------------------------------
# Step 1: Generate validation sensor grid
# ----------------------------------------------
echo "[Step 1/4] Generating validation sensor grid..."
uv run python generate_sensor_grid_validation.py

# Count sensors for rfluxmtx -y parameter
SENSOR_COUNT=$(wc -l < points_validation.txt | tr -d ' ')
echo "  Sensor count: $SENSOR_COUNT"
echo ""

# ----------------------------------------------
# Step 2: Build octree with November-calibrated materials
# ----------------------------------------------
echo "[Step 2/4] Building octree with November-calibrated materials..."
oconv materials_calibrated_november.rad scene.rad objects/scene.geom objects/glazing.geom > octrees/scene_calibrated_november.oct
echo "  Created: octrees/scene_calibrated_november.oct"
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
    -i octrees/scene_calibrated_november.oct \
    < points_validation.txt \
    > matrices/dc/illum_validation_calibrated_november.mtx

echo "  Created: matrices/dc/illum_validation_calibrated_november.mtx"
echo ""

# ----------------------------------------------
# Step 4: Multiply DC × sky matrix
# ----------------------------------------------
echo "[Step 4/4] Generating annual illuminance..."
dctimestep matrices/dc/illum_validation_calibrated_november.mtx skyVectors/nelier_annual.smx \
    | rmtxop -fa -t -c 47.4 119.9 11.6 - \
    > results/dc/annual_validation_calibrated_november.ill

echo "  Created: results/dc/annual_validation_calibrated_november.ill"
echo ""

echo "======================================================"
echo "November-calibrated validation simulation complete!"
echo "======================================================"
echo ""
echo "Results:"
echo "  - Octree:            octrees/scene_calibrated_november.oct"
echo "  - DC matrix:         matrices/dc/illum_validation_calibrated_november.mtx"
echo "  - Annual illuminance: results/dc/annual_validation_calibrated_november.ill"
echo ""
echo "Compare with:"
echo "  - Original:              results/dc/annual_validation.ill"
echo "  - Calibrated (Combined): results/dc/annual_validation_calibrated.ill"
echo ""
