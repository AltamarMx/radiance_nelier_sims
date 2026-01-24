#!/usr/bin/env python3
"""
Analyze floor polygons from Radiance geometry files to determine
actual interior space for sensor grid placement.
"""

import re
import numpy as np
from pathlib import Path

def parse_polygon(line):
    """Parse a Radiance polygon coordinate line."""
    # Format: 12 x1 y1 z1 x2 y2 z2 x3 y3 z3 x4 y4 z4
    parts = line.strip().split()
    if parts[0] != '12':
        return None

    coords = [float(x) for x in parts[1:]]
    # Extract x, y coordinates (every 3rd value starting from 0 and 1)
    x_coords = [coords[i] for i in range(0, len(coords), 3)]
    y_coords = [coords[i] for i in range(1, len(coords), 3)]
    z_coords = [coords[i] for i in range(2, len(coords), 3)]

    return {
        'x': x_coords,
        'y': y_coords,
        'z': z_coords
    }

def get_polygon_bounds(polygon):
    """Get bounding box of a polygon."""
    return {
        'x_min': min(polygon['x']),
        'x_max': max(polygon['x']),
        'y_min': min(polygon['y']),
        'y_max': max(polygon['y']),
        'z': polygon['z'][0]  # Assume floor is flat
    }

def polygon_area(polygon):
    """Calculate area of polygon using shoelace formula."""
    x = polygon['x']
    y = polygon['y']
    n = len(x)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += x[i] * y[j]
        area -= x[j] * y[i]
    return abs(area) / 2.0

