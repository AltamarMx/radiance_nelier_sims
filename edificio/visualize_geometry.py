#!/usr/bin/env python3
"""
Visualize the building geometry to understand the layout.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Main room floor boundaries
main_x_min, main_x_max = 0.259, 8.519
main_y_min, main_y_max = -9.853, 0.117

# Corridor boundaries
corr_x_min, corr_x_max = -2.741, 11.519
corr_y_min, corr_y_max = -13.503, -9.853

# Window locations (from glazing.geom)
# North wall windows (y ≈ 0.117)
north_windows = [
    (1.060, 6.558),  # X range
]

# South wall windows (y ≈ -9.853)
south_windows = [
    (1.060, 6.558),  # X range
]

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(14, 10))

# Draw corridor
corridor = patches.Rectangle(
    (corr_x_min, corr_y_min),
    corr_x_max - corr_x_min,
    corr_y_max - corr_y_min,
    linewidth=2,
    edgecolor='blue',
    facecolor='lightblue',
    alpha=0.3,
    label='Corridor (PISO-PASILLOIER)'
)
ax.add_patch(corridor)

# Draw main room
main_room = patches.Rectangle(
    (main_x_min, main_y_min),
    main_x_max - main_x_min,
    main_y_max - main_y_min,
    linewidth=2,
    edgecolor='red',
    facecolor='lightyellow',
    alpha=0.5,
    label='Main Room (PISO-CONCRETO-PULIDOIER)'
)
ax.add_patch(main_room)

# Draw windows on north wall (y ≈ 0.117)
for x_start, x_end in north_windows:
    window = patches.Rectangle(
        (x_start, 0.117 - 0.05),
        x_end - x_start,
        0.1,
        linewidth=1,
        edgecolor='cyan',
        facecolor='lightcyan',
        alpha=0.7
    )
    ax.add_patch(window)

# Draw windows on south wall (y ≈ -9.853)
for x_start, x_end in south_windows:
    window = patches.Rectangle(
        (x_start, -9.853 - 0.05),
        x_end - x_start,
        0.1,
        linewidth=1,
        edgecolor='cyan',
        facecolor='lightcyan',
        alpha=0.7
    )
    ax.add_patch(window)

# Recommended sensor grid (main room with 0.5m offset)
offset = 0.5
grid_x_min = main_x_min + offset
grid_x_max = main_x_max - offset
grid_y_min = main_y_min + offset
grid_y_max = main_y_max - offset

sensor_grid = patches.Rectangle(
    (grid_x_min, grid_y_min),
    grid_x_max - grid_x_min,
    grid_y_max - grid_y_min,
    linewidth=2,
    edgecolor='green',
    facecolor='none',
    linestyle='--',
    label='Recommended Sensor Grid (0.5m offset)'
)
ax.add_patch(sensor_grid)

# Add dimensions
ax.text((main_x_min + main_x_max) / 2, main_y_min - 0.5,
        f'{main_x_max - main_x_min:.2f}m', ha='center', fontsize=10, weight='bold')
ax.text(main_x_min - 0.5, (main_y_min + main_y_max) / 2,
        f'{main_y_max - main_y_min:.2f}m', ha='right', va='center', fontsize=10, weight='bold', rotation=90)

ax.text((corr_x_min + corr_x_max) / 2, corr_y_min - 0.5,
        f'{corr_x_max - corr_x_min:.2f}m', ha='center', fontsize=10, color='blue')
ax.text(corr_x_min - 0.5, (corr_y_min + corr_y_max) / 2,
        f'{corr_y_max - corr_y_min:.2f}m', ha='right', va='center', fontsize=10, color='blue', rotation=90)

# Labels
ax.text((main_x_min + main_x_max) / 2, (main_y_min + main_y_max) / 2,
        'MAIN ROOM\n8.26m × 9.97m\n82.4 m²',
        ha='center', va='center', fontsize=12, weight='bold', color='darkred')

ax.text((corr_x_min + corr_x_max) / 2, (corr_y_min + corr_y_max) / 2,
        'CORRIDOR\n14.26m × 3.65m',
        ha='center', va='center', fontsize=10, color='darkblue')

ax.text((grid_x_min + grid_x_max) / 2, grid_y_max + 0.3,
        'Sensor Grid: 7.26m × 8.97m\n~238 sensors @ 0.5m spacing',
        ha='center', va='bottom', fontsize=9, color='green', weight='bold')

# Add window labels
ax.text(3.8, 0.5, 'North Windows', ha='center', fontsize=9, color='cyan', style='italic')
ax.text(3.8, -10.2, 'South Windows', ha='center', fontsize=9, color='cyan', style='italic')

# Set axis properties
ax.set_xlim(-3.5, 12.5)
ax.set_ylim(-14.5, 1.5)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.set_xlabel('X (meters)', fontsize=11)
ax.set_ylabel('Y (meters)', fontsize=11)
ax.set_title('Building Layout Analysis\nFloor Plan with Recommended Sensor Grid', fontsize=14, weight='bold')
ax.legend(loc='upper right', fontsize=9)

# Add coordinate reference
ax.plot(0, 0, 'ko', markersize=8, label='Origin (0,0)')
ax.text(0.2, 0.2, '(0,0)', fontsize=8)

plt.tight_layout()
plt.savefig('/Users/gbv/radiance_claude/edificio/floor_layout.png', dpi=150, bbox_inches='tight')
print("Floor layout visualization saved to: /Users/gbv/radiance_claude/edificio/floor_layout.png")

# Print summary
print("\n" + "="*80)
print("GEOMETRY ANALYSIS SUMMARY")
print("="*80)
print("\nYOUR ORIGINAL SENSOR GRID (from bounding box of all geometry):")
print(f"  X: -2.741 to 11.519 m (14.26m)")
print(f"  Y: -13.503 to 0.117 m (13.62m)")
print(f"  This includes: Main room + Corridor + exterior space")
print(f"  Estimated sensors: ~29 × 28 = 812 sensors")

print("\nACTUAL INTERIOR SPACES:")
print(f"  Main Room: 8.26m × 9.97m = 82.4 m²")
print(f"  Corridor: 14.26m × 3.65m = 52.0 m² (but mostly exterior/structural)")

print("\nRECOMMENDED SENSOR GRID (Main Room only, 0.5m offset from walls):")
print(f"  X: {grid_x_min:.3f} to {grid_x_max:.3f} m (7.26m)")
print(f"  Y: {grid_y_min:.3f} to {grid_y_max:.3f} m (8.97m)")
print(f"  Grid: 15 × 18 = 270 sensors")

print("\nWHY THE DIFFERENCE:")
print("  1. Your grid included corridor (3.65m additional depth)")
print("  2. Your grid extended beyond building (-2.74m to 11.52m in X)")
print("  3. No wall offset was applied")
print("  4. The 'corridor' floor polygons appear to define the exterior boundary")
print("     or circulation space, not the primary daylit room")

print("\nRECOMMENDATION:")
print("  Focus sensor grid on the MAIN ROOM (PISO-CONCRETO-PULIDOIER)")
print("  This is the primary occupied space with north and south windows")
print("  The corridor appears to be an exterior circulation/boundary zone")
print("="*80)
