#!/usr/bin/env python3
"""
generate_sensor_grid.py — Genera la rejilla de sensores 7x9 (63 puntos).

Coincide con las posiciones físicas de los luxómetros de las campañas
26 jun 2024 y 20 nov 2024.

Especificaciones (de las mediciones de campo):
  - 7 puntos en X (este-oeste, frente a fondo)
  - 9 puntos en Y (norte-sur, entre ventanas)
  - Espaciado uniforme 1.08 m
  - Altura plano de trabajo: 0.75 m
  - Offsets: 0.71 m (este), 0.68 m (oeste), 0.51 m (norte/sur)

Salida (relativa a la raíz del folder):
  edificio/points/points_validation.txt
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "edificio" / "points" / "points_validation.txt"

# Dimensiones del salón (de PISO-CONCRETO-PULIDOIER)
ROOM_MIN_X = 0.458644626504064   # pared este
ROOM_MAX_X = 8.31864462650407    # pared oeste
ROOM_MIN_Y = -9.65327504952668   # pared sur (ventanas)
ROOM_MAX_Y = -0.0832750495266698 # pared norte (ventanas)

# Rejilla
NX = 7
NY = 9
SPACING = 1.08  # m

# Offsets a paredes
OFFSET_EAST = 0.71
OFFSET_WEST = 0.68
OFFSET_NORTH = 0.51
OFFSET_SOUTH = 0.51

WORK_PLANE_Z = 0.750


def main():
    start_x = ROOM_MIN_X + OFFSET_EAST
    start_y = ROOM_MIN_Y + OFFSET_SOUTH
    end_x = start_x + (NX - 1) * SPACING
    end_y = start_y + (NY - 1) * SPACING

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w") as f:
        for ix in range(NX):
            x = start_x + ix * SPACING
            for iy in range(NY):
                y = start_y + iy * SPACING
                f.write(f"{x:.6f} {y:.6f} {WORK_PLANE_Z:.4f} 0 0 1\n")

    n = NX * NY
    print(f"Rejilla 7x9 ({n} puntos) escrita en {OUTPUT.relative_to(ROOT)}")
    print(f"  X: {start_x:.3f} a {end_x:.3f} m")
    print(f"  Y: {start_y:.3f} a {end_y:.3f} m")
    print(f"  Espaciado: {SPACING} m  |  z = {WORK_PLANE_Z} m")


if __name__ == "__main__":
    main()