def main():
    scene_file = Path('/Users/gbv/radiance_claude/edificio/objects/scene.geom')

    # Read the file and extract floor polygons
    with open(scene_file, 'r') as f:
        lines = f.readlines()

    main_floor_polys = []
    corridor_polys = []

    current_material = None
    for i, line in enumerate(lines):
        if 'PISO-CONCRETO-PULIDOIER polygon' in line:
            current_material = 'main'
        elif 'PISO-PASILLOIER polygon' in line:
            current_material = 'corridor'
        elif line.strip().startswith('12 ') and current_material:
            poly = parse_polygon(line)
            if poly:
                if current_material == 'main':
                    main_floor_polys.append(poly)
                else:
                    corridor_polys.append(poly)
            current_material = None

    print("=" * 80)
    print("FLOOR GEOMETRY ANALYSIS")
    print("=" * 80)

    # Analyze main room floor
    print(f"\nMAIN ROOM FLOOR (PISO-CONCRETO-PULIDOIER):")
    print(f"  Number of polygons: {len(main_floor_polys)}")

    if main_floor_polys:
        all_x = []
        all_y = []
        total_area = 0

        for i, poly in enumerate(main_floor_polys):
            bounds = get_polygon_bounds(poly)
            area = polygon_area(poly)
            total_area += area
            all_x.extend(poly['x'])
            all_y.extend(poly['y'])

            print(f"\n  Polygon {i}:")
            print(f"    X range: {bounds['x_min']:.3f} to {bounds['x_max']:.3f} m")
            print(f"    Y range: {bounds['y_min']:.3f} to {bounds['y_max']:.3f} m")
            print(f"    Z level: {bounds['z']:.6f} m")
            print(f"    Area: {area:.2f} m²")

        main_x_min, main_x_max = min(all_x), max(all_x)
        main_y_min, main_y_max = min(all_y), max(all_y)

        print(f"\n  MAIN ROOM BOUNDS:")
        print(f"    X: {main_x_min:.3f} to {main_x_max:.3f} m (width: {main_x_max - main_x_min:.3f} m)")
        print(f"    Y: {main_y_min:.3f} to {main_y_max:.3f} m (depth: {main_y_max - main_y_min:.3f} m)")
        print(f"    Total area: {total_area:.2f} m²")

    # Analyze corridor floor
    print(f"\nCORRIDOR FLOOR (PISO-PASILLOIER):")
    print(f"  Number of polygons: {len(corridor_polys)}")

    if corridor_polys:
        all_x = []
        all_y = []
        total_area = 0

        for i, poly in enumerate(corridor_polys):
            bounds = get_polygon_bounds(poly)
            area = polygon_area(poly)
            total_area += area
            all_x.extend(poly['x'])
            all_y.extend(poly['y'])

            if i < 3:  # Show first few
                print(f"\n  Polygon {i}:")
                print(f"    X range: {bounds['x_min']:.3f} to {bounds['x_max']:.3f} m")
                print(f"    Y range: {bounds['y_min']:.3f} to {bounds['y_max']:.3f} m")
                print(f"    Area: {area:.2f} m²")

        if len(corridor_polys) > 3:
            print(f"  ... and {len(corridor_polys) - 3} more polygons")

        corr_x_min, corr_x_max = min(all_x), max(all_x)
        corr_y_min, corr_y_max = min(all_y), max(all_y)

        print(f"\n  CORRIDOR BOUNDS:")
        print(f"    X: {corr_x_min:.3f} to {corr_x_max:.3f} m (width: {corr_x_max - corr_x_min:.3f} m)")
        print(f"    Y: {corr_y_min:.3f} to {corr_y_max:.3f} m (depth: {corr_y_max - corr_y_min:.3f} m)")
        print(f"    Total area: {total_area:.2f} m²")

    # Combined analysis
    print("\n" + "=" * 80)
    print("COMPARISON & RECOMMENDATIONS")
    print("=" * 80)

    if main_floor_polys and corridor_polys:
        print("\nThe building contains TWO DISTINCT SPACES:")
        print(f"  1. Main room: {main_x_max - main_x_min:.2f}m × {main_y_max - main_y_min:.2f}m")
        print(f"  2. Corridor: {corr_x_max - corr_x_min:.2f}m × {corr_y_max - corr_y_min:.2f}m")

        # Check for overlap
        if (main_y_min <= corr_y_max and main_y_max >= corr_y_min and
            main_x_min <= corr_x_max and main_x_max >= corr_x_min):
            print("\n  Note: Spaces may overlap or be adjacent")

    print("\nRECOMMENDED SENSOR GRID BOUNDARIES:")
    print("\nOption 1: MAIN ROOM ONLY (most common for daylighting analysis)")
    if main_floor_polys:
        # Add 0.5m offset from walls
        offset = 0.5
        print(f"  X: {main_x_min + offset:.3f} to {main_x_max - offset:.3f} m")
        print(f"  Y: {main_y_min + offset:.3f} to {main_y_max - offset:.3f} m")
        print(f"  Grid dimensions: {main_x_max - main_x_min - 2*offset:.2f}m × {main_y_max - main_y_min - 2*offset:.2f}m")
        print(f"  At 0.5m spacing: ~{int((main_x_max - main_x_min - 2*offset)/0.5) * int((main_y_max - main_y_min - 2*offset)/0.5)} sensors")

    print("\nOption 2: BOTH SPACES (if corridor daylighting is important)")
    if main_floor_polys and corridor_polys:
        combined_x_min = min(main_x_min, corr_x_min)
        combined_x_max = max(main_x_max, corr_x_max)
        combined_y_min = min(main_y_min, corr_y_min)
        combined_y_max = max(main_y_max, corr_y_max)

        offset = 0.5
        print(f"  X: {combined_x_min + offset:.3f} to {combined_x_max - offset:.3f} m")
        print(f"  Y: {combined_y_min + offset:.3f} to {combined_y_max - offset:.3f} m")
        print(f"  Grid dimensions: {combined_x_max - combined_x_min - 2*offset:.2f}m × {combined_y_max - combined_y_min - 2*offset:.2f}m")
        print(f"  At 0.5m spacing: ~{int((combined_x_max - combined_x_min - 2*offset)/0.5) * int((combined_y_max - combined_y_min - 2*offset)/0.5)} sensors")

if __name__ == '__main__':
    main()
