# Radiance Annual Daylighting Simulation - Usage Guide

## Project Overview

Completed annual daylighting simulation for a building exported from DesignBuilder. The simulation uses the Radiance Two-Phase Method (daylight coefficients) for annual calculations.

**Location**: Temixco, Mexico (18.85°N, 99.14°W)

## Project Structure

```
edificio/
├── materials.rad              # Material definitions
├── scene.rad                  # Scene description
├── points.txt                 # Sensor grid (480 points)
├── points_validation.txt      # Validation sensor grid (63 points)
├── run_simulation.sh          # Full simulation workflow script
├── run_simulation_validation.sh  # Validation grid simulation script
├── generate_sensor_grid.py    # Sensor grid generator
├── generate_sensor_grid_validation.py  # Validation grid generator
├── visualize_illuminance.py   # Single-time visualization script
├── visualize_hourly_grid_validation.py # Hourly multi-panel visualization
├── create_room_scheme_validation.py    # Room scheme diagram generator
├── images/                    # Output visualizations (*.png)
├── objects/
│   ├── scene.geom            # Building geometry
│   ├── glazing.geom          # Window geometry
│   └── *.blindgrp            # Blind group definitions
├── skyDomes/
│   └── skyglow.rad           # Sky/ground hemisphere for rfluxmtx
├── skyVectors/
│   └── nelier_annual.smx     # Annual sky matrix (8760 × 146)
├── matrices/dc/
│   ├── illum.mtx             # Daylight coefficient matrix (480 × 146)
│   └── illum_validation.mtx  # Validation DC matrix (63 × 146)
├── octrees/
│   └── scene.oct             # Compiled octree
├── results/dc/
│   ├── annual.ill            # Annual illuminance (8760 × 480)
│   └── annual_validation.ill # Validation annual illuminance (8760 × 63)
└── assets/
    ├── nelier_26jun_20novCST.epw  # Weather file
    └── nelier.wea                  # Converted WEA format
```

## Simulation Parameters

| Parameter | Value |
|-----------|-------|
| Sensor count | 480 points (20×24 grid) |
| Grid spacing | ~0.405m |
| Work plane height | 0.75m |
| Room dimensions | 7.66m × 9.37m |
| Temporal resolution | Hourly (8760 timesteps) |
| Sky patches | 146 (Reinhart m=1) |

## Usage

### Run Full Simulation

```bash
cd edificio
bash run_simulation.sh
```

This script runs all steps:
1. Generate sensor grid (points.txt)
2. Build octree (scene.oct)
3. Calculate daylight coefficients (illum.mtx)
4. Generate annual illuminance (annual.ill)
5. Create visualization images in images/

### Visualize Single Datetime

```bash
cd edificio
uv run python visualize_illuminance.py --date 2024-06-21 --time 12:00 --output summer_noon.png
```

Output files are saved to `images/` folder.

### Generated Visualizations

Images in `edificio/images/`:
- `jun21_*.png` - Summer solstice hourly (9h-17h)
- `dec21_*.png` - Winter solstice hourly (9h-17h)
- `mar20_12h.png` - Spring equinox noon
- `sep22_12h.png` - Fall equinox noon

---

## Re-running the Simulation

### Quick Method (Recommended)

For any changes (sensors, geometry, materials), simply re-run the full script:

```bash
cd edificio
bash run_simulation.sh
```

### If Only Sensor Grid Changes

Edit `generate_sensor_grid.py` to change spacing, coverage, or work plane height, then run the script.

### If Weather File Changes

1. **Convert EPW to WEA format:**
   ```bash
   epw2wea assets/new_weather.epw assets/nelier.wea
   ```

2. **Generate new sky matrix:**
   ```bash
   gendaymtx -m 1 -O1 assets/nelier.wea > skyVectors/nelier_annual.smx
   ```

3. **Run simulation:**
   ```bash
   bash run_simulation.sh
   ```

### Manual Steps (Reference)

If you need to run individual steps:

