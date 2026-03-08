# Optical Properties of Building Materials

This document describes the optical properties of materials used in the Radiance daylighting simulation for the main room (sensor grid area) and the adjacent hallway to the south.

## Material Summary

| Material | Radiance Type | Reflectance (ρ) | Transmittance (τ) | Location |
|----------|---------------|-----------------|-------------------|----------|
| PISO-CONCRETO-PULIDOIER | plastic | 0.30 | - | Main room floor |
| PISO-PASILLOIER | plastic | 0.36 | - | Hallway floor |
| LadrilloIER | plastic | 0.55 | - | Brick walls |
| Material-de-bloque-de-componente-del-proyecto | plastic | 0.40 | - | Wall components |
| CONCRETO-ARMADOIER | plastic | 0.10 | - | Ceiling |
| AluminiumIER | metal | 0.68 | - | Window frames |
| Acristalamiento-exterior-del-proyecto | glass | - | 0.88 | Window glazing |

## Room Layout

```
                    NORTH (y = 0.12m)
                    ══════════════════
                    │    Windows    │
    ┌───────────────┴────────────────┴───────────────┐
    │                                                 │
    │              MAIN ROOM                          │
    │         (PISO-CONCRETO-PULIDOIER)              │
    │              8.26m × 9.97m                      │
    │                                                 │
    │         ┌─────────────────────┐                │
    │         │   Sensor Grid       │                │
    │         │   7 × 9 = 63 pts    │                │
    │         │   z = 0.75m         │                │
    │         └─────────────────────┘                │
    │                                                 │
    ├────────────────┬────────────────┬──────────────┤ y = -9.85m
    │    Windows     │                │   Windows    │
    ══════════════════════════════════════════════════
    │                                                 │
    │              HALLWAY (South)                    │
    │           (PISO-PASILLOIER)                    │
    │           14.26m × 3.65m                       │
    │                                                 │
    └─────────────────────────────────────────────────┘ y = -13.50m
                    SOUTH
```

## Detailed Material Properties

### 1. Main Room Floor - PISO-CONCRETO-PULIDOIER

**Radiance definition:**
```
void plastic PISO-CONCRETO-PULIDOIER
0
0
5 0.3 0.3 0.3 0.06 0.02
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse with specular |
| RGB Reflectance | (0.30, 0.30, 0.30) | Neutral gray |
| Specularity | 0.06 | Subtle specular component |
| Roughness | 0.02 | Nearly smooth surface |
| **Total Reflectance** | **30%** | Polished concrete with subtle brightness |

**Daylighting impact:** Polished concrete floor with subtle reflection contributes to inter-reflections.

---

### 2. Hallway Floor - PISO-PASILLOIER

**Radiance definition:**
```
void plastic PISO-PASILLOIER
0
0
5 0.36 0.36 0.36 0 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse |
| RGB Reflectance | (0.36, 0.36, 0.36) | Medium gray |
| Specularity | 0 | Purely diffuse (no specular) |
| Roughness | 0 | N/A (diffuse material) |
| **Total Reflectance** | **36%** | Rough textured concrete |

**Daylighting impact:** Rough concrete with visible texture and marks. Purely diffuse reflection.

---

### 3. Walls - LadrilloIER (White Ceramic Brick)

**Radiance definition:**
```
void plastic LadrilloIER
0
0
5 0.55 0.55 0.55 0.04 0.03
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse with specular |
| RGB Reflectance | (0.55, 0.55, 0.55) | Medium-light (measured) |
| Specularity | 0.04 | Subtle glaze reflection |
| Roughness | 0.03 | Smooth ceramic surface |
| **Total Reflectance** | **55%** | White ceramic brick (measured) |

**Daylighting impact:** White ceramic brick with subtle glaze provides moderate inter-reflection with slight specular component.

--- 

### 4. Wall Components - Material-de-bloque-de-componente-del-proyecto

**Radiance definition:**
```
void plastic Material-de-bloque-de-componente-del-proyecto
0
0
5 0.4 0.4 0.4 0 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse |
| RGB Reflectance | (0.40, 0.40, 0.40) | Medium gray |
| Specularity | 0 | Purely diffuse |
| **Total Reflectance** | **40%** | Concrete block |

---

### 5. Ceiling - CONCRETO-ARMADOIER

**Radiance definition:**
```
void plastic CONCRETO-ARMADOIER
0
0
5 0.1 0.1 0.1 0 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse |
| RGB Reflectance | (0.10, 0.10, 0.10) | Dark gray |
| Specularity | 0 | Purely diffuse |
| **Total Reflectance** | **10%** | Dark reinforced concrete |

**Daylighting impact:** Very low ceiling reflectance significantly limits upward light reflection, reducing overall light distribution efficiency. This is a key factor in the simulation results.

---

### 6. Window Frames - AluminiumIER

**Radiance definition:**
```
void metal AluminiumIER
0
0
5 0.68 0.68 0.68 0.9 0.15
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | metal | Specular reflective |
| RGB Reflectance | (0.68, 0.68, 0.68) | Light metallic |
| Specularity | 0.9 | High specular fraction (metallic) |
| Roughness | 0.15 | Brushed surface texture |
| **Total Reflectance** | **68%** | Brushed aluminum |

---

### 7. Window Glazing - Acristalamiento-exterior-del-proyecto

**Radiance definition:**
```
void glass Acristalamiento-exterior-del-proyecto
0
0
3 0.88 0.88 0.88
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | glass | Transparent |
| RGB Transmittance | (0.88, 0.88, 0.88) | Clear glass |
| **Total Transmittance** | **88%** | Good light transmission |

**Daylighting impact:** Good light transmission allows significant daylight penetration. This transmittance value is typical for single-pane clear glass.

---

## Reflectance Comparison

```
Ceiling        ██░░░░░░░░░░░░░░░░░░  10%  (Dark)
Main Floor     ██████░░░░░░░░░░░░░░  30%  (Medium-Dark)
Hallway Floor  ████████░░░░░░░░░░░░  36%  (Medium)
Wall Block     ████████░░░░░░░░░░░░  40%  (Medium)
Brick Walls    ███████████░░░░░░░░░  55%  (Medium-Light)
Aluminum       ██████████████░░░░░░  68%  (Reflective)
```

## Notes on Daylighting Performance

1. **Floor-Ceiling Contrast**: The difference between floor reflectance (30%) and ceiling reflectance (10%) creates an asymmetric light distribution pattern, with more light reflected upward from the floor than downward from the ceiling.

2. **Bilateral Daylighting**: Windows on both North and South walls provide bilateral daylighting, which typically results in more uniform illuminance distribution compared to unilateral designs.

3. **Hallway Contribution**: The hallway floor (36%) has slightly higher reflectance than the main room floor (30%), though both are in the medium-dark range.

4. **Glass Transmittance**: The glazing transmittance (88%) is typical for single-pane clear glass. This allows good daylight penetration while accounting for real-world glass properties.
