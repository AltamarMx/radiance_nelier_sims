#!/usr/bin/env python3
"""
run_parametric_search.py — Búsqueda paramétrica sobre (τ, ρ_floor, ρ_hall).

Para cada combinación de parámetros:
  1. Genera un materials.rad temporal con los valores
  2. Compila octree, calcula DC matrix, genera iluminancia anual
  3. Compara contra mediciones experimentales (26 jun y 20 nov)
  4. Calcula NMBE, CV(RMSE), R² y GOF para cada día
  5. Guarda fila en CSV (incremental, soporta --resume)

Salidas:
  data/parametric/grid_results.csv         (todas las combinaciones)
  data/parametric/optimal_parameters.json  (óptimos por día y combinado)

Tiempo aproximado: ~1.5 min por combinación con 8 cores.
  - Default (8×7×6 = 336 combinaciones): ~8 horas
  - --quick (4×4×4 = 64 combinaciones):  ~1.5 horas

Uso:
  bash scripts/run_radiance.sh                    # primero, asegurar que el pipeline base funciona
  uv run python scripts/run_parametric_search.py            # default
  uv run python scripts/run_parametric_search.py --quick    # grid reducido
  uv run python scripts/run_parametric_search.py --resume   # continúa desde grid_results.csv
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

# Hacer importable lib/
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from lib.radiance_io import load_experimental_data, load_radiance_data  # noqa: E402
from lib.metrics import compute_metrics  # noqa: E402

EDIFICIO = ROOT / "edificio"
DATA = ROOT / "data"
EXP_DIR = DATA / "experimental"
PARAM_DIR = DATA / "parametric"
PARAM_DIR.mkdir(parents=True, exist_ok=True)

# Archivos generados por iteración (sobreescritos)
OCT_FILE = EDIFICIO / "octrees" / "scene_parametric.oct"
MTX_FILE = EDIFICIO / "matrices" / "dc" / "illum_parametric.mtx"
ILL_FILE = EDIFICIO / "results" / "dc" / "annual_parametric.ill"
SMX_FILE = EDIFICIO / "skyVectors" / "nelier_annual.smx"
POINTS_FILE = EDIFICIO / "points" / "points_validation.txt"

HOURS = list(range(9, 18))  # 9 a 17 (común a jun y nov)


def generate_materials_rad(tau, rho_floor, rho_hall, output_path):
    """Escribe un materials.rad temporal con los parámetros indicados.

    Base: scene.mat + glazing.mat de la nueva exportación de DesignBuilder
    (geometría con puerta). Solo τ, ρ_floor, ρ_hall varían — el resto de
    materiales se mantienen fijos. Incluye AluminiumIERamarillo (puerta).
    """
    content = f"""# Materiales paramétricos (geometría con puerta)
# τ={tau:.2f}, ρ_floor={rho_floor:.2f}, ρ_hall={rho_hall:.2f}

void plastic PISO-CONCRETO-PULIDOIER
0
0
5 {rho_floor} {rho_floor} {rho_floor} 0.2 0

void plastic PISO-PASILLOIER
0
0
5 {rho_hall} {rho_hall} {rho_hall} 0.2 0

void plastic LadrilloIER
0
0
5 0.55 0.55 0.55 0 0

void plastic CONCRETO-ARMADOIER
0
0
5 0.1 0.1 0.1 0 0

void metal AluminiumIER
0
0
5 0.68 0.68 0.68 0 0

# Puerta amarilla: R=G altos, B bajo. ρ luminosa = 0.265R+0.670G+0.065B = 0.37
void metal AluminiumIERamarillo
0
0
5 0.393 0.393 0.039 0 0

