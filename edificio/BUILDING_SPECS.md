# Building Specifications

## Room Geometry

### Main Room (Analysis Area)
| Parameter | Value |
|-----------|-------|
| Interior dimensions | 8.26m × 9.97m |
| Floor area | 82.4 m² |
| Floor material | PISO-CONCRETO-PULIDOIER |

### Sensor Grid
| Parameter | Value |
|-----------|-------|
| Coverage area | 7.66m × 9.37m |
| Wall offset | 0.1m |
| Grid layout | 20 × 24 |
| Sensor count | 480 |
| Spacing | ~0.40m |
| Work plane height | 0.75m |

### Walls
| Wall | Position | Feature |
|------|----------|---------|
| North | y = 0.12m | Windows |
| South | y = -9.85m | Windows |
| East | x = 8.32m | Solid |
| West | x = 0.26m | Solid |
| Thickness | ~0.20m | |

### Windows
| Location | X Range | Height | Width |
|----------|---------|--------|-------|
| North wall | 1.06m - 6.56m | 0.90m - 3.40m | 5.5m |
| South wall | 1.06m - 6.56m | 0.90m - 3.40m | 5.5m |

Window coverage: ~67% of wall width, bilateral daylighting.

---

## Materials

| Material | Type | ρ/τ | Description |
|----------|------|-----|-------------|
| PISO-CONCRETO-PULIDOIER | plastic | ρ=0.65 | Main room floor (polished concrete) |
| PISO-PASILLOIER | plastic | ρ=0.36 | Corridor floor |
| LadrilloIER | plastic | ρ=0.55 | Brick walls |
| Material-de-bloque-de-componente-del-proyecto | plastic | ρ=0.40 | Wall components |
| CONCRETO-ARMADOIER | plastic | ρ=0.10 | Concrete ceiling |
| AluminiumIER | metal | ρ=0.68 | Aluminum frames |
| Acristalamiento-exterior-del-proyecto | glass | τ=0.978 | Window glazing |

**ρ** = reflectance, **τ** = transmittance

### Material Types
- **plastic**: Lambertian diffuse surfaces
- **metal**: Specular reflective surfaces
- **glass**: Transparent materials

### Daylighting Notes
- High glazing transmittance (97.8%) - excellent
- Light floor (65%) - good inter-reflection
- Dark ceiling (10%) - limits light distribution

---

## Coordinate System

```
Y ↑
  │
  │   ┌─────────────────┐ y = 0.12 (North, windows)
  │   │                 │
  │   │   MAIN ROOM     │
  │   │   8.26 × 9.97m  │
  │   │                 │
  │   └─────────────────┘ y = -9.85 (South, windows)
  │   x=0.26          x=8.32
  └────────────────────────→ X
```

Grid origin: (0.559, -9.553, 0.75)
