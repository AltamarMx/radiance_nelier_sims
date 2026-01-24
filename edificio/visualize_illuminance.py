#!/usr/bin/env python3
"""
Visualize annual daylighting simulation results
Generates illuminance maps for specific dates and times
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from datetime import datetime, timedelta
import argparse
import sys
import os

# Room and sensor grid parameters (main room only)
# Main room with 0.1m wall offset
MIN_X = 0.558644626504064
MAX_X = 8.218644626504070
MIN_Y = -9.553275049526680
MAX_Y = -0.183275049526670
GRID_SPACING = 0.405  # Approximately equidistant (0.403 x 0.407 m)
WORK_PLANE_Z = 0.750

# Calculate grid dimensions
nx = 20  # X direction
ny = 24  # Y direction
total_sensors = 480  # Main room only, 10cm wall offset

def parse_annual_ill_file(filepath):
    """
    Parse the annual.ill file
    Returns: numpy array of shape (timesteps, sensors)
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip header lines - look for lines that start with metadata keywords or special characters
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
        if not is_header and line.strip():  # Found first data line
            data_start = i
            break

    # Read illuminance data
    data = []
    for line in lines[data_start:]:
        if line.strip():
            try:
                values = [float(x) for x in line.split()]
                if len(values) > 0:  # Only add non-empty lines
                    data.append(values)
            except ValueError:
                # Skip lines that can't be converted to floats
                continue

    return np.array(data)

def datetime_to_hour_of_year(dt, year=2024):
    """
    Convert datetime to hour of year index (0-8759).

    The WEA/annual.ill format uses intervals where hour H.5 represents
    the interval from H:00 to (H+1):00, centered at H:30.

    To get illuminance AT time H:00, we use the interval ending at H:00,
    which is row (H-1) representing (H-1):00 to H:00.

    Example: For 12:00, we want row 11 (interval 11:00-12:00, centered at 11:30)
    """
    start_of_year = datetime(year, 1, 1, 0, 0, 0)
    target_dt = datetime(year, dt.month, dt.day, dt.hour, 0, 0)
    delta = target_dt - start_of_year
    hour_of_year = int(delta.total_seconds() / 3600)
    # Subtract 1 to get the interval ENDING at the requested time
    return max(0, hour_of_year - 1)

def create_grid_coordinates():
    """Create X, Y meshgrid for sensor positions matching the actual grid generation"""
    # Match the actual grid generation from generate_sensor_grid.py
    width = MAX_X - MIN_X
    depth = MAX_Y - MIN_Y

    # Actual spacing used (from grid generation)
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
    """
    Reshape 1D illuminance values into 2D grid
    Returns: 2D array, x_unique, y_unique
    """
    # Get unique x and y values
    x_unique = np.unique(x_coords)
    y_unique = np.unique(y_coords)

    nx = len(x_unique)
    ny = len(y_unique)

    # Create 2D grid
    grid = np.full((ny, nx), np.nan)

    # Fill grid with illuminance values
    for i, (x, y, val) in enumerate(zip(x_coords, y_coords, illuminance_values)):
        ix = np.argmin(np.abs(x_unique - x))
        iy = np.argmin(np.abs(y_unique - y))
        grid[iy, ix] = val

    return grid, x_unique, y_unique

