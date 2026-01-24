#!/usr/bin/env python3
"""
Create combined figure with all hours (9-17) for June 26 and November 20
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from datetime import datetime
import os

# Room and sensor grid parameters (main room only)
MIN_X = 0.558644626504064
MAX_X = 8.218644626504070
MIN_Y = -9.553275049526680
MAX_Y = -0.183275049526670
nx = 20
ny = 24

def parse_annual_ill_file(filepath):
    """Parse the annual.ill file"""
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

def datetime_to_hour_of_year(dt, year=2024):
    """
    Convert datetime to hour of year index (0-8759).

    The WEA/annual.ill format uses intervals where hour H.5 represents
    the interval from H:00 to (H+1):00, centered at H:30.

    To get illuminance AT time H:00, we use the interval ending at H:00,
    which is row (H-1) representing (H-1):00 to H:00.
    """
    start_of_year = datetime(year, 1, 1, 0, 0, 0)
    target_dt = datetime(year, dt.month, dt.day, dt.hour, 0, 0)
    delta = target_dt - start_of_year
    hour_of_year = int(delta.total_seconds() / 3600)
    return max(0, hour_of_year - 1)

def create_grid_coordinates():
    """Create X, Y meshgrid for sensor positions"""
    width = MAX_X - MIN_X
    depth = MAX_Y - MIN_Y
    spacing_x = width / (nx - 1)
    spacing_y = depth / (ny - 1)

    x_coords = []
    y_coords = []

    for ix in range(nx):
        x = MIN_X + ix * spacing_x
        for iy in range(ny):
            y = MIN_Y + iy * spacing_y
            x_coords.append(x)
            y_coords.append(y)

    return np.array(x_coords), np.array(y_coords)

def reshape_to_grid(illuminance_values, x_coords, y_coords):
    """Reshape 1D illuminance values into 2D grid"""
    x_unique = np.unique(x_coords)
    y_unique = np.unique(y_coords)
    nx_local = len(x_unique)
    ny_local = len(y_unique)

    grid = np.full((ny_local, nx_local), np.nan)

    for i, (x, y, val) in enumerate(zip(x_coords, y_coords, illuminance_values)):
        ix = np.argmin(np.abs(x_unique - x))
        iy = np.argmin(np.abs(y_unique - y))
        grid[iy, ix] = val

    return grid, x_unique, y_unique

def create_single_day_figure(data, x_coords, y_coords, month, day, label, output_file):
    """
    Create a 3x3 grid figure for a single day showing hours 9-17
    """
    hours = list(range(9, 18))  # 9 to 17
    n_rows = 3
    n_cols = 3

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 14))

    niveles = [0, 299, 500, 1000, 1500, 2000, 3000,
               4000, 5000, 6000, 7000, 8000, 10000]

    for idx, hour in enumerate(hours):
        row = idx // n_cols
        col = idx % n_cols
        ax = axes[row, col]

        # Get hour of year
        dt = datetime(2024, month, day, hour)
        hour_of_year = datetime_to_hour_of_year(dt)

        # Get illuminance values
        illuminance_values = data[hour_of_year, :]

        # Reshape to grid
        grid, x_unique, y_unique = reshape_to_grid(illuminance_values, x_coords, y_coords)

        # Create meshgrid
        XX, YY = np.meshgrid(x_unique, y_unique)
        ZZ = grid

        # Rotate 90 counter-clockwise
        Xr = -YY
        Yr = XX

        # Plot
        contour_filled = ax.contourf(Xr, Yr, ZZ, cmap='jet', alpha=0.7,
                                     levels=niveles, extend='max')
        contour_lines = ax.contour(Xr, Yr, ZZ, colors='black',
                                   levels=niveles, linewidths=0.5)
        ax.clabel(contour_lines, inline=True, fontsize=7, fmt='%g')

        ax.set_aspect('equal', adjustable='box')
        ax.tick_params(labelsize=8)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Stats
        min_lux = np.nanmin(illuminance_values)
        max_lux = np.nanmax(illuminance_values)
        mean_lux = np.nanmean(illuminance_values)

        # Title for each subplot
        ax.set_title(f'{hour}:00', fontsize=12, fontweight='bold')

        # Stats text box
        stats_text = f'Min: {min_lux:.0f}\nMax: {max_lux:.0f}\nMean: {mean_lux:.0f}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='gray'))

        # Axis labels
        if col == 0:
            ax.set_ylabel('[m]', fontsize=10)
        if row == n_rows - 1:
            ax.set_xlabel('[m]', fontsize=10)

    # Add colorbar
    fig.subplots_adjust(right=0.88, hspace=0.25, wspace=0.15)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(contour_filled, cax=cbar_ax, label='Illuminance [lux]')
    cbar.ax.tick_params(labelsize=10)

    # Main title
    fig.suptitle(f'Hourly Illuminance Maps - {label}\nTemixco, Mexico (18.85°N, 99.14°W) - Work Plane 0.75m',
                 fontsize=14, fontweight='bold', y=0.98)

    # Add orientation note
    fig.text(0.02, 0.02, 'North: ← (left)', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9))

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Figure saved to: {output_file}")
    plt.close()

def main():
    # Load data
    print("Loading annual illuminance data...")
    data = parse_annual_ill_file('results/dc/annual.ill')
    print(f"Data shape: {data.shape}")

    # Create grid coordinates
    x_coords, y_coords = create_grid_coordinates()

    os.makedirs('images', exist_ok=True)

    # Create separate figure for June 26
    print("\nGenerating June 26 grid...")
    create_single_day_figure(data, x_coords, y_coords,
                             month=6, day=26, label='June 26, 2024',
                             output_file='images/jun26_hourly_grid.png')

    # Create separate figure for November 20
    print("\nGenerating November 20 grid...")
    create_single_day_figure(data, x_coords, y_coords,
                             month=11, day=20, label='November 20, 2024',
                             output_file='images/nov20_hourly_grid.png')

    print("\nDone!")

if __name__ == '__main__':
    main()
