#!/usr/bin/env python3
"""
Analyze Radiance geometry files to extract room dimensions and bounding box.
"""

import re
import numpy as np

def parse_radiance_polygon(line):
    """
    Parse a Radiance polygon definition line to extract coordinates.
    Format: "12 x1 y1 z1 x2 y2 z2 x3 y3 z3 x4 y4 z4"
    """
    parts = line.strip().split()
    if len(parts) < 13 or parts[0] != '12':
        return None

    # Extract coordinates (skip first element which is '12')
    coords = [float(x) for x in parts[1:]]

    # Group into (x, y, z) tuples
    vertices = []
    for i in range(0, len(coords), 3):
        if i+2 < len(coords):
            vertices.append((coords[i], coords[i+1], coords[i+2]))

    return vertices

def analyze_geometry_file(filepath, material_filter=None):
    """
    Analyze a Radiance geometry file and extract all polygon vertices.
    """
    vertices = []
    current_material = None

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            # Check if this is a material/object definition line
            if ' polygon ' in line:
                current_material = line.split()[0]

            # Check if this is a coordinate line (starts with "12")
            elif line.startswith('12 '):
                # If filtering by material, check if it matches
                if material_filter:
                    if current_material and any(m.lower() in current_material.lower() for m in material_filter):
                        verts = parse_radiance_polygon(line)
                        if verts:
                            vertices.extend(verts)
                else:
                    verts = parse_radiance_polygon(line)
                    if verts:
                        vertices.extend(verts)

    return vertices

def get_bounding_box(vertices):
    """
    Calculate bounding box from list of (x, y, z) vertices.
    """
    if not vertices:
        return None

    vertices = np.array(vertices)

    min_coords = vertices.min(axis=0)
    max_coords = vertices.max(axis=0)

    return {
        'min_x': min_coords[0],
        'max_x': max_coords[0],
        'min_y': min_coords[1],
        'max_y': max_coords[1],
        'min_z': min_coords[2],
        'max_z': max_coords[2]
    }

