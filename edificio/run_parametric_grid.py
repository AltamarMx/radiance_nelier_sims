#!/usr/bin/env python3
"""
run_parametric_grid.py - Run parametric grid search for optimal calibration

This script runs a grid search over glazing transmittance and floor reflectance
values to find the optimal combination that minimizes error between Radiance
simulation and experimental measurements.

Usage:
    python run_parametric_grid.py
    python run_parametric_grid.py --tau-min 0.70 --tau-max 0.85 --tau-step 0.01

Output:
    results/parametric/grid_results.csv - All simulation results
    results/parametric/optimal_parameters.json - Best parameters found
"""

import argparse
import json
import subprocess
import tempfile
import os
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime


def generate_materials_file(transmittance: float, reflectance: float, output_path: str) -> None:
    """Generate a materials.rad file with specified parameters."""
    content = f"""# Radiance Materials - Parametric Calibration
# Glazing transmittance: {transmittance}
# Floor reflectance: {reflectance}

# FLOORS
void plastic PISO-CONCRETO-PULIDOIER
0
0
5 {reflectance} {reflectance} {reflectance} 0.06 0.02

void plastic PISO-PASILLOIER
0
0
5 0.36 0.36 0.36 0 0

# WALLS & STRUCTURE
void plastic LadrilloIER
0
0
5 0.55 0.55 0.55 0.04 0.03

void plastic Material-de-bloque-de-componente-del-proyecto
0
0
5 0.4 0.4 0.4 0 0

# CEILING
void plastic CONCRETO-ARMADOIER
0
0
5 0.1 0.1 0.1 0 0

# METAL ELEMENTS
void metal AluminiumIER
0
0
5 0.68 0.68 0.68 0.9 0.15

# GLAZING
void glass Acristalamiento-exterior-del-proyecto
0
0
3 {transmittance} {transmittance} {transmittance}
"""
    with open(output_path, 'w') as f:
        f.write(content)


