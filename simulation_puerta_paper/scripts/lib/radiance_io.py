"""
radiance_io.py — Lectores de archivos Radiance y experimentales.

Funciones:
  - parse_annual_ill_file: lee un .ill (resultado de dctimestep + rmtxop)
  - load_experimental_data: carga CSV crudos de luxómetros (klux -> lux)
  - load_radiance_data: extrae horas específicas de un .ill y reordena al grid 7x9
  - datetime_to_hour_of_year: convierte fecha/hora a índice de hora del año
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Columnas del experimento (excluyendo I5N, sensor defectuoso)
EXP_COLS = ['I1N', 'I2N', 'I3N', 'I4N', 'I1S', 'I2S', 'I3S', 'I4S', 'I5S']

# Geometría de la rejilla
NX = 7   # filas (este-oeste)
NY = 9   # columnas (norte-sur)


def parse_annual_ill_file(filepath):
    """Lee un .ill de Radiance y devuelve un array (n_horas, n_sensores).

    Salta el header generado por dctimestep/rmtxop (líneas con NCOMP, NROWS, etc.).
    """
    with open(filepath) as f:
        lines = f.readlines()

    skip_keywords = (
        '#', 'NCOMP', 'NROWS', 'NCOLS', 'FORMAT', 'SOFTWARE',
        'CAPDATE', 'GMT', 'rmtxop', 'dctimestep', 'Applied',
        'Transposed', 'LATLONG'
    )
    data_start = 0
    for i, line in enumerate(lines):
        if line.strip() and not any(line.startswith(kw) for kw in skip_keywords):
            data_start = i
            break

    rows = []
    for line in lines[data_start:]:
        if not line.strip():
            continue
        try:
            rows.append([float(x) for x in line.split()])
        except ValueError:
            continue

    return np.array(rows)


def load_experimental_data(base_path, hours, reverse_odd_hours=True):
    """Carga CSVs experimentales por hora.

    Devuelve una lista de DataFrames (una por hora), cada uno 7 filas x 9 columnas
    (orden EXP_COLS), en lux.

    - klux -> lux (multiplica por 1000)
    - Excluye I5N (sensor defectuoso)
    - Invierte filas en horas impares para alinear con el sistema de coordenadas
    """
    base = Path(base_path)
    dfs = []
    for hour in hours:
        f = base / f"{hour:02d}h.csv"
        df = pd.read_csv(f)
        if reverse_odd_hours and hour % 2 == 1:
            df = df[::-1].reset_index(drop=True)
        dfs.append(df[EXP_COLS] * 1000.0)
    return dfs


def datetime_to_hour_of_year(month, day, hour, year=2024):
    """Convierte (mes, dia, hora) a índice 0-based de hora del año."""
    start = datetime(year, 1, 1)
    target = datetime(year, month, day, hour)
    return max(0, int((target - start).total_seconds() / 3600) - 1)


def load_radiance_data(ill_file, month, day, hours):
    """Extrae las horas pedidas de un .ill, reformatea a 7x9 y mapea a EXP_COLS.

    Devuelve una lista de DataFrames (una por hora), 7 filas x 9 columnas, en lux.
    El reordenamiento [::-1, ::-1] alinea con el sistema de coordenadas del experimento.
    """
    annual = parse_annual_ill_file(ill_file)
    dfs = []
    for hour in hours:
        idx = datetime_to_hour_of_year(month, day, hour)
        illum_1d = annual[idx, :]
        illum_2d = illum_1d.reshape(NX, NY)
        illum_matched = illum_2d[::-1, ::-1]
        dfs.append(pd.DataFrame(illum_matched, columns=EXP_COLS))
    return dfs
