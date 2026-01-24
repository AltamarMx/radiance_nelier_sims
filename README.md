# Radiance Daylighting Simulation - Validation Study

Annual daylighting simulation for a building in Temixco, Mexico, using the Radiance Two-Phase Method with validation against experimental measurements.

## Requirements

### Software
- **Radiance** (lighting simulation) - [radiance-online.org](https://www.radiance-online.org/)
- **Python 3.11+**
- **uv** (Python package manager) - [docs.astral.sh/uv](https://docs.astral.sh/uv/)
- **Quarto** (for reports) - [quarto.org](https://quarto.org/)

### Verify Radiance Installation
```bash
# These commands should work after installing Radiance
oconv -version
rfluxmtx -version
dctimestep -version
```

## Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd radiance_nelier_sims
```

### 2. Install Python dependencies
```bash
uv sync
```

### 3. Run the validation simulation (7×9 grid)
```bash
cd edificio

# Build octree
oconv materials.rad scene.rad objects/scene.geom objects/glazing.geom > octrees/scene.oct

# Calculate daylight coefficients (~5-10 min)
SENSOR_COUNT=$(wc -l < points_validation.txt | tr -d ' ')
rfluxmtx -v -faf -ab 5 -ad 10000 -lw 0.0001 -n 8 \
    -I+ -y "$SENSOR_COUNT" \
    - skyDomes/skyglow.rad \
    -i octrees/scene.oct \
    < points_validation.txt \
    > matrices/dc/illum_validation.mtx

# Generate annual illuminance
dctimestep matrices/dc/illum_validation.mtx skyVectors/nelier_annual.smx \
    | rmtxop -fa -t -c 47.4 119.9 11.6 - \
    > results/dc/annual_validation.ill
```

### 4. Generate the validation report
```bash
cd report
QUARTO_PYTHON=$(uv run which python) quarto render validation_report.qmd
```

## Project Structure

```
radiance_nelier_sims/
├── CLAUDE.md                    # Detailed project documentation
├── README.md                    # This file
├── pyproject.toml               # Python dependencies
├── uv.lock                      # Locked dependencies
│
├── data/
│   └── experimental/            # Field measurements (CSV)
│       ├── 005_26Junio/         # June 26 measurements
│       └── 006_20Nov/           # November 20 measurements
│
├── edificio/                    # Radiance model
│   ├── materials.rad            # Material definitions
│   ├── scene.rad                # Scene description
│   ├── points_validation.txt    # Sensor grid (63 points)
│   ├── objects/                 # Geometry files
│   ├── skyDomes/                # Sky hemisphere
│   ├── skyVectors/              # Annual sky matrix
│   ├── assets/                  # Weather files
│   ├── octrees/                 # Compiled geometry (generated)
│   ├── matrices/dc/             # Daylight coefficients (generated)
│   ├── results/dc/              # Annual illuminance (generated)
│   └── images/                  # Visualizations (generated)
│
├── scripts/                     # Analysis scripts
│   ├── 001_26jun_exp.py         # Experimental visualization
│   ├── 002_26jun_radiance.py    # Radiance visualization
│   ├── 003_26jun_error.py       # Error analysis
│   ├── 004_comparison_tables.py # Comparison tables
│   └── 005_diagnostic.py        # Data alignment diagnostics
│
└── report/                      # Quarto report
    ├── validation_report.qmd    # Main report
    └── MATERIALS.md             # Optical properties
```

## Key Files

| File | Description |
|------|-------------|
| `edificio/materials.rad` | Optical properties (reflectance, transmittance) |
| `edificio/points_validation.txt` | 63 sensor positions (7×9 grid) |
| `edificio/assets/nelier.wea` | Weather data for Temixco, Mexico |
| `data/experimental/` | Field measurements in klux |

## Simulation Parameters

| Parameter | Value |
|-----------|-------|
| Location | Temixco, Mexico (18.85°N, 99.14°W) |
| Sensor grid | 7×9 = 63 points |
| Work plane height | 0.75 m |
| Ambient bounces | 5 |
| Ambient divisions | 10000 |
| Sky patches | 146 (Reinhart m=1) |

## Validation Dates

- **June 26**: Summer conditions
- **November 20**: Fall/winter conditions

## License

[Add license information]

## References

- Radiance: Ward, G. J. (1994). The RADIANCE lighting simulation and rendering system.
- Two-Phase Method: McNeil, A. (2013). The Five-Phase Method for Simulating Complex Fenestration.
# radiance_nelier_sims
