# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# %%
# Load Radiance validation simulation results
data_file = "../edificio/results/dc/annual_validation.ill"

def parse_annual_ill_file(filepath):
    """Parse the annual.ill file, skip header lines"""
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

def datetime_to_hour_of_year(month, day, hour, year=2024):
    """Convert date/time to hour of year index (0-8759)"""
    start_of_year = datetime(year, 1, 1, 0, 0, 0)
    target_dt = datetime(year, month, day, hour, 0, 0)
    delta = target_dt - start_of_year
    hour_of_year = int(delta.total_seconds() / 3600)
    # Use interval ending at requested time
    return max(0, hour_of_year - 1)

# Load all annual data
print("Loading Radiance validation data...")
radiance_data = parse_annual_ill_file(data_file)
print(f"Data shape: {radiance_data.shape}")

# %%
# Validation grid parameters
NX = 7   # Points in X direction (east to west) - corresponds to Y axis in plot
NY = 9   # Points in Y direction (south to north) - corresponds to X axis in plot

# Extract data for June 26, hours 9-17
horas = ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]

dataframes_por_hora = []

for hour in hours:
    hour_idx = datetime_to_hour_of_year(6, 26, hour)
    illum_1d = radiance_data[hour_idx, :]

    # Reshape from 1D (63) to 2D (7x9)
    # Data is ordered: for each X (7), iterate Y (9)
    # So shape is (NX, NY) = (7, 9) when reshaped with order='C'
    illum_2d = illum_1d.reshape(NX, NY)

    # The experimental data has shape (7, 9) where:
    # - rows (7) = Y positions (lines from pizarron/east to back/west)
    # - cols (9) = X positions (sensors from north to south)
    #
    # Radiance grid:
    # - illum_2d[ix, iy] where ix=0..6 (east to west), iy=0..8 (south to north)
    #
    # To match experimental format:
    # - experimental row i (Y) = radiance ix (X direction)
    # - experimental col j (X) = radiance iy (Y direction), but reversed (N to S vs S to N)
    #
    # So we need: result[ix, :] = illum_2d[ix, ::-1]  (reverse Y to go N to S)
    illum_matched = illum_2d[:, ::-1]  # Reverse columns to match N to S direction

    df = pd.DataFrame(illum_matched)
    dataframes_por_hora.append(df)
    print(f"Hour {hour}:00 - idx {hour_idx} - mean: {illum_1d.mean():.0f} lux")

# %%
# Plot settings (same as experimental)
niveles = [0, 299, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000]

# Grid positions (same as experimental)
distancia_muro_norte = 0.51
distancia_entre_sensores = 1.08
distancia_pizarron = 0.71
distancia_entre_lineas = 1.08

# X positions (9 sensors, north to south direction)
x_positions = [distancia_muro_norte + i * distancia_entre_sensores for i in range(9)]

# Y positions (7 lines, from pizarron/east to back/west)
y_positions = [distancia_pizarron + i * distancia_entre_lineas for i in range(7)]

# Create figure (same layout as experimental)
fig, axes = plt.subplots(3, 3, figsize=(18, 12), sharex=True, sharey=True)

for i, (df, hora) in enumerate(zip(dataframes_por_hora, horas)):
    ax = axes[i // 3, i % 3]

    # Create meshgrid
    X, Y = np.meshgrid(x_positions, y_positions)
    Z = df.values[::-1, :].astype(float)  # Flip vertically (mirror on x-axis)

    # Plot contours
    contour_filled = ax.contourf(X, Y, Z, cmap='jet', alpha=0.7, levels=niveles)
    contour = ax.contour(X, Y, Z, colors='black', levels=niveles)
    ax.clabel(contour, inline=True, fontsize=8)

    # Configure subplot
    ax.set_aspect(aspect='auto')
    ax.set_title(f'{hora}')
    ax.set_xticks(x_positions)
    ax.set_yticks(y_positions)
    ax.invert_yaxis()

# Add axis labels
for i in range(3):
    axes[2, i].set_xlabel('[m]')
    axes[i, 0].set_ylabel('[m]')

# Add colorbar
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
fig.colorbar(contour_filled, cax=cbar_ax, label='Iluminancia [lx]')

plt.suptitle('Radiance Simulation - June 26', fontsize=14, fontweight='bold', y=0.98)
plt.savefig('../edificio/images/002_26jun_radiance.png', dpi=300, bbox_inches='tight')
plt.show()

# %%
dataframes_por_hora
# %%
