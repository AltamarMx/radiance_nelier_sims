#!/usr/bin/env python3
"""
Visualize validation grid annual daylighting results as hourly multi-panel figure
Creates a grid showing illuminance maps for hours 9-17 in a single image.
Based on physical luxmeter measurement grid (7×9 = 63 sensors).
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from datetime import datetime
import argparse
import sys
import os

# Validation grid parameters (from generate_sensor_grid_validation.py)
# Room dimensions
ROOM_MIN_X = 0.458644626504064   # East wall
ROOM_MAX_X = 8.31864462650407    # West wall
ROOM_MIN_Y = -9.65327504952668   # South wall (windows)
ROOM_MAX_Y = -0.0832750495266698 # North wall (windows)

# Validation grid specifications
NX = 7   # Points in X direction (east to west)
NY = 9   # Points in Y direction (north to south)
SPACING = 1.08  # Uniform spacing [m]
OFFSET_EAST = 0.71
OFFSET_SOUTH = 0.51
WORK_PLANE_Z = 0.750

# Calculate start positions
START_X = ROOM_MIN_X + OFFSET_EAST
START_Y = ROOM_MIN_Y + OFFSET_SOUTH

TOTAL_SENSORS = NX * NY  # 63


def parse_annual_ill_file(filepath):
    """
    Parse the annual.ill file
    Returns: numpy array of shape (timesteps, sensors)
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip header lines
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

    # Read illuminance data
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
    Uses interval ending at requested time.
    """
    start_of_year = datetime(year, 1, 1, 0, 0, 0)
    target_dt = datetime(year, dt.month, dt.day, dt.hour, 0, 0)
    delta = target_dt - start_of_year
    hour_of_year = int(delta.total_seconds() / 3600)
    return max(0, hour_of_year - 1)


def create_grid_coordinates():
    """Create X, Y coordinates for validation sensor positions"""
    x_coords = []
    y_coords = []

    for ix in range(NX):
        x = START_X + ix * SPACING
        for iy in range(NY):
            y = START_Y + iy * SPACING
            x_coords.append(x)
            y_coords.append(y)

    return np.array(x_coords), np.array(y_coords)


def reshape_to_grid(illuminance_values, x_coords, y_coords):
    """
    Reshape 1D illuminance values into 2D grid
    Returns: 2D array, x_unique, y_unique
    """
    x_unique = np.unique(x_coords)
    y_unique = np.unique(y_coords)

    nx = len(x_unique)
    ny = len(y_unique)

    grid = np.full((ny, nx), np.nan)

    for i, (x, y, val) in enumerate(zip(x_coords, y_coords, illuminance_values)):
        ix = np.argmin(np.abs(x_unique - x))
        iy = np.argmin(np.abs(y_unique - y))
        grid[iy, ix] = val

    return grid, x_unique, y_unique


def create_hourly_grid_figure(illuminance_data, x_coords, y_coords, date_str, output_file=None):
    """
    Create a multi-panel figure showing illuminance for hours 9-17.
    Layout: 3 rows × 3 columns for hours 9, 10, 11, 12, 13, 14, 15, 16, 17
    """
    hours = list(range(9, 18))  # 9 to 17 inclusive

    fig, axes = plt.subplots(3, 3, figsize=(18, 16))
    axes = axes.flatten()

    # Parse date
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

    # Illuminance levels
    niveles = [0, 299, 500, 1000, 1500, 2000, 3000,
               4000, 5000, 6000, 7000, 8000, 10000]

    # Create custom colormap with better visibility
    cmap = plt.cm.jet

    # Track global min/max for consistent colorbar
    global_max = 0

    for idx, hour in enumerate(hours):
        ax = axes[idx]

        # Get datetime and hour of year
        dt = datetime(date_obj.year, date_obj.month, date_obj.day, hour, 0, 0)
        hour_of_year = datetime_to_hour_of_year(dt)

        # Get illuminance values
        if hour_of_year < illuminance_data.shape[0]:
            illuminance_values = illuminance_data[hour_of_year, :]
        else:
            illuminance_values = np.zeros(len(x_coords))

        # Trim if needed
        min_count = min(len(x_coords), len(illuminance_values))
        illum = illuminance_values[:min_count]

        global_max = max(global_max, np.nanmax(illum))

        # Reshape to 2D grid
        grid, x_unique, y_unique = reshape_to_grid(illum, x_coords[:min_count], y_coords[:min_count])

        # Create meshgrid
        XX, YY = np.meshgrid(x_unique, y_unique)

        # Rotate 90° counter-clockwise: (x', y') = (-y, x) to have north face left
        Xr = -YY
        Yr = XX

        # Filled contours
        cf = ax.contourf(Xr, Yr, grid, cmap=cmap, alpha=0.7, levels=niveles, extend='max')

        # Contour lines
        cs = ax.contour(Xr, Yr, grid, colors='black', levels=niveles, linewidths=0.5)
        ax.clabel(cs, inline=True, fontsize=7, fmt='%g')

        # Plot sensor points
        x_rot = -y_coords[:min_count]
        y_rot = x_coords[:min_count]
        ax.scatter(x_rot, y_rot, c='white', s=20, edgecolors='black', linewidths=0.5, zorder=5)

        # Set title and labels
        ax.set_title(f'{hour:02d}:00', fontsize=12, fontweight='bold')
        ax.set_aspect('equal', adjustable='box')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.3)

        # Statistics
        stats_text = f'Mean: {np.nanmean(illum):.0f} lx\nMax: {np.nanmax(illum):.0f} lx'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'))

    # Add colorbar
    fig.subplots_adjust(right=0.9)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=mcolors.BoundaryNorm(niveles, cmap.N))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, label='Illuminance [lux]', extend='max')
    cbar.set_ticks(niveles)

    # Main title
    fig.suptitle(f'Validation Grid Hourly Illuminance - {date_str}\n'
                 f'Sensor Grid: {NX}×{NY} = {NX*NY} points, Spacing: {SPACING}m, Height: {WORK_PLANE_Z}m',
                 fontsize=14, fontweight='bold', y=0.98)

    # Add orientation note
    fig.text(0.5, 0.01, 'Orientation: North ← (left) | Windows on North and South walls',
             ha='center', fontsize=10, style='italic')

    plt.tight_layout(rect=[0, 0.02, 0.9, 0.95])

    if output_file:
        os.makedirs('images', exist_ok=True)
        output_path = os.path.join('images', output_file)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Visualize validation grid hourly illuminance')
    parser.add_argument('--date', type=str, required=True,
                       help='Date in YYYY-MM-DD format (e.g., 2024-06-26)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file name (saved to images/ folder)')
    parser.add_argument('--data-file', type=str, default='results/dc/annual_validation.ill',
                       help='Path to annual_validation.ill file')

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError as e:
        print(f"Error parsing date: {e}")
        sys.exit(1)

    # Load annual illuminance data
    print(f"Loading data from: {args.data_file}")
    try:
        illuminance_data = parse_annual_ill_file(args.data_file)
        print(f"Data shape: {illuminance_data.shape} (timesteps × sensors)")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    # Create grid coordinates
    x_coords, y_coords = create_grid_coordinates()
    print(f"Grid coordinates: {len(x_coords)} sensors")

    # Verify sensor count
    if illuminance_data.shape[1] != TOTAL_SENSORS:
        print(f"Warning: Expected {TOTAL_SENSORS} sensors, got {illuminance_data.shape[1]}")

    # Create visualization
    print(f"Generating hourly grid visualization for {args.date}...")
    create_hourly_grid_figure(illuminance_data, x_coords, y_coords, args.date, args.output)

    print("Done!")


if __name__ == '__main__':
    main()
