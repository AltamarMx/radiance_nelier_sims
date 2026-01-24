#!/usr/bin/env python3
"""
Generate sensor grid for Radiance daylighting simulation
Main room only with 10cm wall offset
Equidistant sensor spacing
"""

# Main room dimensions (from PISO-CONCRETO-PULIDOIER floor polygon)
# Floor corners: (0.459, -9.653) to (8.319, -0.083)
room_min_x = 0.458644626504064
room_max_x = 8.31864462650407
room_min_y = -9.65327504952668
room_max_y = -0.0832750495266698

# Wall offset (10 cm = 0.1 m)
wall_offset = 0.1

# Calculate usable area with wall offset
min_x = room_min_x + wall_offset
max_x = room_max_x - wall_offset
min_y = room_min_y + wall_offset
max_y = room_max_y - wall_offset

# Calculate room dimensions
width = max_x - min_x
depth = max_y - min_y

print(f"Main room dimensions:")
print(f"  Width (X): {width:.3f} m")
print(f"  Depth (Y): {depth:.3f} m")
print(f"  Area: {width * depth:.2f} m²")
print(f"\nUsable area with {wall_offset}m wall offset:")
print(f"  X range: {min_x:.3f} to {max_x:.3f} m")
print(f"  Y range: {min_y:.3f} to {max_y:.3f} m")

# Find optimal equidistant spacing
# Try different spacings and pick the one closest to 0.5m that fits well
spacings_to_try = [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
best_spacing = None
best_fit_score = float('inf')

for spacing in spacings_to_try:
    nx = int(width / spacing) + 1
    ny = int(depth / spacing) + 1

    # Calculate actual spacing needed
    actual_spacing_x = width / (nx - 1) if nx > 1 else width
    actual_spacing_y = depth / (ny - 1) if ny > 1 else depth

    # How different is X spacing from Y spacing? (want them equal)
    fit_score = abs(actual_spacing_x - actual_spacing_y)

    if fit_score < best_fit_score:
        best_fit_score = fit_score
        best_spacing = spacing
        best_nx = nx
        best_ny = ny
        best_actual_x = actual_spacing_x
        best_actual_y = actual_spacing_y

# Use the best spacing found
nx = best_nx
ny = best_ny
spacing_x = best_actual_x
spacing_y = best_actual_y

print(f"\nOptimal equidistant grid:")
print(f"  Nominal spacing: ~{best_spacing:.2f} m")
print(f"  Actual spacing X: {spacing_x:.4f} m")
print(f"  Actual spacing Y: {spacing_y:.4f} m")
print(f"  Spacing difference: {abs(spacing_x - spacing_y)*1000:.2f} mm")
print(f"  Grid: {nx} × {ny} = {nx * ny} sensors")
print(f"  Sensor density: {(width * depth) / (nx * ny):.3f} m²/sensor")

# Work plane height (0.75m above floor)
work_plane_z = 0.750

# Generate grid points with calculated spacing
grid_points = []

for ix in range(nx):
    x = min_x + ix * spacing_x
    for iy in range(ny):
        y = min_y + iy * spacing_y
        # Format: x y z dx dy dz (direction vector pointing up)
        grid_points.append(f"{x:.6f} {y:.6f} {work_plane_z:.4f} 0 0 1")

# Write to points.txt
output_file = "points.txt"
with open(output_file, 'w') as f:
    for point in grid_points:
        f.write(point + '\n')

print(f"\n✓ Generated {len(grid_points)} sensor points")
print(f"✓ Work plane height: {work_plane_z}m")
print(f"✓ Output file: {output_file}")
print(f"\nGrid layout:")
print(f"  Rows (Y direction): {ny} sensors, spacing {spacing_y:.4f}m")
print(f"  Columns (X direction): {nx} sensors, spacing {spacing_x:.4f}m")
print(f"  Coverage: Main room only (PISO-CONCRETO-PULIDOIER)")
print(f"  Wall clearance: {wall_offset*100:.0f} cm on all sides")