def analyze_room_geometry(scene_file, glazing_file):
    """
    Analyze room geometry from scene and glazing files.
    """
    print("=" * 70)
    print("RADIANCE ROOM GEOMETRY ANALYSIS")
    print("=" * 70)
    print()

    # Analyze floor polygons (PISO material)
    print("Analyzing floor polygons (PISO material)...")
    floor_vertices = analyze_geometry_file(scene_file, material_filter=['PISO', 'piso'])

    if floor_vertices:
        floor_bbox = get_bounding_box(floor_vertices)
        print(f"  Found {len(floor_vertices)} floor vertices")
        print(f"  Floor bounding box:")
        print(f"    X: {floor_bbox['min_x']:.3f} to {floor_bbox['max_x']:.3f} m")
        print(f"    Y: {floor_bbox['min_y']:.3f} to {floor_bbox['max_y']:.3f} m")
        print(f"    Z: {floor_bbox['min_z']:.3f} to {floor_bbox['max_z']:.3f} m")
        print()

        # Calculate floor dimensions
        floor_length = floor_bbox['max_x'] - floor_bbox['min_x']
        floor_width = floor_bbox['max_y'] - floor_bbox['min_y']
        floor_area = floor_length * floor_width

        print(f"Floor dimensions:")
        print(f"  Length (X): {floor_length:.3f} m")
        print(f"  Width (Y): {floor_width:.3f} m")
        print(f"  Area: {floor_area:.2f} m²")
        print()
    else:
        floor_bbox = None
        print("  WARNING: No floor polygons found!")
        print()

    # Analyze all scene geometry to get room height
    print("Analyzing complete room geometry...")
    all_vertices = analyze_geometry_file(scene_file)

    if all_vertices:
        room_bbox = get_bounding_box(all_vertices)
        print(f"  Found {len(all_vertices)} total vertices in scene")
        print(f"  Complete room bounding box:")
        print(f"    X: {room_bbox['min_x']:.3f} to {room_bbox['max_x']:.3f} m")
        print(f"    Y: {room_bbox['min_y']:.3f} to {room_bbox['max_y']:.3f} m")
        print(f"    Z: {room_bbox['min_z']:.3f} to {room_bbox['max_z']:.3f} m")
        print()

        room_height = room_bbox['max_z'] - room_bbox['min_z']
        print(f"Room height: {room_height:.3f} m")
        print()
    else:
        room_bbox = None
        print("  WARNING: No geometry found in scene file!")
        print()

    # Analyze glazing
    print("Analyzing glazing geometry...")
    glazing_vertices = analyze_geometry_file(glazing_file)

    if glazing_vertices:
        glazing_bbox = get_bounding_box(glazing_vertices)
        print(f"  Found {len(glazing_vertices)} glazing vertices")
        print(f"  Glazing bounding box:")
        print(f"    X: {glazing_bbox['min_x']:.3f} to {glazing_bbox['max_x']:.3f} m")
        print(f"    Y: {glazing_bbox['min_y']:.3f} to {glazing_bbox['max_y']:.3f} m")
        print(f"    Z: {glazing_bbox['min_z']:.3f} to {glazing_bbox['max_z']:.3f} m")
        print()

        # Estimate window sill height (minimum Z of glazing)
        window_sill_height = glazing_bbox['min_z']
        print(f"Window sill height: {window_sill_height:.3f} m")
        print()
    else:
        glazing_bbox = None
        print("  WARNING: No glazing geometry found!")
        print()

    # Determine work plane height
    print("=" * 70)
    print("SENSOR GRID RECOMMENDATIONS")
    print("=" * 70)
    print()

    # Standard work plane heights
    work_plane_height = 0.75  # Default for office spaces (0.75m or 0.8m typical)

    if floor_bbox:
        # Work plane is typically 0.75m above the floor
        work_plane_z = floor_bbox['min_z'] + work_plane_height

        print(f"Recommended work plane height: {work_plane_height:.2f} m above floor")
        print(f"Work plane Z-coordinate: {work_plane_z:.3f} m")
        print()

        # Calculate sensor grid parameters with 0.5m spacing
        spacing = 0.5

        # Calculate number of sensors in each direction
        nx = int(floor_length / spacing) + 1
        ny = int(floor_width / spacing) + 1
        total_sensors = nx * ny

        print(f"Sensor grid parameters (spacing: {spacing} m):")
        print(f"  Grid origin: ({floor_bbox['min_x']:.3f}, {floor_bbox['min_y']:.3f}, {work_plane_z:.3f})")
        print(f"  Grid dimensions: {nx} x {ny} sensors")
        print(f"  Total sensor points: {total_sensors}")
        print(f"  Coverage area: {floor_area:.2f} m²")
        print(f"  Sensor density: {floor_area/total_sensors:.2f} m²/sensor")
        print()

        # Generate sensor grid definition
        print("=" * 70)
        print("SENSOR GRID DEFINITION")
        print("=" * 70)
        print()
        print(f"# Sensor grid for annual daylighting analysis")
        print(f"# Generated from geometry analysis")
        print(f"# Grid spacing: {spacing} m")
        print(f"# Work plane height: {work_plane_height} m")
        print(f"#")
        print(f"# Grid parameters:")
        print(f"#   Origin: ({floor_bbox['min_x']:.3f}, {floor_bbox['min_y']:.3f}, {work_plane_z:.3f})")
        print(f"#   X-direction: {floor_length:.3f} m, {nx} points")
        print(f"#   Y-direction: {floor_width:.3f} m, {ny} points")
        print(f"#   Total points: {total_sensors}")
        print()

        return {
            'floor_bbox': floor_bbox,
            'room_bbox': room_bbox,
            'glazing_bbox': glazing_bbox,
            'floor_length': floor_length,
            'floor_width': floor_width,
            'floor_area': floor_area,
            'room_height': room_height if room_bbox else None,
            'work_plane_height': work_plane_height,
            'work_plane_z': work_plane_z,
            'sensor_spacing': spacing,
            'sensor_grid_nx': nx,
            'sensor_grid_ny': ny,
            'total_sensors': total_sensors
        }
    else:
        print("ERROR: Cannot determine work plane height without floor geometry!")
        return None

if __name__ == "__main__":
    scene_file = "/Users/gbv/radiance_claude/edificio/scene.geom"
    glazing_file = "/Users/gbv/radiance_claude/edificio/glazing.geom"

    results = analyze_room_geometry(scene_file, glazing_file)

    if results:
        print("=" * 70)
        print("Analysis complete!")
        print("=" * 70)