void glass Acristalamiento-exterior-del-proyecto
0
0
3 {tau} {tau} {tau}
"""
    Path(output_path).write_text(content)


def run_radiance(materials_path):
    """Compila octree + DC matrix + iluminancia anual para los materiales dados.

    Todos los subprocess corren con cwd=EDIFICIO porque scene.rad usa paths
    relativos (./objects/...) y los octrees compilados por oconv guardan paths
    relativos a la cwd al momento de compilación. Los paths que pasamos a los
    comandos también son relativos a EDIFICIO para consistencia con run_radiance.sh.
    """
    n_sensors = sum(1 for _ in POINTS_FILE.open())

    # Paths relativos a EDIFICIO (para que coincidan con los del .sh)
    oct_rel = OCT_FILE.relative_to(EDIFICIO)
    mtx_rel = MTX_FILE.relative_to(EDIFICIO)
    ill_rel = ILL_FILE.relative_to(EDIFICIO)
    smx_rel = SMX_FILE.relative_to(EDIFICIO)
    points_rel = POINTS_FILE.relative_to(EDIFICIO)
    skyglow_rel = "skyDomes/skyglow.rad"

    # 1. oconv (con cwd=EDIFICIO)
    with OCT_FILE.open("w") as f:
        subprocess.run(
            ["oconv", str(materials_path), "scene.rad",
             "objects/scene.geom", "objects/glazing.geom"],
            stdout=f, stderr=subprocess.PIPE, check=True, cwd=EDIFICIO,
        )

    # 2. rfluxmtx (paso lento) — DESDE cwd=EDIFICIO
    with POINTS_FILE.open() as stdin_f, MTX_FILE.open("w") as stdout_f:
        subprocess.run(
            ["rfluxmtx", "-faf", "-ab", "5", "-ad", "10000", "-lw", "0.0001",
             "-n", "8", "-I+", "-y", str(n_sensors),
             "-", skyglow_rel,
             "-i", str(oct_rel)],
            stdin=stdin_f, stdout=stdout_f, stderr=subprocess.PIPE,
            check=True, cwd=EDIFICIO,
        )

    # 3. dctimestep | rmtxop — DESDE cwd=EDIFICIO
    p1 = subprocess.Popen(
        ["dctimestep", str(mtx_rel), str(smx_rel)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=EDIFICIO,
    )
    with ILL_FILE.open("w") as f:
        p2 = subprocess.Popen(
            ["rmtxop", "-fa", "-t", "-c", "47.4", "119.9", "11.6", "-"],
            stdin=p1.stdout, stdout=f, stderr=subprocess.PIPE, cwd=EDIFICIO,
        )
        p1.stdout.close()
        p2.communicate()
    if p2.returncode != 0:
        raise RuntimeError(f"rmtxop falló (rc={p2.returncode})")


def evaluate_combination(tau, rho_floor, rho_hall, exp_jun, exp_nov):
    """Corre una simulación y devuelve métricas por día."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rad", delete=False) as f:
        materials_path = f.name
    try:
        generate_materials_rad(tau, rho_floor, rho_hall, materials_path)
        run_radiance(materials_path)

        rad_jun = load_radiance_data(ILL_FILE, 6, 26, HOURS)
        rad_nov = load_radiance_data(ILL_FILE, 11, 20, HOURS)
        m_jun = compute_metrics(exp_jun, rad_jun)
        m_nov = compute_metrics(exp_nov, rad_nov)

        gof_combined = (m_jun['gof'] + m_nov['gof']) / 2.0
        return {
            'tau': float(tau), 'rho_floor': float(rho_floor), 'rho_hall': float(rho_hall),
            'nmbe_jun': m_jun['nmbe'], 'cvrmse_jun': m_jun['cvrmse'], 'nmae_jun': m_jun['nmae'],
            'r2_jun': m_jun['r2'], 'gof_jun': m_jun['gof'],
            'nmbe_nov': m_nov['nmbe'], 'cvrmse_nov': m_nov['cvrmse'], 'nmae_nov': m_nov['nmae'],
            'r2_nov': m_nov['r2'], 'gof_nov': m_nov['gof'],
            'gof_combined': float(gof_combined),
            'meets_ashrae_jun': m_jun['meets_ashrae'],
            'meets_ashrae_nov': m_nov['meets_ashrae'],
            'success': True,
        }
    except Exception as e:
        return {
            'tau': float(tau), 'rho_floor': float(rho_floor), 'rho_hall': float(rho_hall),
            'error': str(e), 'success': False,
        }
    finally:
        if os.path.exists(materials_path):
            os.remove(materials_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="Grid reducido 4×4×4 = 64 combinaciones (~1.5 h)")
    ap.add_argument("--resume", action="store_true",
                    help="Continúa desde grid_results.csv si existe")
    ap.add_argument("--tau-min", type=float, default=None)
    ap.add_argument("--tau-max", type=float, default=None)
    ap.add_argument("--rho-floor-min", type=float, default=None)
    ap.add_argument("--rho-floor-max", type=float, default=None)
    ap.add_argument("--rho-hall-min", type=float, default=None)
    ap.add_argument("--rho-hall-max", type=float, default=None)
    ap.add_argument("--step", type=float, default=None)
    args = ap.parse_args()

    if args.quick:
        tau_grid = np.round(np.linspace(0.70, 0.82, 4), 2)
        rho_floor_grid = np.round(np.linspace(0.10, 0.20, 4), 2)
        rho_hall_grid = np.round(np.linspace(0.13, 0.21, 4), 2)
    else:
        step = args.step or 0.02
        tau_grid = np.round(np.arange(args.tau_min or 0.68, (args.tau_max or 0.82) + 1e-9, step), 2)
        rho_floor_grid = np.round(np.arange(args.rho_floor_min or 0.09, (args.rho_floor_max or 0.21) + 1e-9, step), 2)
        rho_hall_grid = np.round(np.arange(args.rho_hall_min or 0.11, (args.rho_hall_max or 0.21) + 1e-9, step), 2)

    total = len(tau_grid) * len(rho_floor_grid) * len(rho_hall_grid)
    results_file = PARAM_DIR / "grid_results.csv"
    optimal_file = PARAM_DIR / "optimal_parameters.json"

    print("=" * 70)
    print("BÚSQUEDA PARAMÉTRICA — τ × ρ_floor × ρ_hall")
    print("=" * 70)
    print(f"  τ:        {tau_grid[0]:.2f} a {tau_grid[-1]:.2f}  ({len(tau_grid)} valores)")
    print(f"  ρ_floor:  {rho_floor_grid[0]:.2f} a {rho_floor_grid[-1]:.2f}  ({len(rho_floor_grid)} valores)")
    print(f"  ρ_hall:   {rho_hall_grid[0]:.2f} a {rho_hall_grid[-1]:.2f}  ({len(rho_hall_grid)} valores)")
    print(f"  Total:    {total} combinaciones")
    print(f"  Estimado: ~{total * 1.5 / 60:.1f} horas")
    print(f"  CSV:      {results_file.relative_to(ROOT)}")
    print("=" * 70)
    print()

    # Cargar experimentales una sola vez
    exp_jun = load_experimental_data(EXP_DIR / "005_26Junio", HOURS)
    exp_nov = load_experimental_data(EXP_DIR / "006_20Nov", HOURS)

    # Resume support
    completed = set()
    results = []
    if args.resume and results_file.exists():
        existing = pd.read_csv(results_file)
        results = existing.to_dict("records")
        for r in results:
            completed.add((round(r['tau'], 2), round(r['rho_floor'], 2), round(r['rho_hall'], 2)))
        print(f"Resume: {len(completed)} ya completadas. Saltándolas.\n")

    # Asegurar carpetas para artefactos paramétricos (regenerados por iteración)
    OCT_FILE.parent.mkdir(parents=True, exist_ok=True)
    MTX_FILE.parent.mkdir(parents=True, exist_ok=True)
    ILL_FILE.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    for idx, (tau, rho_floor, rho_hall) in enumerate(
        product(tau_grid, rho_floor_grid, rho_hall_grid), start=1
    ):
        key = (round(float(tau), 2), round(float(rho_floor), 2), round(float(rho_hall), 2))
        if key in completed:
            continue

        elapsed = time.time() - start
        done = idx - len(completed)
        eta = (total - idx) * (elapsed / done) / 60 if done > 0 else 0

        t0 = time.time()
        print(f"  [{idx}/{total}] τ={tau:.2f} ρf={rho_floor:.2f} ρh={rho_hall:.2f} ... ", end="", flush=True)
        r = evaluate_combination(tau, rho_floor, rho_hall, exp_jun, exp_nov)
        dt = time.time() - t0

        if r['success']:
            print(f"OK ({dt:.0f}s) GOF_jun={r['gof_jun']:5.1f}% GOF_nov={r['gof_nov']:5.1f}%  ETA: {eta:.1f}min")
        else:
            print(f"FAIL: {r.get('error', 'unknown')}")

        results.append(r)
        # Guardar CSV en cada iteración (resume seguro)
        pd.DataFrame(results).to_csv(results_file, index=False)

    total_time = time.time() - start
    print(f"\nCompletado en {total_time / 60:.1f} min ({total_time / 3600:.2f} h)")

    # Resumen y óptimos
    df = pd.DataFrame(results)
    ok = df[df.get('success', False) == True].copy()
    if len(ok) == 0:
        print("Sin corridas exitosas.")
        return

    best_jun = ok.loc[ok['gof_jun'].idxmin()]
    best_nov = ok.loc[ok['gof_nov'].idxmin()]
    best_combined = ok.loc[ok['gof_combined'].idxmin()]

    optimal = {
        'best_june':     {k: float(best_jun[k])     for k in best_jun.index if isinstance(best_jun[k], (int, float, np.floating, np.integer))},
        'best_november': {k: float(best_nov[k])     for k in best_nov.index if isinstance(best_nov[k], (int, float, np.floating, np.integer))},
        'best_combined': {k: float(best_combined[k]) for k in best_combined.index if isinstance(best_combined[k], (int, float, np.floating, np.integer))},
    }
    optimal_file.write_text(json.dumps(optimal, indent=2))

    print()
    print("=" * 70)
    print("ÓPTIMOS")
    print("=" * 70)
    for label, b in [("Mejor para 26 jun", best_jun),
                     ("Mejor para 20 nov", best_nov),
                     ("Mejor combinado",   best_combined)]:
        print(f"  {label}:")
        print(f"    τ={b['tau']:.2f}  ρ_floor={b['rho_floor']:.2f}  ρ_hall={b['rho_hall']:.2f}")
        print(f"    GOF_jun={b['gof_jun']:5.2f}%  NMBE_jun={b['nmbe_jun']:+5.2f}%  NMAE_jun={b['nmae_jun']:5.2f}%")
        print(f"    GOF_nov={b['gof_nov']:5.2f}%  NMBE_nov={b['nmbe_nov']:+5.2f}%  NMAE_nov={b['nmae_nov']:5.2f}%")
        print()

    print(f"CSV resultados: {results_file}")
    print(f"JSON óptimos:   {optimal_file}")


if __name__ == "__main__":
    main()
