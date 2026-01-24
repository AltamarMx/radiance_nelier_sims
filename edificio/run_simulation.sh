#!/bin/bash
#
# run_simulation.sh - Complete Radiance annual daylighting simulation workflow
#
# This script runs the full Two-Phase Method simulation:
# 1. Generate sensor grid
# 2. Build octree from geometry
# 3. Calculate daylight coefficients (DC matrix)
# 4. Multiply DC matrix × sky matrix to get annual illuminance
# 5. Generate visualization images
#
# Usage: bash run_simulation.sh
#

set -e  # Exit on error

# Change to script directory
cd "$(dirname "$0")"

echo "=============================================="
echo "Radiance Annual Daylighting Simulation"
echo "=============================================="
echo ""

# ----------------------------------------------
# Step 1: Generate sensor grid
# ----------------------------------------------
echo "[Step 1/5] Generating sensor grid..."
uv run python generate_sensor_grid.py

# Count sensors for rfluxmtx -y parameter
SENSOR_COUNT=$(wc -l < points.txt | tr -d ' ')
echo "  Sensor count: $SENSOR_COUNT"
echo ""

# ----------------------------------------------
# Step 2: Build octree
# ----------------------------------------------
echo "[Step 2/5] Building octree..."
oconv materials.rad scene.rad objects/scene.geom objects/glazing.geom > octrees/scene.oct
echo "  Created: octrees/scene.oct"
echo ""

# ----------------------------------------------
# Step 3: Calculate daylight coefficients
# ----------------------------------------------
echo "[Step 3/5] Calculating daylight coefficients..."
echo "  This may take 10-30 minutes depending on CPU..."
echo "  Parameters: -ab 5 -ad 10000 -lw 0.0001"

rfluxmtx -v -faf -ab 5 -ad 10000 -lw 0.0001 -n 8 \
    -I+ -y "$SENSOR_COUNT" \
    - skyDomes/skyglow.rad \
    -i octrees/scene.oct \
    < points.txt \
    > matrices/dc/illum.mtx

echo "  Created: matrices/dc/illum.mtx"
echo ""

# ----------------------------------------------
# Step 4: Multiply DC × sky matrix
# ----------------------------------------------
echo "[Step 4/5] Generating annual illuminance..."
dctimestep matrices/dc/illum.mtx skyVectors/nelier_annual.smx \
    | rmtxop -fa -t -c 47.4 119.9 11.6 - \
    > results/dc/annual.ill

echo "  Created: results/dc/annual.ill"
echo ""

# ----------------------------------------------
# Step 5: Generate visualization images
# ----------------------------------------------
echo "[Step 5/5] Generating visualization images..."
mkdir -p images

# # Summer solstice (June 21)
# echo "  Generating summer solstice images..."
# for hour in 09 10 11 12 13 14 15 16 17; do
#     uv run python visualize_illuminance.py --date 2024-06-21 --time ${hour}:00 --output jun21_${hour}h.png
# done

# June 26 (weather file reference date)
echo "  Generating June 26 images..."
for hour in 09 10 11 12 13 14 15 16 17; do
    uv run python visualize_illuminance.py --date 2024-06-26 --time ${hour}:00 --output jun26_${hour}h.png
done

# November 20 (weather file reference date)
echo "  Generating November 20 images..."
for hour in 09 10 11 12 13 14 15 16 17; do
    uv run python visualize_illuminance.py --date 2024-11-20 --time ${hour}:00 --output nov20_${hour}h.png
done

# # Winter solstice (December 21)
# echo "  Generating winter solstice images..."
# for hour in 09 10 11 12 13 14 15 16 17; do
#     uv run python visualize_illuminance.py --date 2024-12-21 --time ${hour}:00 --output dec21_${hour}h.png
# done

# # Equinoxes at noon
# echo "  Generating equinox images..."
# uv run python visualize_illuminance.py --date 2024-03-20 --time 12:00 --output mar20_12h.png
# uv run python visualize_illuminance.py --date 2024-09-22 --time 12:00 --output sep22_12h.png

echo ""
echo "=============================================="
echo "Simulation complete!"
echo "=============================================="
echo ""
echo "Results:"
echo "  - Annual illuminance: results/dc/annual.ill"
echo "  - Visualizations: images/*.png"
echo ""
ls -la images/*.png 2>/dev/null | head -5
echo "  ... and $(ls images/*.png 2>/dev/null | wc -l | tr -d ' ') total images"
