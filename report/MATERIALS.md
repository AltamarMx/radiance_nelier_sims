# Optical Properties of Building Materials

This document describes the optical properties of materials used in the Radiance daylighting simulation for the main room (sensor grid area) and the adjacent hallway to the south.

## Material Summary

| Material | Radiance Type | Reflectance (ρ) | Transmittance (τ) | Location |
|----------|---------------|-----------------|-------------------|----------|
| PISO-CONCRETO-PULIDOIER | plastic | 0.65 | - | Main room floor |
| PISO-PASILLOIER | plastic | 0.36 | - | Hallway floor |
| LadrilloIER | plastic | 0.55 | - | Brick walls |
| Material-de-bloque-de-componente-del-proyecto | plastic | 0.40 | - | Wall components |
| CONCRETO-ARMADOIER | plastic | 0.10 | - | Ceiling |
| AluminiumIER | metal | 0.68 | - | Window frames |
| Acristalamiento-exterior-del-proyecto | glass | - | 0.978 | Window glazing |

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
5 0.65 0.65 0.65 0.2 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse |
| RGB Reflectance | (0.65, 0.65, 0.65) | Neutral gray |
| Specularity | 0.2 | Moderate specular component |
| Roughness | 0 | Smooth surface |
| **Total Reflectance** | **65%** | Light gray polished concrete |

**Daylighting impact:** High reflectance floor contributes significantly to inter-reflections, improving light distribution in the room interior.

---

### 2. Hallway Floor - PISO-PASILLOIER

**Radiance definition:**
```
void plastic PISO-PASILLOIER
0
0
5 0.36 0.36 0.36 0.2 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse |
| RGB Reflectance | (0.36, 0.36, 0.36) | Medium gray |
| Specularity | 0.2 | Moderate specular component |
| Roughness | 0 | Smooth surface |
| **Total Reflectance** | **36%** | Medium gray floor |

**Daylighting impact:** Lower reflectance than main room reduces light contribution from hallway to main room through south windows.

---

### 3. Walls - LadrilloIER (Brick)

**Radiance definition:**
```
void plastic LadrilloIER
0
0
5 0.55 0.55 0.55 0 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | plastic | Lambertian diffuse |
| RGB Reflectance | (0.55, 0.55, 0.55) | Medium-light gray |
| Specularity | 0 | Purely diffuse |
| Roughness | 0 | - |
| **Total Reflectance** | **55%** | Typical painted brick |

**Daylighting impact:** Moderate wall reflectance provides good inter-reflection without excessive brightness.

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
5 0.68 0.68 0.68 0 0
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | metal | Specular reflective |
| RGB Reflectance | (0.68, 0.68, 0.68) | Light metallic |
| Specularity | 0 | (inherent to metal type) |
| **Total Reflectance** | **68%** | Brushed aluminum |

---

### 7. Window Glazing - Acristalamiento-exterior-del-proyecto

**Radiance definition:**
```
void glass Acristalamiento-exterior-del-proyecto
0
0
3 0.978371 0.978371 0.978371
```

| Property | Value | Description |
|----------|-------|-------------|
| Type | glass | Transparent |
| RGB Transmittance | (0.978, 0.978, 0.978) | Clear glass |
| **Total Transmittance** | **97.8%** | Very high clarity |

**Daylighting impact:** Excellent light transmission allows maximum daylight penetration. This high transmittance value represents idealized clear glass without coatings or tinting.

---

## Reflectance Comparison

```
Ceiling        ████░░░░░░░░░░░░░░░░  10%  (Dark)
Hallway Floor  ████████░░░░░░░░░░░░  36%  (Medium)
Wall Block     ████████░░░░░░░░░░░░  40%  (Medium)
Brick Walls    ███████████░░░░░░░░░  55%  (Medium-Light)
Main Floor     █████████████░░░░░░░  65%  (Light)
Aluminum       ██████████████░░░░░░  68%  (Reflective)
```

## Notes on Daylighting Performance

1. **Floor-Ceiling Contrast**: The large difference between floor reflectance (65%) and ceiling reflectance (10%) creates an asymmetric light distribution pattern, with more light reflected upward from the floor than downward from the ceiling.

2. **Bilateral Daylighting**: Windows on both North and South walls provide bilateral daylighting, which typically results in more uniform illuminance distribution compared to unilateral designs.

3. **Hallway Contribution**: The darker hallway floor (36% vs 65%) reduces the amount of reflected light entering the main room from the south, potentially creating slight north-south asymmetry in the light distribution.

4. **Glass Transmittance**: The very high glazing transmittance (97.8%) represents idealized conditions. Real-world glazing typically has lower transmittance (70-85%) due to coatings, dirt, and frame obstruction.