```bash
# 1. Generate sensors
uv run python generate_sensor_grid.py

# 2. Build octree
oconv materials.rad scene.rad objects/scene.geom objects/glazing.geom > octrees/scene.oct

# 3. Calculate daylight coefficients (slow, ~10-30 min)
SENSORS=$(wc -l < points.txt)
rfluxmtx -v -faf -ab 5 -ad 10000 -lw 0.0001 -n 8 \
    -I+ -y $SENSORS \
    - skyDomes/skyglow.rad \
    -i octrees/scene.oct \
    < points.txt > matrices/dc/illum.mtx

# 4. Multiply DC × sky matrix
dctimestep matrices/dc/illum.mtx skyVectors/nelier_annual.smx \
    | rmtxop -fa -t -c 47.4 119.9 11.6 - \
    > results/dc/annual.ill
```

---

## Simulation Parameters Reference

### rfluxmtx (Daylight Coefficients)

| Flag | Value | Description |
|------|-------|-------------|
| `-ab` | 5 | Ambient bounces |
| `-ad` | 10000 | Ambient divisions |
| `-lw` | 0.0001 | Light weight cutoff |
| `-n` | 16 | CPU threads |
| `-I+` | - | Irradiance calculation |
| `-y` | 480 | Number of sensor points |

### gendaymtx (Sky Matrix)

| Flag | Value | Description |
|------|-------|-------------|
| `-m` | 1 | Reinhart subdivision (146 patches) |
| `-O1` | - | Output sun + sky (no solar only) |

### rmtxop (RGB to Illuminance)

Coefficients `-c 47.4 119.9 11.6` convert RGB irradiance to photopic illuminance (lux).

---

## Data Access

### Reading Illuminance Data

```python
import numpy as np

# Load annual data (skip header lines)
data = np.loadtxt('edificio/results/dc/annual.ill', skiprows=11)
# Shape: (8760, 480) - hours × sensors

# Get illuminance for June 21, noon (hour 4380)
hour = 4380
lux_values = data[hour, :]

# Load sensor positions
sensors = np.loadtxt('edificio/points.txt')
x, y, z = sensors[:, 0], sensors[:, 1], sensors[:, 2]
```

---

## Interpreting Visualizations

### Orientation

**North faces LEFT (←)** in all visualizations. The room is rotated 90° counter-clockwise from original coordinates.

```
        North ←
    ┌───────────────┐
    │               │
    │   MAIN ROOM   │  → South
    │  7.66 × 9.37m │
    │               │
    └───────────────┘
```

- Left edge = North wall (windows)
- Right edge = South wall (windows)

### Contour Levels

Visualizations use discrete illuminance levels:

```
[0, 299, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000] lux
```

### Illuminance Level Interpretation

| Level (lux) | Meaning | Application |
|-------------|---------|-------------|
| 0-299 | Insufficient | Below work standard |
| 300-499 | Minimum | Corridors, minimal tasks |
| 500-999 | Good | General office work |
| 1000-1499 | Very good | Detailed work |
| 1500-1999 | Excellent | Technical drawing |
| 2000-2999 | Very bright | Near windows |
| 3000-5000 | Potential glare | Direct sun zones |
| 5000+ | High glare risk | May need shading |

### Colormap (Jet)

- Blue/Cyan: Low illuminance (0-1000 lux)
- Green/Yellow: Medium illuminance (1000-3000 lux)
- Orange/Red: High illuminance (3000+ lux)

### Reading Contours

- **Closely spaced contours** = Rapid illuminance change (near windows, shadow edges)
- **Widely spaced contours** = Gradual change (interior zones)
- **Labeled values** = Exact illuminance at that contour

### Quality Indicators

**Good daylighting:**
- Most floor area in 500-2000 lux range
- Smooth gradients, no harsh transitions
- No large areas below 300 lux

**Potential issues:**
- Large areas >5000 lux = glare risk
- Areas <300 lux = insufficient light
- Very tight contours = harsh shadows

### IES Recommended Levels (Reference)

| Space Type | Illuminance (lux) |
|------------|-------------------|
| Corridors | 100 min |
| General office | 300-500 |
| Detailed office work | 500-750 |
| Technical drawing | 750-1000 |

---

## Key Files

