# Annual Daylighting Simulation - Edificio

Radiance annual daylighting simulation using the Two-Phase Method (Daylight Coefficients).

## Overview

| Parameter | Value |
|-----------|-------|
| Location | Temixco, Mexico (18.85°N, 99.14°W) |
| Method | Two-Phase (Daylight Coefficients) |
| Work plane height | 0.75m |
| Sensor grid | 480 points (20×24, ~0.40m spacing) |
| Temporal coverage | 8,760 hours |

## Directory Structure

```
edificio/
├── run_simulation.sh          # Full simulation workflow
├── generate_sensor_grid.py    # Sensor grid generator
├── visualize_illuminance.py   # Visualization tool
├── materials.rad              # Material definitions
├── scene.rad                  # Scene file
├── points.txt                 # Sensor grid (480 points)
├── images/                    # Output visualizations
├── objects/                   # Geometry files
│   ├── scene.geom
│   ├── glazing.geom
│   └── *.blindgrp
├── skyDomes/
│   └── skyglow.rad
├── skyVectors/
│   └── nelier_annual.smx      # Annual sky matrix
├── matrices/dc/
│   └── illum.mtx              # Daylight coefficients
├── octrees/
│   └── scene.oct
├── results/dc/
│   └── annual.ill             # Annual illuminance results
└── assets/
    ├── nelier_26jun_20novCST.epw
    └── nelier.wea
```

## Quick Start

### Run Full Simulation
```bash
bash run_simulation.sh
```

### Visualize Results
```bash
uv run python visualize_illuminance.py --date 2024-06-21 --time 12:00 --output summer_noon.png
```

Images are saved to `images/` folder.

## Simulation Parameters

### rfluxmtx (Daylight Coefficients)
| Flag | Value |
|------|-------|
| `-ab` | 5 (ambient bounces) |
| `-ad` | 10000 (ambient divisions) |
| `-lw` | 0.0001 (light weight) |
| `-n` | 8 (processors) |

### Sky Model
- Perez model via `gendaymtx`
- Reinhart subdivision (146 patches)
- Hourly resolution

## Materials

| Material | Type | ρ/τ |
|----------|------|-----|
| PISO-CONCRETO-PULIDOIER | plastic | ρ=0.65 |
| CONCRETO-ARMADOIER | plastic | ρ=0.10 |
| LadrilloIER | plastic | ρ=0.55 |
| AluminiumIER | metal | ρ=0.68 |
| PISO-PASILLOIER | plastic | ρ=0.36 |
| Acristalamiento-exterior-del-proyecto | glass | τ=0.978 |

## Room Geometry

- Main room: 8.26m × 9.97m (82.4 m²)
- Sensor grid: 7.66m × 9.37m (0.1m wall offset)
- Windows: North and south walls, 5.5m wide × 2.5m tall

## Visualization

- Colormap: Jet (blue → green → yellow → red)
- Contour levels: [0, 299, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000] lux
- Orientation: North faces left
- Resolution: 300 DPI

## Data Format

### annual.ill
- 8,760 rows (hours) × 480 columns (sensors)
- Values in lux
- Header with Radiance metadata

### points.txt
```
x y z dx dy dz
```
Position (x,y,z) and direction vector (0 0 1 = up).

## Additional Documentation

- `../CLAUDE.md` - Main project guide
- `BUILDING_SPECS.md` - Detailed geometry and materials
