# %%
"""
Diagnostic script to verify data alignment between experimental and radiance data.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# %%
# =============================================================================
# Load raw data without manipulation to understand structure
# =============================================================================

# Load experimental CSV for 12h (NOT reversed)
exp_12h_raw = pd.read_csv("../data/experimental/005_26Junio/12h.csv")
cols_map = ['I1N', 'I2N', 'I3N', 'I4N', 'I1S', 'I2S', 'I3S', 'I4S', 'I5S']

print("Experimental 12h raw data (values in klux):")
print(exp_12h_raw[cols_map].round(2))
print("\nRow 0 (first row in CSV):")
print(exp_12h_raw[cols_map].iloc[0].round(2).to_dict())
print("\nRow 6 (last row in CSV):")
print(exp_12h_raw[cols_map].iloc[6].round(2).to_dict())

# %%
# Load radiance points to understand ordering
points = np.loadtxt("../edificio/points_validation.txt")
print("\nRadiance sensor points (X, Y, Z):")
print(f"Points 1-9 (first line): X={points[0:9, 0].mean():.2f}, Y range: {points[0:9, 1].min():.2f} to {points[0:9, 1].max():.2f}")
print(f"Points 55-63 (last line): X={points[54:63, 0].mean():.2f}, Y range: {points[54:63, 1].min():.2f} to {points[54:63, 1].max():.2f}")

# %%
# Load radiance illuminance data for 12h
def parse_annual_ill_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    skip_keywords = ['#', 'NCOMP', 'NROWS', 'NCOLS', 'FORMAT', 'SOFTWARE',
                     'CAPDATE', 'GMT', 'rmtxop', 'dctimestep', 'Applied',
                     'Transposed', 'LATLONG']

    data_start = 0
    for i, line in enumerate(lines):
        is_header = any(line.startswith(kw) for kw in skip_keywords)
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
    start = datetime(year, 1, 1)
    target = datetime(year, month, day, hour)
    return max(0, int((target - start).total_seconds() / 3600) - 1)

radiance_data = parse_annual_ill_file("../edificio/results/dc/annual_validation.ill")
hour_idx = datetime_to_hour_of_year(6, 26, 12)
rad_12h_1d = radiance_data[hour_idx, :]

print(f"\nRadiance 12h data: {len(rad_12h_1d)} points, hour index {hour_idx}")

# Reshape to 7x9 (no manipulation)
rad_12h_2d = rad_12h_1d.reshape(7, 9)
print("\nRadiance 12h reshaped (7 lines x 9 sensors), NO manipulation:")
print(f"Row 0 (X=1.17, pizarron/east): {rad_12h_2d[0, :].round(0)}")
print(f"Row 6 (X=7.65, back/west): {rad_12h_2d[6, :].round(0)}")

# %%
# =============================================================================
# Visual comparison - plot both data sources for 12h
# =============================================================================

# Grid positions
distancia_muro_norte = 0.51
distancia_entre_sensores = 1.08
distancia_pizarron = 0.71
distancia_entre_lineas = 1.08

x_positions = [distancia_muro_norte + i * distancia_entre_sensores for i in range(9)]
y_positions = [distancia_pizarron + i * distancia_entre_lineas for i in range(7)]

niveles = [0, 299, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000]

fig, axes = plt.subplots(2, 3, figsize=(14, 8))

# Experimental raw (no flip)
ax = axes[0, 0]
X, Y = np.meshgrid(x_positions, y_positions)
Z = exp_12h_raw[cols_map].values * 1000
cf = ax.contourf(X, Y, Z, cmap='jet', levels=niveles)
ax.contour(X, Y, Z, colors='black', levels=niveles, linewidths=0.5)
ax.set_title('Exp 12h - RAW (no flip)')
ax.invert_yaxis()
ax.set_aspect('equal')

# Experimental reversed
ax = axes[0, 1]
Z = exp_12h_raw[cols_map].values[::-1, :] * 1000
cf = ax.contourf(X, Y, Z, cmap='jet', levels=niveles)
ax.contour(X, Y, Z, colors='black', levels=niveles, linewidths=0.5)
ax.set_title('Exp 12h - rows REVERSED')
ax.invert_yaxis()
ax.set_aspect('equal')

# Radiance raw (no manipulation)
ax = axes[1, 0]
Z = rad_12h_2d
cf = ax.contourf(X, Y, Z, cmap='jet', levels=niveles)
ax.contour(X, Y, Z, colors='black', levels=niveles, linewidths=0.5)
ax.set_title('Rad 12h - RAW reshape(7,9)')
ax.invert_yaxis()
ax.set_aspect('equal')

# Radiance with column reversal (N to S)
ax = axes[1, 1]
Z = rad_12h_2d[:, ::-1]
cf = ax.contourf(X, Y, Z, cmap='jet', levels=niveles)
ax.contour(X, Y, Z, colors='black', levels=niveles, linewidths=0.5)
ax.set_title('Rad 12h - cols REVERSED')
ax.invert_yaxis()
ax.set_aspect('equal')

# Radiance with both reversals
ax = axes[1, 2]
Z = rad_12h_2d[::-1, ::-1]
cf = ax.contourf(X, Y, Z, cmap='jet', levels=niveles)
ax.contour(X, Y, Z, colors='black', levels=niveles, linewidths=0.5)
ax.set_title('Rad 12h - BOTH reversed')
ax.invert_yaxis()
ax.set_aspect('equal')

# Hide unused subplot
axes[0, 2].axis('off')

plt.tight_layout()
plt.savefig('../edificio/images/005_diagnostic.png', dpi=150, bbox_inches='tight')
plt.show()

# %%
# =============================================================================
# Find best alignment by comparing patterns
# =============================================================================
print("\n" + "="*60)
print("ALIGNMENT CHECK - Comparing corner values")
print("="*60)

exp_vals = exp_12h_raw[cols_map].values * 1000

# Experimental corners (in klux converted to lux)
print("\nExperimental 12h (raw CSV order):")
print(f"  Top-left (row0, I1N): {exp_vals[0, 0]:.0f} lux")
print(f"  Top-right (row0, I5S): {exp_vals[0, 8]:.0f} lux")
print(f"  Bottom-left (row6, I1N): {exp_vals[6, 0]:.0f} lux")
print(f"  Bottom-right (row6, I5S): {exp_vals[6, 8]:.0f} lux")

# Radiance corners (various manipulations)
print("\nRadiance 12h - RAW reshape(7,9):")
print(f"  Row0-Col0: {rad_12h_2d[0, 0]:.0f} lux")
print(f"  Row0-Col8: {rad_12h_2d[0, 8]:.0f} lux")
print(f"  Row6-Col0: {rad_12h_2d[6, 0]:.0f} lux")
print(f"  Row6-Col8: {rad_12h_2d[6, 8]:.0f} lux")

print("\nRadiance 12h - cols reversed [:, ::-1]:")
rad_col_rev = rad_12h_2d[:, ::-1]
print(f"  Row0-Col0: {rad_col_rev[0, 0]:.0f} lux")
print(f"  Row0-Col8: {rad_col_rev[0, 8]:.0f} lux")
print(f"  Row6-Col0: {rad_col_rev[6, 0]:.0f} lux")
print(f"  Row6-Col8: {rad_col_rev[6, 8]:.0f} lux")

# %%
# =============================================================================
# Check if experimental rows are in reverse order
# =============================================================================
print("\n" + "="*60)
print("ROW ORDER CHECK")
print("="*60)

# If pizarron (east) is closest to windows, we expect HIGH illuminance there
# Let's see which row has higher mean illuminance
print("\nExperimental mean illuminance per row:")
for i in range(7):
    print(f"  Row {i}: {exp_vals[i, :].mean():.0f} lux")

print("\nRadiance mean illuminance per row (raw):")
for i in range(7):
    print(f"  Row {i}: {rad_12h_2d[i, :].mean():.0f} lux")

# %%
