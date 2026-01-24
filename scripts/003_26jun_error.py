# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# %%
# =============================================================================
# Load Experimental Data (from 001_26jun_exp.py)
# =============================================================================
cols_map = ['I1N', 'I2N', 'I3N', 'I4N', 'I1S', 'I2S', 'I3S', 'I4S', 'I5S']

f = "../data/experimental/005_26Junio/09h.csv"
nueve = pd.read_csv(f)
nueve = nueve[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/10h.csv'
diez = pd.read_csv(f)

f = '../data/experimental/005_26Junio/11h.csv'
once = pd.read_csv(f)
once = once[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/12h.csv'
doce = pd.read_csv(f)

f = '../data/experimental/005_26Junio/13h.csv'
trece = pd.read_csv(f)
trece = trece[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/14h.csv'
catorce = pd.read_csv(f)

f = '../data/experimental/005_26Junio/15h.csv'
quince = pd.read_csv(f)
quince = quince[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/16h.csv'
dieciseis = pd.read_csv(f)

f = '../data/experimental/005_26Junio/17h.csv'
diecisiete = pd.read_csv(f)
diecisiete = diecisiete[::-1].reset_index(drop=True)

# Experimental dataframes (in klux, need to multiply by 1000)
exp_dataframes = [nueve[cols_map],
                  diez[cols_map],
                  once[cols_map],
                  doce[cols_map],
                  trece[cols_map],
                  catorce[cols_map],
                  quince[cols_map],
                  dieciseis[cols_map],
                  diecisiete[cols_map]]

# Convert to lux
exp_dataframes_lux = [df * 1000 for df in exp_dataframes]

# %%
# =============================================================================
# Load Radiance Data (from 002_26jun_radiance.py)
# =============================================================================
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
    return max(0, hour_of_year - 1)

# Load Radiance data
radiance_data = parse_annual_ill_file(data_file)

# Grid parameters
NX = 7   # Points in X direction (east to west)
NY = 9   # Points in Y direction (south to north)

# Extract Radiance data for June 26, hours 9-17
hours = [9, 10, 11, 12, 13, 14, 15, 16, 17]
rad_dataframes = []

for hour in hours:
    hour_idx = datetime_to_hour_of_year(6, 26, hour)
    illum_1d = radiance_data[hour_idx, :]
    illum_2d = illum_1d.reshape(NX, NY)
    # Reverse Y direction to match N to S (same as experimental)
    illum_matched = illum_2d[:, ::-1]
    df = pd.DataFrame(illum_matched, columns=cols_map)
    rad_dataframes.append(df)

# %%
# =============================================================================
# Calculate Error (Radiance - Experimental)
# =============================================================================
horas = ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]

error_dataframes = []
for exp_df, rad_df in zip(exp_dataframes_lux, rad_dataframes):
    error = rad_df.values - exp_df.values
    error_dataframes.append(pd.DataFrame(error, columns=cols_map))

# Print error statistics
print("Error Statistics (Radiance - Experimental) [lux]:")
print("-" * 60)
for hora, err_df in zip(horas, error_dataframes):
    err = err_df.values
    print(f"{hora}: Mean={err.mean():+8.1f}, Std={err.std():7.1f}, "
          f"Min={err.min():+8.1f}, Max={err.max():+8.1f}")

# %%
# =============================================================================
# Plot Error
# =============================================================================
# Error levels (symmetric around 0)
niveles_error = [-5000, -3000, -2000, -1000, -500, 0, 500, 1000, 2000, 3000, 5000]

# Grid positions (same as experimental)
distancia_muro_norte = 0.51
distancia_entre_sensores = 1.08
distancia_pizarron = 0.71
distancia_entre_lineas = 1.08

x_positions = [distancia_muro_norte + i * distancia_entre_sensores for i in range(9)]
y_positions = [distancia_pizarron + i * distancia_entre_lineas for i in range(7)]

# Create figure
fig, axes = plt.subplots(3, 3, figsize=(18, 12), sharex=True, sharey=True)

# Diverging colormap (blue=negative, white=zero, red=positive)
cmap = 'RdBu_r'

for i, (df, hora) in enumerate(zip(error_dataframes, horas)):
    ax = axes[i // 3, i % 3]

    X, Y = np.meshgrid(x_positions, y_positions)
    Z = df.values.astype(float)

    # Plot contours
    contour_filled = ax.contourf(X, Y, Z, cmap=cmap, alpha=0.7, levels=niveles_error, extend='both')
    contour = ax.contour(X, Y, Z, colors='black', levels=niveles_error, linewidths=0.5)
    ax.clabel(contour, inline=True, fontsize=7)

    # Zero contour line (thicker)
    ax.contour(X, Y, Z, colors='black', levels=[0], linewidths=2)

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
cbar = fig.colorbar(contour_filled, cax=cbar_ax, label='Error (Radiance - Exp) [lx]')

plt.suptitle('Error: Radiance - Experimental | June 26', fontsize=14, fontweight='bold', y=0.98)
plt.savefig('../edificio/images/003_26jun_error.png', dpi=300, bbox_inches='tight')
plt.show()

# %%
# =============================================================================
# Summary Statistics
# =============================================================================
all_errors = np.concatenate([df.values.flatten() for df in error_dataframes])
print("\nOverall Error Statistics:")
print(f"  Mean Bias (MBE): {all_errors.mean():+.1f} lux")
print(f"  Std Dev: {all_errors.std():.1f} lux")
print(f"  RMSE: {np.sqrt((all_errors**2).mean()):.1f} lux")
print(f"  Range: {all_errors.min():+.1f} to {all_errors.max():+.1f} lux")

# Percentage error (relative to experimental mean)
exp_all = np.concatenate([df.values.flatten() for df in exp_dataframes_lux])
print(f"\nRelative Metrics:")
print(f"  Exp Mean: {exp_all.mean():.1f} lux")
print(f"  MBE %: {100 * all_errors.mean() / exp_all.mean():+.1f}%")
print(f"  CV(RMSE): {100 * np.sqrt((all_errors**2).mean()) / exp_all.mean():.1f}%")

# %%
