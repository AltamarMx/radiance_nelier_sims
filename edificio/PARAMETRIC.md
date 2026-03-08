# Extended Parametric Calibration with Hallway

## Overview

Extended parametric search including hallway reflectance with ASHRAE-compliant metrics (NMBE, CV(RMSE), R², GOF).

## Context

The Radiance daylighting simulation overestimates measured illuminance values due to unmodeled window frames and furniture. Calibration adjusts effective material properties to compensate for these missing elements.

---

## Reference Values

Measured values from materials.rad:

| Parameter | Measured Value | Material Name |
|-----------|----------------|---------------|
| Glazing transmittance (τ) | 0.88 | Acristalamiento-exterior-del-proyecto |
| Floor reflectance (ρ_floor) | 0.30 | PISO-CONCRETO-PULIDOIER |
| Hallway reflectance (ρ_hall) | 0.36 | PISO-PASILLOIER |

---

## Parameter Grid

### Search Ranges

Calibrated "effective" values are lower than measured values to account for unmodeled geometry (frames, furniture).

| Parameter | Min | Max | Step | Values |
|-----------|-----|-----|------|--------|
| τ (transmittance) | 0.58 | 0.88 | 0.02 | 16 |
| ρ_floor | 0.05 | 0.30 | 0.02 | 13 |
| ρ_hall | 0.11 | 0.36 | 0.02 | 13 |

**Total combinations**: 16 × 13 × 13 = **2704 simulations**

---

## Metrics

### ASHRAE Guideline 14 Thresholds (Hourly Data)

| Metric | Formula | Threshold |
|--------|---------|-----------|
| **NMBE** | [Σ(E_meas - E_sim) / (n × Ē_meas)] × 100% | ≤ ±10% |
| **CV(RMSE)** | (RMSE / Ē_meas) × 100% | ≤ 30% |
| **R²** | 1 - SS_res / SS_tot | > 0.85 |
| **GOF** | √(NMBE² + CV(RMSE)²) | Minimize |

**Note**: NMBE positive = simulation underestimates measurements

### Selection Criteria

**Optimal solution**: Minimize GOF subject to ASHRAE thresholds

---

## Scripts

### `run_parametric_single.py`

Single-point simulation script with three parameters.

**Usage:**
```bash
cd edificio
uv run python run_parametric_single.py --tau 0.77 --rho-floor 0.12 --rho-hall 0.25
uv run python run_parametric_single.py -t 0.77 -f 0.12 -h 0.25 --output results.json
```

**Arguments:**
- `-t, --tau`: Glazing transmittance (0.0-1.0)
- `-f, --rho-floor`: Floor reflectance (0.0-1.0)
- `-h, --rho-hall`: Hallway reflectance (0.0-1.0)
- `-o, --output`: Output JSON file (default: stdout)

**Output JSON:**
```json
{
  "tau": 0.77,
  "rho_floor": 0.12,
  "rho_hall": 0.25,
  "june26": {"nmbe": ..., "cvrmse": ..., "r2": ..., "gof": ..., "meets_ashrae": ...},
  "november20": {"nmbe": ..., "cvrmse": ..., "r2": ..., "gof": ..., "meets_ashrae": ...},
  "combined": {"nmbe": ..., "cvrmse": ..., "r2": ..., "gof": ..., "meets_ashrae": ...},
  "gof": ...,
  "success": true
}
```

### `run_parametric_grid_extended.py`

Batch grid search over all parameter combinations.

**Usage:**
```bash
cd edificio
uv run python run_parametric_grid_extended.py           # Run full grid search
uv run python run_parametric_grid_extended.py --resume  # Continue interrupted run
```

**Features:**
- Progress reporting with ETA
- Incremental CSV saves (every 10 simulations)
- Resume capability from previous runs
- Summary statistics at completion

**Output Files:**
- `results/parametric/grid_results_extended.csv`: All simulation results
- `results/parametric/optimal_parameters_extended.json`: Best parameters found

---

## Analysis Report

### `report/parametric_calibration_extended.qmd`

Quarto document for analysis and visualization. Loads results from CSV (does not run simulations).

**Render:**
```bash
cd report
quarto render parametric_calibration_extended.qmd
```

**Sections:**
1. Introduction & ASHRAE metrics
2. Optimal parameters summary
3. ASHRAE compliance analysis
4. GOF heatmaps (2D slices at optimal values)
5. NMBE and CV(RMSE) heatmaps
6. R² heatmap with ASHRAE threshold contour
7. Sensitivity analysis per parameter
8. Parameter contribution ranking
9. Original vs Optimal comparison
10. Conclusions

---

## File Structure

```
edificio/
├── PARAMETRIC.md                     # This document
├── run_parametric_single.py          # Single-point simulation
├── run_parametric_grid_extended.py   # Batch grid search
├── results/parametric/
│   ├── grid_results.csv              # Previous 2-parameter results
│   ├── grid_results_extended.csv     # Extended 3-parameter results
│   ├── optimal_parameters.json       # Previous optimal
│   └── optimal_parameters_extended.json  # Extended optimal

report/
├── parametric_calibration.qmd        # Previous 2-parameter analysis
└── parametric_calibration_extended.qmd  # Extended 3-parameter analysis
```

---

## Results CSV Columns

```
tau              - Glazing transmittance
rho_floor        - Floor reflectance
rho_hall         - Hallway reflectance
nmbe_jun         - NMBE June 26 [%]
nmbe_nov         - NMBE November 20 [%]
nmbe_combined    - Combined NMBE [%]
cvrmse_jun       - CV(RMSE) June 26 [%]
cvrmse_nov       - CV(RMSE) November 20 [%]
cvrmse_combined  - Combined CV(RMSE) [%]
r2_jun           - R² June 26
r2_nov           - R² November 20
r2_combined      - Combined R²
gof              - Goodness of Fit [%]
meets_ashrae     - Boolean: meets ASHRAE thresholds
success          - Boolean: simulation successful
```

---

## Execution Workflow

```bash
# Step 1: Run extended grid search (~6 hours for 2704 simulations)
cd edificio
uv run python run_parametric_grid_extended.py

# Step 2: Generate analysis report
cd report
quarto render parametric_calibration_extended.qmd
```

**Resume interrupted run:**
```bash
cd edificio
uv run python run_parametric_grid_extended.py --resume
```

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-31 | 1.0 | Initial plan |
| 2024-01-31 | 1.1 | Confirmed measured values, hallway always included |
| 2024-01-31 | 2.0 | Converted to documentation of implemented scripts |
