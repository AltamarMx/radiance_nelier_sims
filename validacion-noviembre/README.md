# Validacion Noviembre - Simulacion con Calibracion Combinada

Simulacion de validacion para el 20 de noviembre usando la calibracion combinada optima (3 parametros).

## Proposito

Comparar los resultados de la simulacion Radiance (Two-Phase Method) contra mediciones experimentales con luximetro realizadas el 20 de noviembre de 2024, usando los materiales calibrados mediante busqueda parametrica.

## Parametros de Calibracion

Parametros optimos obtenidos de la busqueda parametrica extendida (3 parametros):

| Parametro | Original | Calibrado | Justificacion |
|-----------|----------|-----------|---------------|
| Transmitancia del acristalamiento (tau) | 0.88 | **0.76** | Obstruccion de marco + suciedad |
| Reflectancia del piso (rho_floor) | 0.30 | **0.21** | Pupitres cubren area del piso |
| Reflectancia del pasillo (rho_hall) | 0.36 | **0.29** | Mobiliario/equipo en pasillo |

Metricas de la calibracion: NMBE=-3.4%, CV(RMSE)=47.0%, R^2=0.61, GOF=47.1%

## Propiedades de Materiales

| Material | Reflectancia/Transmitancia | Especularidad | Rugosidad |
|----------|---------------------------|---------------|-----------|
| Piso concreto (PISO-CONCRETO-PULIDOIER) | 0.21 | 0.06 | 0.02 |
| Piso pasillo (PISO-PASILLOIER) | 0.29 | 0 | 0 |
| Ladrillo (LadrilloIER) | 0.55 | 0.04 | 0.03 |
| Bloque componente | 0.40 | 0 | 0 |
| Techo concreto (CONCRETO-ARMADOIER) | 0.10 | 0 | 0 |
| Aluminio (AluminiumIER) | 0.68 | 0.90 | 0.15 |
| Acristalamiento | tau = 0.76 | - | - |

## Esquema del Espacio

```
         MURO NORTE (5 ventanas)
    +-------------------------------+
    |  o   o   o   o   o   o   o    |  <- Fila 9 (Y = -0.50m)
    |  o   o   o   o   o   o   o    |
    |  o   o   o   o   o   o   o    |
    |  o   o   o   o   o   o   o    |
E   |  o   o   o   o   o   o   o    |  O
S   |  o   o   o   o   o   o   o    |  E
T   |  o   o   o   o   o   o   o    |  S
E   |  o   o   o   o   o   o   o    |  T
    |  o   o   o   o   o   o   o    |  <- Fila 1 (Y = -9.14m)
    +-------------------------------+
         MURO SUR (5 ventanas)

    7 columnas (dir. X): 1.17m a 7.65m
    9 filas (dir. Y): -9.14m a -0.50m
    Espaciado: 1.08m en ambas direcciones
    Altura plano de trabajo: 0.75m
```

Dimensiones del cuarto: 7.86m (E-O) x 9.57m (N-S)

## Estructura de Archivos

```
validacion-noviembre/
├── README.md                  # Este archivo
├── materials.rad              # Materiales calibracion combinada
├── scene.rad                  # Archivo de escena
├── points_validation.txt      # Grid de sensores (63 puntos) - generado
├── generate_sensor_grid.py    # Generador del grid de sensores
├── run_simulation.sh          # Script principal de simulacion
├── visualize_hourly_grid.py   # Visualizacion horaria multi-panel
├── create_room_scheme.py      # Diagrama esquematico del cuarto
├── objects/                   # Geometria del edificio
│   ├── scene.geom
│   ├── glazing.geom
│   └── *.blindgrp
├── skyDomes/
│   └── skyglow.rad            # Hemisferio cielo/suelo
├── skyVectors/
│   └── nelier_annual.smx      # Matriz de cielo anual (8760 x 146)
├── assets/
│   └── nelier.wea             # Archivo de clima
├── data/                      # Datos experimentales noviembre 20
│   ├── 09h.csv ... 17h.csv   # 9 archivos (horas 9-17)
├── octrees/                   # (generado por simulacion)
│   └── scene.oct
├── matrices/dc/               # (generado por simulacion)
│   └── illum.mtx
├── results/dc/                # (generado por simulacion)
│   └── annual.ill
└── images/                    # (generado por visualizacion)
```

## Instrucciones

### 1. Correr la Simulacion

```bash
cd validacion-noviembre
bash run_simulation.sh
```

Esto ejecuta los 4 pasos:
1. Genera el grid de sensores (points_validation.txt, 63 puntos)
2. Construye el octree con materiales calibrados (scene.oct)
3. Calcula coeficientes de luz natural (illum.mtx)
4. Genera iluminancia anual (annual.ill, 8760 x 63)

### 2. Visualizar Resultados

**Iluminancia horaria del 20 de noviembre:**
```bash
uv run python visualize_hourly_grid.py --date 2024-11-20 --output nov20.png
```

**Diagrama esquematico del cuarto:**
```bash
uv run python create_room_scheme.py
```

**Visualizar otra fecha:**
```bash
uv run python visualize_hourly_grid.py --date 2024-06-21 --output jun21.png
```

### 3. Leer Datos de Simulacion

```python
import numpy as np

# Cargar iluminancia anual
data = np.loadtxt('results/dc/annual.ill', skiprows=11)
# Shape: (8760, 63) - horas x sensores

# Cargar posiciones de sensores
sensors = np.loadtxt('points_validation.txt')
# Shape: (63, 6) - columnas: x, y, z, dx, dy, dz
```

### 4. Leer Datos Experimentales

Los archivos CSV en `data/` contienen mediciones de luximetro del 20 de noviembre:

```python
import pandas as pd

# Cargar medicion de las 12h
df = pd.read_csv('data/12h.csv')
# Columnas: I1N, I2N, I3N, I4N, I5N, I1S, I2S, I3S, I4S, I5S
# 7 filas (columnas este-oeste)
# Valores en klux (multiplicar por 1000 para lux)
```

Formato CSV:
- **Columnas**: I1N...I5N (ventanas norte), I1S...I5S (ventanas sur)
- **Filas**: 7 filas correspondientes a las columnas este-oeste del grid
- **Unidades**: klux

## Parametros de Simulacion

| Parametro | Valor |
|-----------|-------|
| Sensores | 63 (7 x 9) |
| Espaciado | 1.08 m |
| Altura plano trabajo | 0.75 m |
| Bounces ambientales (-ab) | 5 |
| Divisiones ambientales (-ad) | 10000 |
| Peso minimo (-lw) | 0.0001 |
| Hilos CPU (-n) | 8 |
| Patches de cielo | 146 (Reinhart m=1) |
| Coeficientes RGB->lux | 47.4, 119.9, 11.6 |

## Ubicacion

Temixco, Mexico (18.85 N, 99.14 W)