def run_simulation(materials_file: str, edificio_dir: Path) -> str:
    """Run Radiance simulation and return path to annual.ill file."""
    octree_file = edificio_dir / "octrees" / "scene_parametric.oct"
    dc_matrix_file = edificio_dir / "matrices" / "dc" / "illum_parametric.mtx"
    annual_file = edificio_dir / "results" / "parametric" / "annual_parametric.ill"

    # Ensure output directories exist
    octree_file.parent.mkdir(parents=True, exist_ok=True)
    dc_matrix_file.parent.mkdir(parents=True, exist_ok=True)
    annual_file.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Build octree
    oconv_cmd = [
        "oconv",
        str(materials_file),
        str(edificio_dir / "scene.rad"),
        str(edificio_dir / "objects" / "scene.geom"),
        str(edificio_dir / "objects" / "glazing.geom")
    ]
    with open(octree_file, 'w') as f:
        subprocess.run(oconv_cmd, stdout=f, stderr=subprocess.PIPE, check=True)

    # Step 2: Count sensors
    points_file = edificio_dir / "points_validation.txt"
    with open(points_file, 'r') as f:
        sensor_count = sum(1 for line in f if line.strip())

    # Step 3: Calculate daylight coefficients
    rfluxmtx_cmd = [
        "rfluxmtx",
        "-v",
        "-faf",
        "-ab", "5",
        "-ad", "10000",
        "-lw", "0.0001",
        "-n", "8",
        "-I+",
        "-y", str(sensor_count),
        "-",
        str(edificio_dir / "skyDomes" / "skyglow.rad"),
        "-i", str(octree_file)
    ]
    with open(points_file, 'r') as stdin_file:
        with open(dc_matrix_file, 'w') as stdout_file:
            subprocess.run(rfluxmtx_cmd, stdin=stdin_file, stdout=stdout_file,
                         stderr=subprocess.PIPE, check=True)

    # Step 4: Multiply DC × sky matrix
    sky_matrix = edificio_dir / "skyVectors" / "nelier_annual.smx"

    dctimestep_cmd = ["dctimestep", str(dc_matrix_file), str(sky_matrix)]
    dctimestep_proc = subprocess.Popen(dctimestep_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    rmtxop_cmd = ["rmtxop", "-fa", "-t", "-c", "47.4", "119.9", "11.6", "-"]
    with open(annual_file, 'w') as f:
        rmtxop_proc = subprocess.Popen(rmtxop_cmd, stdin=dctimestep_proc.stdout,
                                       stdout=f, stderr=subprocess.PIPE)
        dctimestep_proc.stdout.close()
        rmtxop_proc.communicate()

    return str(annual_file)


def parse_annual_ill_file(filepath: str) -> np.ndarray:
    """Parse the annual.ill file, skip header lines."""
    with open(filepath, 'r') as f:
        lines = f.readlines()

    skip_keywords = ['#', 'NCOMP', 'NROWS', 'NCOLS', 'FORMAT', 'SOFTWARE',
                     'CAPDATE', 'GMT', 'rmtxop', 'dctimestep', 'Applied',
                     'Transposed', 'LATLONG']

    data_start = 0
    for i, line in enumerate(lines):
        is_header = False
        for keyword in skip_keywords:
            if line.startswith(keyword):
                is_header = True
                break
        if not is_header and line.strip():
            data_start = i
            break

    data = []
    for line in lines[data_start:]:
        if line.strip():
            try:
                values = [float(x) for x in line.split()]
                if len(values) > 0:
                    data.append(values)
            except ValueError:
                continue

    return np.array(data)


def datetime_to_hour_of_year(month: int, day: int, hour: int, year: int = 2024) -> int:
    """Convert date/time to hour of year index (0-8759)."""
    start_of_year = datetime(year, 1, 1, 0, 0, 0)
    target_dt = datetime(year, month, day, hour, 0, 0)
    delta = target_dt - start_of_year
    hour_of_year = int(delta.total_seconds() / 3600)
    return max(0, hour_of_year - 1)


def load_experimental_data(base_path: Path, hours: list, reverse_odd_hours: bool = True) -> list:
    """Load experimental data from CSV files."""
    cols_map = ['I1N', 'I2N', 'I3N', 'I4N', 'I1S', 'I2S', 'I3S', 'I4S', 'I5S']
    dataframes = []

    for hour in hours:
        f = base_path / f"{hour:02d}h.csv"
        df = pd.read_csv(f)
        if reverse_odd_hours and hour % 2 == 1:
            df = df[::-1].reset_index(drop=True)
        dataframes.append(df[cols_map] * 1000)  # Convert klux to lux

    return dataframes


def load_radiance_data(ill_file: str, month: int, day: int, hours: list) -> list:
    """Load radiance data for specific date and hours."""
    radiance_data = parse_annual_ill_file(ill_file)
    NX, NY = 7, 9
    cols_map = ['I1N', 'I2N', 'I3N', 'I4N', 'I1S', 'I2S', 'I3S', 'I4S', 'I5S']

    dataframes = []
    for hour in hours:
        hour_idx = datetime_to_hour_of_year(month, day, hour)
        illum_1d = radiance_data[hour_idx, :]
        illum_2d = illum_1d.reshape(NX, NY)
        # Flip rows (to match experimental row order) and columns (N to S)
        illum_matched = illum_2d[::-1, ::-1]
        df = pd.DataFrame(illum_matched, columns=cols_map)
        dataframes.append(df)

    return dataframes


def compute_metrics(exp_list: list, rad_list: list) -> dict:
    """Compute error metrics for experimental vs radiance data."""
    all_exp = np.concatenate([df.values.flatten() for df in exp_list])
    all_rad = np.concatenate([df.values.flatten() for df in rad_list])
    all_err = all_rad - all_exp

    exp_mean = all_exp.mean()
    mbe = all_err.mean()
    rmse = np.sqrt((all_err**2).mean())

    return {
        'exp_mean': float(exp_mean),
        'sim_mean': float(all_rad.mean()),
        'mbe_lux': float(mbe),
        'mbe_pct': float(100 * mbe / exp_mean),
        'rmse_lux': float(rmse),
        'cvrmse_pct': float(100 * rmse / exp_mean)
    }


def run_single_parametric(transmittance: float, reflectance: float,
                          edificio_dir: Path, data_dir: Path) -> dict:
    """Run a single parametric simulation and return metrics."""
    hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]

    # Create temporary materials file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.rad', delete=False) as f:
        materials_file = f.name

    try:
        # Generate materials file
        generate_materials_file(transmittance, reflectance, materials_file)

        # Run simulation
        annual_file = run_simulation(materials_file, edificio_dir)

        # Load experimental data
        exp_jun26 = load_experimental_data(data_dir / "005_26Junio", hours)
        exp_nov20 = load_experimental_data(data_dir / "006_20Nov", hours)

        # Load radiance results
        rad_jun26 = load_radiance_data(annual_file, 6, 26, hours)
        rad_nov20 = load_radiance_data(annual_file, 11, 20, hours)

        # Compute metrics
        metrics_jun26 = compute_metrics(exp_jun26, rad_jun26)
        metrics_nov20 = compute_metrics(exp_nov20, rad_nov20)

        # Combined error (equal weights for both days, both metrics)
        combined_error = (
            0.25 * abs(metrics_jun26['mbe_pct']) +
            0.25 * abs(metrics_nov20['mbe_pct']) +
            0.25 * metrics_jun26['cvrmse_pct'] +
            0.25 * metrics_nov20['cvrmse_pct']
        )

        return {
            'transmittance': transmittance,
            'reflectance': reflectance,
            'mbe_jun_pct': metrics_jun26['mbe_pct'],
            'mbe_nov_pct': metrics_nov20['mbe_pct'],
            'cvrmse_jun_pct': metrics_jun26['cvrmse_pct'],
            'cvrmse_nov_pct': metrics_nov20['cvrmse_pct'],
            'combined_error': combined_error,
            'success': True
        }

    except Exception as e:
        return {
            'transmittance': transmittance,
            'reflectance': reflectance,
            'error': str(e),
            'success': False
        }

    finally:
        # Cleanup temporary files
        if os.path.exists(materials_file):
            os.remove(materials_file)