def visualize_illuminance(illuminance_values, x_coords, y_coords, date_str, time_str, output_file=None):
    """
    Create illuminance contour visualization with north facing left
    """
    # Reshape data to 2D grid
    grid, x_unique, y_unique = reshape_to_grid(illuminance_values, x_coords, y_coords)

    fig, ax = plt.subplots(figsize=(14, 12))

    # Create meshgrid
    XX, YY = np.meshgrid(x_unique, y_unique)
    ZZ = grid

    # Rotate 90° counter-clockwise: (x', y') = (-y, x)
    # This makes north face left instead of up
    Xr = -YY
    Yr = XX

    # Illuminance levels (from user specification)
    niveles = [0, 299, 500, 1000, 1500, 2000, 3000,
               4000, 5000, 6000, 7000, 8000, 10000]

    # Filled contours with jet colormap
    contour_filled = ax.contourf(Xr, Yr, ZZ, cmap='jet', alpha=0.7, levels=niveles, extend='max')

    # Contour lines with labels
    contour_lines = ax.contour(Xr, Yr, ZZ, colors='black', levels=niveles, linewidths=0.8)
    ax.clabel(contour_lines, inline=True, fontsize=9, fmt='%g')

    # Add colorbar
    cbar = plt.colorbar(contour_filled, ax=ax, label='Iluminancia [lx]', pad=0.02)
    cbar.ax.tick_params(labelsize=11)

    # Set labels and title
    ax.set_xlabel('[m]', fontsize=13, fontweight='bold')
    ax.set_ylabel('[m]', fontsize=13, fontweight='bold')
    ax.set_title(f'Illuminance Map - {date_str} at {time_str}',
                 fontsize=15, fontweight='bold', pad=20)

    # Set aspect ratio
    ax.set_aspect('equal', adjustable='box')

    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Add statistics text box
    valid_values = illuminance_values[~np.isnan(illuminance_values)]
    if len(valid_values) > 0:
        stats_text = f'Min: {np.nanmin(illuminance_values):.1f} lx\n'
        stats_text += f'Max: {np.nanmax(illuminance_values):.1f} lx\n'
        stats_text += f'Mean: {np.nanmean(illuminance_values):.1f} lx\n'
        stats_text += f'Median: {np.nanmedian(illuminance_values):.1f} lx'
    else:
        stats_text = 'No illuminance data\n(nighttime or no sun)'

    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=2))

    # Add work plane info with orientation note
    info_text = f'Work plane: {WORK_PLANE_Z}m\n'
    info_text += f'Grid spacing: ~{GRID_SPACING:.2f}m\n'
    info_text += f'Sensors: {len(illuminance_values)}\n'
    info_text += f'North: ← (left)'

    ax.text(0.98, 0.02, info_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.9, edgecolor='black', linewidth=2))

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to: {output_file}")
    else:
        plt.show()

    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Visualize annual daylighting simulation results')
    parser.add_argument('--date', type=str, required=True,
                       help='Date in YYYY-MM-DD format (e.g., 2024-06-21)')
    parser.add_argument('--time', type=str, required=True,
                       help='Time in HH:MM format (e.g., 12:00)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file name (saved to images/ folder, optional)')
    parser.add_argument('--data-file', type=str, default='results/dc/annual.ill',
                       help='Path to annual.ill file (default: results/dc/annual.ill)')

    args = parser.parse_args()

    # Parse date and time
    try:
        date_obj = datetime.strptime(args.date, '%Y-%m-%d')
        time_obj = datetime.strptime(args.time, '%H:%M').time()
        dt = datetime.combine(date_obj.date(), time_obj)
    except ValueError as e:
        print(f"Error parsing date/time: {e}")
        sys.exit(1)

    # Calculate hour of year
    hour_of_year = datetime_to_hour_of_year(dt)
    print(f"Requested: {args.date} at {args.time}")
    print(f"Hour of year: {hour_of_year} (0-8759)")

    # Load annual illuminance data
    print(f"Loading data from: {args.data_file}")
    try:
        illuminance_data = parse_annual_ill_file(args.data_file)
        print(f"Data shape: {illuminance_data.shape} (timesteps × sensors)")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    # Check if hour_of_year is valid
    if hour_of_year >= illuminance_data.shape[0]:
        print(f"Error: Hour {hour_of_year} exceeds available data ({illuminance_data.shape[0]} timesteps)")
        sys.exit(1)

    # Get illuminance values for the requested time
    illuminance_values = illuminance_data[hour_of_year, :]
    print(f"Illuminance range: {illuminance_values.min():.2f} - {illuminance_values.max():.2f} lux")

    # Create grid coordinates
    x_coords, y_coords = create_grid_coordinates()

    # Verify sensor count
    if len(x_coords) != illuminance_values.shape[0]:
        print(f"Warning: Sensor count mismatch ({len(x_coords)} coords vs {illuminance_values.shape[0]} values)")
        # Trim to match
        min_count = min(len(x_coords), illuminance_values.shape[0])
        x_coords = x_coords[:min_count]
        y_coords = y_coords[:min_count]
        illuminance_values = illuminance_values[:min_count]

    # Create visualization
    print("Generating visualization...")
    output_file = None
    if args.output:
        os.makedirs('images', exist_ok=True)
        output_file = os.path.join('images', args.output)
    visualize_illuminance(illuminance_values, x_coords, y_coords,
                         args.date, args.time, output_file)

    print("Done!")

if __name__ == '__main__':
    main()