| File | Size | Description |
|------|------|-------------|
| `annual.ill` | 63 MB | Hourly illuminance (8760 × 480) |
| `illum.mtx` | 2.7 MB | Daylight coefficients (480 × 146) |
| `nelier_annual.smx` | 13 MB | Annual sky matrix (8760 × 146) |
| `scene.oct` | 2.3 MB | Compiled geometry |
| `points.txt` | 15 KB | Sensor positions |
| `annual_validation.ill` | 8 MB | Validation hourly illuminance (8760 × 63) |
| `illum_validation.mtx` | 111 KB | Validation DC matrix (63 × 146) |
| `points_validation.txt` | 2 KB | Validation sensor positions (63 points) |

---

## Validation Grid Simulation

A separate validation simulation uses a sensor grid matching physical luxmeter measurement positions for comparison with field measurements.

### Validation Grid Specifications

| Parameter | Value |
|-----------|-------|
| Grid size | 7 x 9 = 63 points |
| Spacing | 1.08 m (uniform) |
| Work plane height | 0.75 m |
| Distance from east wall (front) | 0.71 m |
| Distance to west wall | 0.68 m |
| Distance from north/south walls | 0.51 m |

### Validation Files

```
edificio/
├── generate_sensor_grid_validation.py  # Validation grid generator
├── run_simulation_validation.sh        # Validation simulation workflow
├── visualize_hourly_grid_validation.py # Hourly multi-panel visualization
├── create_room_scheme_validation.py    # Room scheme diagram generator
├── points_validation.txt               # Validation sensor positions (63 points)
├── matrices/dc/
│   └── illum_validation.mtx           # Validation DC matrix (63 x 146)
├── results/dc/
│   └── annual_validation.ill          # Validation annual illuminance (8760 x 63)
└── images/
    ├── room_scheme_validation.png     # Room layout with sensor grid
    ├── jun26_hourly_grid_validation.png  # June 26 hourly illuminance (9h-17h)
    └── nov20_hourly_grid_validation.png  # November 20 hourly illuminance (9h-17h)
```

### Run Validation Simulation

```bash
cd edificio
bash run_simulation_validation.sh
```

This runs:
1. Generate validation sensor grid (points_validation.txt)
2. Build octree (scene.oct)
3. Calculate daylight coefficients (illum_validation.mtx)
4. Generate annual illuminance (annual_validation.ill)
5. Create hourly grid visualizations for June 26 and November 20

### Generate Individual Visualizations

**Room scheme diagram:**
```bash
uv run python create_room_scheme_validation.py
```
Output: `images/room_scheme_validation.png`

**Hourly grid for specific date:**
```bash
uv run python visualize_hourly_grid_validation.py --date 2024-06-26 --output jun26_hourly_grid_validation.png
uv run python visualize_hourly_grid_validation.py --date 2024-11-20 --output nov20_hourly_grid_validation.png
```

### Reading Validation Data

```python
import numpy as np

# Load validation annual data
data = np.loadtxt('edificio/results/dc/annual_validation.ill', skiprows=11)
# Shape: (8760, 63) - hours x sensors

# Load validation sensor positions
sensors = np.loadtxt('edificio/points_validation.txt')
# Shape: (63, 6) - columns: x, y, z, dx, dy, dz
x, y = sensors[:, 0], sensors[:, 1]
```

### Validation Grid Layout

```
         NORTH WALL (5 windows)
    ┌─────────────────────────────┐
    │  o   o   o   o   o   o   o  │  ← Row 9 (Y = -0.50m)
    │  o   o   o   o   o   o   o  │
    │  o   o   o   o   o   o   o  │
    │  o   o   o   o   o   o   o  │
E   │  o   o   o   o   o   o   o  │  W
A   │  o   o   o   o   o   o   o  │  E
S   │  o   o   o   o   o   o   o  │  S
T   │  o   o   o   o   o   o   o  │  T
    │  o   o   o   o   o   o   o  │  ← Row 1 (Y = -9.14m)
    └─────────────────────────────┘
         SOUTH WALL (5 windows)

    7 columns (X direction): 1.17m to 7.65m
    9 rows (Y direction): -9.14m to -0.50m
    Spacing: 1.08m in both directions
```