def main():
    parser = argparse.ArgumentParser(
        description='Run parametric grid search for optimal calibration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default grid (88 simulations)
    python run_parametric_grid.py

    # Custom transmittance range
    python run_parametric_grid.py --tau-min 0.70 --tau-max 0.82 --tau-step 0.02

    # Finer grid (more simulations)
    python run_parametric_grid.py --tau-step 0.01 --rho-step 0.01
        """
    )
    parser.add_argument('--tau-min', type=float, default=0.65,
                       help='Minimum glazing transmittance (default: 0.65)')
    parser.add_argument('--tau-max', type=float, default=0.85,
                       help='Maximum glazing transmittance (default: 0.85)')
    parser.add_argument('--tau-step', type=float, default=0.02,
                       help='Transmittance step size (default: 0.02)')
    parser.add_argument('--rho-min', type=float, default=0.10,
                       help='Minimum floor reflectance (default: 0.10)')
    parser.add_argument('--rho-max', type=float, default=0.25,
                       help='Maximum floor reflectance (default: 0.25)')
    parser.add_argument('--rho-step', type=float, default=0.02,
                       help='Reflectance step size (default: 0.02)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from existing results file')

    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    edificio_dir = script_dir
    data_dir = script_dir.parent / "data" / "experimental"
    results_dir = edificio_dir / "results" / "parametric"
    results_dir.mkdir(parents=True, exist_ok=True)

    results_file = results_dir / "grid_results.csv"
    optimal_file = results_dir / "optimal_parameters.json"

    # Generate parameter grid
    tau_values = np.arange(args.tau_min, args.tau_max + args.tau_step/2, args.tau_step)
    rho_values = np.arange(args.rho_min, args.rho_max + args.rho_step/2, args.rho_step)

    print("=" * 60)
    print("PARAMETRIC GRID SEARCH")
    print("=" * 60)
    print(f"Transmittance (τ): {args.tau_min:.2f} - {args.tau_max:.2f} (step {args.tau_step:.2f})")
    print(f"  Values: {[f'{v:.2f}' for v in tau_values]}")
    print(f"Reflectance (ρ): {args.rho_min:.2f} - {args.rho_max:.2f} (step {args.rho_step:.2f})")
    print(f"  Values: {[f'{v:.2f}' for v in rho_values]}")
    print(f"Total combinations: {len(tau_values) * len(rho_values)}")
    print("=" * 60)
    print()

    # Load existing results if resuming
    completed = set()
    results = []
    if args.resume and results_file.exists():
        existing_df = pd.read_csv(results_file)
        results = existing_df.to_dict('records')
        for r in results:
            completed.add((round(r['transmittance'], 3), round(r['reflectance'], 3)))
        print(f"Resuming: {len(completed)} simulations already completed")
        print()

    # Run grid search
    total = len(tau_values) * len(rho_values)
    start_time = time.time()
    idx = 0

    for tau in tau_values:
        for rho in rho_values:
            idx += 1

            # Skip if already completed
            if (round(tau, 3), round(rho, 3)) in completed:
                print(f"[{idx}/{total}] τ={tau:.2f}, ρ={rho:.2f} ... SKIPPED (already done)")
                continue

            print(f"[{idx}/{total}] τ={tau:.2f}, ρ={rho:.2f} ... ", end="", flush=True)

            sim_start = time.time()
            result = run_single_parametric(tau, rho, edificio_dir, data_dir)
            sim_time = time.time() - sim_start

            if result['success']:
                print(f"done ({sim_time:.1f}s) - Combined: {result['combined_error']:.1f}%")
            else:
                print(f"FAILED: {result.get('error', 'Unknown error')}")

            results.append(result)

            # Save intermediate results
            pd.DataFrame(results).to_csv(results_file, index=False)

    total_time = time.time() - start_time

    # Filter successful results
    results_df = pd.DataFrame(results)
    successful_df = results_df[results_df['success'] == True].copy()

    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total simulations: {len(results_df)}")
    print(f"Successful: {len(successful_df)}")
    print(f"Failed: {len(results_df) - len(successful_df)}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print()

    if len(successful_df) > 0:
        # Find optimal parameters
        optimal_idx = successful_df['combined_error'].idxmin()
        optimal = successful_df.loc[optimal_idx]

        print("OPTIMAL PARAMETERS:")
        print(f"  Glazing transmittance (τ): {optimal['transmittance']:.2f}")
        print(f"  Floor reflectance (ρ):     {optimal['reflectance']:.2f}")
        print()
        print("Metrics at optimal point:")
        print(f"  June 26 MBE:       {optimal['mbe_jun_pct']:+.1f}%")
        print(f"  June 26 CV(RMSE):  {optimal['cvrmse_jun_pct']:.1f}%")
        print(f"  Nov 20 MBE:        {optimal['mbe_nov_pct']:+.1f}%")
        print(f"  Nov 20 CV(RMSE):   {optimal['cvrmse_nov_pct']:.1f}%")
        print(f"  Combined error:    {optimal['combined_error']:.1f}%")
        print("=" * 60)

        # Save optimal parameters
        optimal_params = {
            'transmittance': float(optimal['transmittance']),
            'reflectance': float(optimal['reflectance']),
            'mbe_jun_pct': float(optimal['mbe_jun_pct']),
            'mbe_nov_pct': float(optimal['mbe_nov_pct']),
            'cvrmse_jun_pct': float(optimal['cvrmse_jun_pct']),
            'cvrmse_nov_pct': float(optimal['cvrmse_nov_pct']),
            'combined_error': float(optimal['combined_error'])
        }

        with open(optimal_file, 'w') as f:
            json.dump(optimal_params, f, indent=2)

        print(f"\nResults saved to: {results_file}")
        print(f"Optimal parameters saved to: {optimal_file}")
    else:
        print("No successful simulations!")
        sys.exit(1)


if __name__ == '__main__':
    main()
