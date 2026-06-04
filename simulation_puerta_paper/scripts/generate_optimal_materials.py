#!/usr/bin/env python3
"""
generate_optimal_materials.py — Genera 3 archivos materials_*.rad calibrados
desde data/parametric/optimal_parameters.json.

Crea:
  edificio/materials/materials_calibrated.rad   (mejor combinado)
  edificio/materials/materials_jun_optimal.rad  (mejor para 26 jun)
  edificio/materials/materials_nov_optimal.rad  (mejor para 20 nov)

Cada archivo es idéntico a materials.rad excepto por (τ, ρ_floor, ρ_hall)
ajustados a los valores óptimos.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDIFICIO = ROOT / "edificio"
PARAM_JSON = ROOT / "data" / "parametric" / "optimal_parameters.json"
MATERIALS_DIR = EDIFICIO / "materials"


def write_materials_rad(path: Path, tau: float, rho_floor: float, rho_hall: float, label: str):
    """Escribe un materials_<label>.rad con los parámetros indicados."""
    content = f"""# Radiance Materials — {label}
# Generado por scripts/generate_optimal_materials.py desde optimal_parameters.json
# τ={tau:.2f}, ρ_floor={rho_floor:.2f}, ρ_hall={rho_hall:.2f}
# Resto de materiales: igual que materials.rad base (geometría con puerta)

# FLOORS
void plastic PISO-CONCRETO-PULIDOIER
0
0
5 {rho_floor} {rho_floor} {rho_floor} 0.2 0

void plastic PISO-PASILLOIER
0
0
5 {rho_hall} {rho_hall} {rho_hall} 0.2 0

# WALLS & STRUCTURE
void plastic LadrilloIER
0
0
5 0.55 0.55 0.55 0 0

# CEILING
void plastic CONCRETO-ARMADOIER
0
0
5 0.1 0.1 0.1 0 0

# METAL ELEMENTS
void metal AluminiumIER
0
0
5 0.68 0.68 0.68 0 0

# DOOR (puerta amarilla) — ρ luminosa = 0.265R+0.670G+0.065B = 0.37
void metal AluminiumIERamarillo
0
0
5 0.393 0.393 0.039 0 0

# GLAZING
void glass Acristalamiento-exterior-del-proyecto
0
0
3 {tau} {tau} {tau}
"""
    path.write_text(content)


def main():
    if not PARAM_JSON.exists():
        print(f"ERROR: no existe {PARAM_JSON.relative_to(ROOT)}", file=sys.stderr)
        print("  Corre primero: uv run python scripts/run_parametric_search.py", file=sys.stderr)
        sys.exit(1)

    optimal = json.loads(PARAM_JSON.read_text())

    mapping = [
        ("calibrated",  "best_combined", "Calibrado combinado"),
        ("jun_optimal", "best_june",     "Óptimo 26 jun"),
        ("nov_optimal", "best_november", "Óptimo 20 nov"),
    ]

    for variant, key, label in mapping:
        if key not in optimal:
            print(f"  Skip {variant}: '{key}' no está en JSON")
            continue
        params = optimal[key]
        out = MATERIALS_DIR / f"materials_{variant}.rad"
        write_materials_rad(out, params['tau'], params['rho_floor'], params['rho_hall'], label)
        print(f"  OK: {out.relative_to(ROOT)}  "
              f"(τ={params['tau']:.2f}, ρ_floor={params['rho_floor']:.2f}, ρ_hall={params['rho_hall']:.2f})")


if __name__ == "__main__":
    main()
