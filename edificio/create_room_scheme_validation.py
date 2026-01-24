#!/usr/bin/env python3
"""
Create room scheme diagram showing:
- Room boundaries and dimensions
- Window positions on north and south walls
- Validation sensor grid (7×9 = 63 points)
- Door location (on east wall)
- Orientation indicators

Output: images/room_scheme_validation.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
import os

# Room dimensions (from geometry)
ROOM_MIN_X = 0.458644626504064   # East wall
ROOM_MAX_X = 8.31864462650407    # West wall
ROOM_MIN_Y = -9.65327504952668   # South wall
ROOM_MAX_Y = -0.0832750495266698 # North wall

ROOM_WIDTH = ROOM_MAX_X - ROOM_MIN_X   # ~7.86m (E-W)
ROOM_DEPTH = ROOM_MAX_Y - ROOM_MIN_Y   # ~9.57m (N-S)

# Window positions from glazing.geom
# North wall windows (Y ≈ 0.117): X ranges from 1.06 to 6.56
NORTH_WINDOWS = [
    (1.05964463, 2.15764463),  # Window 1
    (2.15964463, 3.25764463),  # Window 2
    (3.25964463, 4.35764463),  # Window 3
    (4.35964463, 5.45764463),  # Window 4
    (5.45964463, 6.55764463),  # Window 5
]
NORTH_WALL_Y = -0.0832750495266698

# South wall windows (Y ≈ -9.853): X ranges from 1.06 to 6.56
SOUTH_WINDOWS = [
    (1.05964463, 2.15764463),  # Window 1
    (2.15964463, 3.25764463),  # Window 2
    (3.25964463, 4.35764463),  # Window 3
    (4.35964463, 5.45764463),  # Window 4
    (5.45964463, 6.55764463),  # Window 5
]
SOUTH_WALL_Y = -9.65327504952668

# Door on east wall (typical location - assumed based on building conventions)
DOOR_Y_START = -6.0
DOOR_Y_END = -4.0
DOOR_X = ROOM_MIN_X

# Validation grid specifications
NX = 7   # Points in X direction
NY = 9   # Points in Y direction
SPACING = 1.08
OFFSET_EAST = 0.71
OFFSET_SOUTH = 0.51
START_X = ROOM_MIN_X + OFFSET_EAST
START_Y = ROOM_MIN_Y + OFFSET_SOUTH


def create_room_scheme():
    """Create the room scheme diagram"""

    fig, ax = plt.subplots(figsize=(14, 16))

    # Draw room outline
    room_rect = Rectangle(
        (ROOM_MIN_X, ROOM_MIN_Y), ROOM_WIDTH, ROOM_DEPTH,
        linewidth=3, edgecolor='black', facecolor='#f5f5f5',
        label='Room floor'
    )
    ax.add_patch(room_rect)

    # Draw walls as thick lines
    wall_width = 0.15

    # North wall (with windows)
    ax.fill([ROOM_MIN_X - wall_width, ROOM_MAX_X + wall_width, ROOM_MAX_X + wall_width, ROOM_MIN_X - wall_width],
            [ROOM_MAX_Y, ROOM_MAX_Y, ROOM_MAX_Y + wall_width, ROOM_MAX_Y + wall_width],
            color='#808080', label='Walls')

    # South wall (with windows)
    ax.fill([ROOM_MIN_X - wall_width, ROOM_MAX_X + wall_width, ROOM_MAX_X + wall_width, ROOM_MIN_X - wall_width],
            [ROOM_MIN_Y, ROOM_MIN_Y, ROOM_MIN_Y - wall_width, ROOM_MIN_Y - wall_width],
            color='#808080')

    # East wall (with door)
    ax.fill([ROOM_MIN_X - wall_width, ROOM_MIN_X, ROOM_MIN_X, ROOM_MIN_X - wall_width],
            [ROOM_MIN_Y - wall_width, ROOM_MIN_Y - wall_width, ROOM_MAX_Y + wall_width, ROOM_MAX_Y + wall_width],
            color='#808080')

    # West wall
    ax.fill([ROOM_MAX_X, ROOM_MAX_X + wall_width, ROOM_MAX_X + wall_width, ROOM_MAX_X],
            [ROOM_MIN_Y - wall_width, ROOM_MIN_Y - wall_width, ROOM_MAX_Y + wall_width, ROOM_MAX_Y + wall_width],
            color='#808080')

    # Draw north wall windows (cyan/blue)
    for x_start, x_end in NORTH_WINDOWS:
        window = Rectangle(
            (x_start, ROOM_MAX_Y - 0.05), x_end - x_start, 0.20,
            linewidth=2, edgecolor='blue', facecolor='#87CEEB', alpha=0.8
        )
        ax.add_patch(window)

    # Draw south wall windows (cyan/blue)
    for x_start, x_end in SOUTH_WINDOWS:
        window = Rectangle(
            (x_start, ROOM_MIN_Y - 0.15), x_end - x_start, 0.20,
            linewidth=2, edgecolor='blue', facecolor='#87CEEB', alpha=0.8
        )
        ax.add_patch(window)

    # Draw door on east wall (brown)
    door = Rectangle(
        (ROOM_MIN_X - 0.20, DOOR_Y_START), 0.25, DOOR_Y_END - DOOR_Y_START,
        linewidth=2, edgecolor='#8B4513', facecolor='#D2691E', alpha=0.9
    )
    ax.add_patch(door)

    # Draw validation sensor grid points
    sensor_x = []
    sensor_y = []
    for ix in range(NX):
        x = START_X + ix * SPACING
        for iy in range(NY):
            y = START_Y + iy * SPACING
            sensor_x.append(x)
            sensor_y.append(y)

    ax.scatter(sensor_x, sensor_y, c='red', s=80, marker='o',
               edgecolors='darkred', linewidths=1.5, zorder=10,
               label=f'Luxmeter positions ({NX}×{NY}={NX*NY})')

    # Draw grid lines connecting sensors
    for ix in range(NX):
        x = START_X + ix * SPACING
        y_start = START_Y
        y_end = START_Y + (NY - 1) * SPACING
        ax.plot([x, x], [y_start, y_end], 'r--', alpha=0.3, linewidth=0.8)

    for iy in range(NY):
        y = START_Y + iy * SPACING
        x_start = START_X
        x_end = START_X + (NX - 1) * SPACING
        ax.plot([x_start, x_end], [y, y], 'r--', alpha=0.3, linewidth=0.8)

    # Add dimension annotations
    # Room width
    ax.annotate('', xy=(ROOM_MAX_X, ROOM_MIN_Y - 0.8), xytext=(ROOM_MIN_X, ROOM_MIN_Y - 0.8),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text((ROOM_MIN_X + ROOM_MAX_X) / 2, ROOM_MIN_Y - 1.1,
            f'{ROOM_WIDTH:.2f} m', ha='center', va='top', fontsize=11, fontweight='bold')

    # Room depth
    ax.annotate('', xy=(ROOM_MAX_X + 0.8, ROOM_MAX_Y), xytext=(ROOM_MAX_X + 0.8, ROOM_MIN_Y),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(ROOM_MAX_X + 1.1, (ROOM_MIN_Y + ROOM_MAX_Y) / 2,
            f'{ROOM_DEPTH:.2f} m', ha='left', va='center', fontsize=11, fontweight='bold', rotation=90)

    # Grid spacing annotation
    ax.annotate('', xy=(START_X + SPACING, START_Y - 0.3), xytext=(START_X, START_Y - 0.3),
                arrowprops=dict(arrowstyle='<->', color='red', lw=1))
    ax.text(START_X + SPACING / 2, START_Y - 0.5, f'{SPACING} m', ha='center', va='top',
            fontsize=9, color='darkred')

    # Offset annotations
    # East wall offset
    ax.annotate('', xy=(START_X, ROOM_MIN_Y + 0.3), xytext=(ROOM_MIN_X, ROOM_MIN_Y + 0.3),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1))
    ax.text((ROOM_MIN_X + START_X) / 2, ROOM_MIN_Y + 0.5, f'{OFFSET_EAST} m', ha='center',
            fontsize=8, color='darkgreen')

    # South wall offset
    ax.annotate('', xy=(ROOM_MIN_X + 0.3, START_Y), xytext=(ROOM_MIN_X + 0.3, ROOM_MIN_Y),
                arrowprops=dict(arrowstyle='<->', color='green', lw=1))
    ax.text(ROOM_MIN_X + 0.5, (ROOM_MIN_Y + START_Y) / 2, f'{OFFSET_SOUTH} m', ha='left',
            fontsize=8, color='darkgreen', rotation=90, va='center')

    # Add orientation compass
    compass_x, compass_y = ROOM_MIN_X - 1.5, (ROOM_MIN_Y + ROOM_MAX_Y) / 2
    arrow_len = 0.8
    ax.annotate('N', xy=(compass_x, compass_y + arrow_len), xytext=(compass_x, compass_y),
                arrowprops=dict(arrowstyle='->', color='navy', lw=2),
                fontsize=14, fontweight='bold', ha='center', va='bottom', color='navy')
    ax.text(compass_x, compass_y - 0.3, 'S', fontsize=10, ha='center', va='top', color='gray')
    ax.text(compass_x + arrow_len, compass_y, 'E', fontsize=10, ha='left', va='center', color='gray')
    ax.text(compass_x - arrow_len, compass_y, 'W', fontsize=10, ha='right', va='center', color='gray')

    # Add wall labels
    ax.text((ROOM_MIN_X + ROOM_MAX_X) / 2, ROOM_MAX_Y + 0.4, 'NORTH WALL (5 windows)',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='blue')
    ax.text((ROOM_MIN_X + ROOM_MAX_X) / 2, ROOM_MIN_Y - 0.4, 'SOUTH WALL (5 windows)',
            ha='center', va='top', fontsize=11, fontweight='bold', color='blue')
    ax.text(ROOM_MIN_X - 0.4, (ROOM_MIN_Y + ROOM_MAX_Y) / 2, 'EAST\n(front)',
            ha='right', va='center', fontsize=10, fontweight='bold', color='#8B4513')
    ax.text(ROOM_MAX_X + 0.4, (ROOM_MIN_Y + ROOM_MAX_Y) / 2, 'WEST',
            ha='left', va='center', fontsize=10, fontweight='bold', color='gray')

    # Title and info
    ax.set_title('Room Scheme - Validation Sensor Grid\n'
                 f'Grid: {NX}×{NY} = {NX*NY} points | Spacing: {SPACING} m | Height: 0.75 m',
                 fontsize=14, fontweight='bold', pad=20)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#87CEEB', edgecolor='blue', label='Windows'),
        mpatches.Patch(facecolor='#D2691E', edgecolor='#8B4513', label='Door'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red',
                   markersize=10, markeredgecolor='darkred', label=f'Luxmeter points ({NX*NY})'),
        plt.Line2D([0], [0], linestyle='--', color='red', alpha=0.5, label='Sensor grid lines'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # Grid specifications text box
    specs_text = (
        f"Validation Grid Specifications:\n"
        f"  Points X (E→W): {NX}\n"
        f"  Points Y (N↔S): {NY}\n"
        f"  Total sensors: {NX*NY}\n"
        f"  Spacing: {SPACING} m\n"
        f"  Height: 0.75 m\n"
        f"\nWall offsets:\n"
        f"  From East: {OFFSET_EAST} m\n"
        f"  From South: {OFFSET_SOUTH} m\n"
        f"  To West: 0.68 m\n"
        f"  To North: 0.51 m"
    )
    ax.text(0.02, 0.02, specs_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='bottom', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, edgecolor='orange'))

    # Set axis properties
    ax.set_xlim(ROOM_MIN_X - 2.5, ROOM_MAX_X + 2)
    ax.set_ylim(ROOM_MIN_Y - 2, ROOM_MAX_Y + 1.5)
    ax.set_aspect('equal')
    ax.set_xlabel('X coordinate [m]', fontsize=12)
    ax.set_ylabel('Y coordinate [m]', fontsize=12)
    ax.grid(True, alpha=0.2, linestyle=':')

    plt.tight_layout()

    # Save
    os.makedirs('images', exist_ok=True)
    output_path = 'images/room_scheme_validation.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")

    plt.close()


if __name__ == '__main__':
    create_room_scheme()
