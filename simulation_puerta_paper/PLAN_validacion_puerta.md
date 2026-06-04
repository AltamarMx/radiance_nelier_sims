# Plan de Validación con Puerta — Reconstrucción desde Cero

> Documento de planeación. Define cómo reconstruir la carpeta `simulation_puerta/` para que sea **autocontenida**, **portable** (se puede mover a cualquier ruta) y **reproducible desde cero**.
>
> **Núcleo del folder**: un `index.qmd` que documenta y ejecuta el proceso completo (literate programming) — desde correr los comandos de Radiance, cargar los archivos `.ill`, calcular métricas y graficar. Los `scripts/` son helpers que el `index.qmd` invoca o referencia, no el centro.
>
> **Punto de partida**: `validation/validation_gof.qmd` actual (ya tiene 11 secciones funcionales: carga, métricas ASHRAE, contornos, scatter, UDI, DGPs). Lo migramos y le añadimos la documentación de la cadena Radiance.

---

## 0. Decisiones tomadas

| # | Pregunta | Decisión |
|---|----------|----------|
| 1 | ¿Qué representa "puerta"? | Simulación que **incluirá** la puerta (geometría nueva), pero en una **fase 2**. Fase 1 reconstruye todo limpio con la geometría actual hasta que funcione. |
| 2 | Fechas de medición | **26 junio 2024** y **20 noviembre 2024** (las mismas del estudio actual) |
| 3 | Rejilla de sensores | **7 × 9 = 63 puntos**, espaciado 1.08 m, altura plano de trabajo 0.75 m (la misma) |
| 4 | Variable extra a calibrar (fase 2) | Por definir cuando entremos a la puerta — probablemente reflectancia ρ_door |
| 5 | Métrica objetivo | ASHRAE Guideline 14: \|NMBE\| ≤ 10 %, CV(RMSE) ≤ 30 %, R² > 0.85 |

---

## 1. Estrategia en dos fases

### **Fase 1 — Reconstruir limpio y portable con `index.qmd` como núcleo** (foco actual)

Crear `simulation_puerta/` que:
- Reproduzca exactamente los resultados de `validation/` actual
- Sea **autocontenida** (no depende de nada fuera del folder)
- Sea **portable** (`mv` a cualquier ruta y sigue funcionando)
- Esté **bien documentada** dentro de `index.qmd` (literate programming): cada paso explica el qué/por qué/cómo
- Tenga el **pipeline limpio** orquestado desde el `index.qmd`

**Criterio de aceptación de fase 1**: copiar el folder a `/tmp/test/`, abrir `index.qmd`, ejecutarlo de arriba a abajo, obtener `annual_validation.ill` numéricamente equivalente al actual y ASHRAE G14 con valores conocidos del estudio previo. El HTML renderizado es el reporte final.

### **Fase 2 — Añadir la puerta** (después de fase 1)

Una vez la fase 1 esté validada:
- Añadir `objects/door.geom` con la geometría de la puerta
- Añadir material(es) de puerta a `materials.rad`
- Recompilar octree, recalcular DC matrix, regenerar annual.ill
- Comparar contra mediciones experimentales (¿con la puerta en qué posición durante las mediciones?) — esto se decide al inicio de fase 2

**Importante**: hasta que fase 1 corra de extremo a extremo y se valide contra los números del estudio previo, **no se toca la geometría de la puerta**.

---

## 2. Estructura de carpeta propuesta

```
simulation_puerta/
├── index.qmd                     # ★ DOCUMENTO CENTRAL: literate programming
│                                 #   Documenta y ejecuta el proceso completo:
│                                 #   - Setup y dependencias
│                                 #   - Cómo correr Radiance (oconv, rfluxmtx, dctimestep)
│                                 #   - Carga de .ill y experimentales
│                                 #   - Métricas ASHRAE G14
│                                 #   - Visualizaciones (contornos, scatter, UDI, DGPs)
│                                 #   - Calibración paramétrica
│                                 #   Renderiza a index.html (reporte final)
│
├── _quarto.yml                   # Config Quarto (output formats, theme, ejecución)
├── README.md                     # Visión general corta (cómo abrir el index, requisitos)
├── CLAUDE.md                     # Guía para Claude Code (folder self-contained)
├── PLAN_validacion_puerta.md     # Este documento (referencia histórica)
│
├── data/
│   ├── experimental/
│   │   ├── 005_26Junio/          # CSV crudos por hora (10 archivos: 09h–18h)
│   │   └── 006_20Nov/            # CSV crudos por hora (9 archivos: 09h–17h)
│   ├── radiance/                 # CSV procesados (generados por index.qmd)
│   ├── parametric/               # Resultados de búsqueda por rejilla
│   └── weather/
│       ├── nelier_26jun_20novCST.epw
│       └── nelier.wea            # Generado por epw2wea
│
├── edificio/                     # Escena Radiance (todo relativo a este folder)
│   ├── scene.rad                 # Wrapper de la escena
│   ├── materials/
│   │   ├── materials.rad             # Original (DesignBuilder, sin puerta)
│   │   ├── materials_calibrated.rad  # Óptimo combinado (τ=0.76, ρ_floor=0.21, ρ_hall=0.29)
│   │   ├── materials_jun_optimal.rad # τ=0.80, ρ_floor=0.17, ρ_hall=0.13
│   │   └── materials_nov_optimal.rad # τ=0.70, ρ_floor=0.11, ρ_hall=0.17
│   ├── objects/
│   │   ├── scene.geom            # Geometría base (sin puerta en fase 1)
│   │   ├── glazing.geom          # Vidrios
│   │   └── *.blindgrp            # Persianas
│   ├── points/
│   │   └── points_validation.txt # 63 puntos (7×9, espaciado 1.08 m)
│   ├── skyDomes/skyglow.rad
│   ├── skyVectors/nelier_annual.smx
│   ├── octrees/                  # Generados (regenerables)
│   ├── matrices/dc/              # DC matrices (regenerables)
│   └── results/dc/               # .ill anuales (regenerables)
│
├── scripts/                      # Helpers invocados desde index.qmd o desde shell
│   ├── lib/
│   │   ├── radiance_io.py        # Parse de .ill, .mtx, .smx (importado en qmd)
│   │   └── metrics.py            # ASHRAE G14 (importado en qmd)
│   ├── generate_sensor_grid.py   # Genera points/points_validation.txt
│   ├── run_radiance_pipeline.sh  # Orquesta oconv + rfluxmtx + dctimestep para 1 variant
│   │                             # (también documentado dentro del index.qmd como bash chunks)
│   └── run_parametric_search.py  # Grid search (largo; no se corre dentro del qmd)
│
└── images/                       # Visualizaciones generadas (auxiliares al qmd)
```

**Decisiones clave de esta estructura:**

- **`index.qmd` es el centro** — abrirlo y leerlo equivale a entender todo el pipeline. Renderizarlo equivale a ejecutar la validación. No hay un PDF/MD aparte — el HTML del `index.qmd` ES el reporte.
- **Sin `docs/`** — la documentación vive en el `index.qmd` (en prosa intercalada con código). Solo un README corto que dice "abre `index.qmd`".
- **Scripts mínimos** — solo lo que no es eficiente meter en el qmd: la búsqueda paramétrica (3+ horas de cómputo) y orquestación shell. La librería (`scripts/lib/`) la importa el qmd.
- **`_quarto.yml`** controla la ejecución: por default `freeze: auto` para no recomputar lo lento (rfluxmtx) en cada render, pero permite forzar.
- Todo path en código fuente es **relativo** al script o a la raíz del folder. **Nunca** rutas absolutas.
- Los `.oct`, `.mtx`, `.ill` son **regenerables**; los `.rad`, `.geom`, `.epw`, `.csv` experimentales son **insumos**.

---

## 2.1 Estructura propuesta de `index.qmd`

Punto de partida: `validation/validation_gof.qmd` actual (1163 líneas, 11 secciones funcionales). Se migra y se le **añaden secciones de cadena Radiance** (que hoy no están en el qmd).

### Tabla de contenido del `index.qmd`

| § | Sección | Origen | Tipo de chunk |
|---|---------|--------|---------------|
| 1 | **Introducción** — objetivo, ubicación, fechas, escenario "puerta" | Nuevo + intro de `gof.qmd` | prosa |
| 2 | **Setup** — paths, librerías, deps | `gof.qmd §2` | `python` |
| 3 | **Insumos del modelo** — geometría, materiales, weather, sky | Nuevo | prosa + `bash --eval=false` para mostrar comandos |
| 4 | **Generar rejilla de sensores** — `generate_sensor_grid.py` | Nuevo | `python` (importa script) |
| 5 | **Construir octree** — `oconv mat scene objects → scene.oct` | **Nuevo** | `bash` con freeze |
| 6 | **Calcular DC matrix** — `rfluxmtx -ab 5 -ad 10000 ...` | **Nuevo** | `bash` con freeze (lento) |
| 7 | **Generar sky matrix** — `epw2wea + gendaymtx -m 1 -O1` | **Nuevo** | `bash` con freeze |
| 8 | **Generar iluminancia anual** — `dctimestep \| rmtxop -c 47.4 119.9 11.6` | **Nuevo** | `bash` con freeze |
| 9 | **Cargar datos** — experimentales y .ill simulados (4 variants) | `gof.qmd §3` | `python` |
| 10 | **Esquema de salón y rejilla** — diagrama de planta | `gof.qmd §3.1` | `python` (matplotlib) |
| 11 | **Métricas ASHRAE G14** — NMBE, CV(RMSE), R², GOF | `gof.qmd §4` | `python` |
| 12 | **Análisis cross-validation** — entrenar en jun, evaluar en nov (y viceversa) | `gof.qmd §5` | `python` |
| 13 | **Mapas de contorno** — exp vs sim para 26jun y 20nov por hora | `gof.qmd §6` | `python` |
| 14 | **Scatter plots** — exp vs sim, línea 1:1 | `gof.qmd §7` | `python` |
| 15 | **Comparación horaria** — promedio espacial por hora | `gof.qmd §8` | `python` |
| 16 | **Mapa de confort temporal** — % área en 300–2000 lux | `gof.qmd §9` | `python` |
| 17 | **UDI** — useful daylight illuminance, rejilla 480 puntos | `gof.qmd §9.1` | `python` |
| 18 | **DGPs** — simplified daylight glare probability | `gof.qmd §10` | `python` |
| 19 | **Resumen y conclusiones** — tabla final, cumplimiento ASHRAE | `gof.qmd §11` | `python` + prosa |
| 20 | **Próximos pasos: añadir puerta** | Nuevo (placeholder fase 2) | prosa |

### Cómo se manejan los pasos lentos de Radiance

Los chunks `bash` que invocan `rfluxmtx`, `oconv`, `dctimestep` son lentos (minutos). Se manejan con dos estrategias combinadas:

1. **`freeze: auto`** en `_quarto.yml` → solo recomputa el chunk si su código cambia. Tras el primer render, los siguientes son rápidos.
2. **Detección de archivo existente** dentro del chunk:
   ```bash
   if [ ! -f octrees/scene_validation.oct ]; then
       oconv ... > octrees/scene_validation.oct
   else
       echo "Skipping: octrees/scene_validation.oct already exists"
   fi
   ```
   Para forzar regeneración: `rm` el archivo y re-renderizar, o `quarto render --no-freeze`.

3. **El grid paramétrico (88+ simulaciones) NO va en el qmd** — vive en `scripts/run_parametric_search.py` y se invoca aparte. El qmd solo carga `data/parametric/grid_results.csv` para visualizar.

### Convención de chunks bash

Los chunks `bash` que documentan comandos pero **no deben ejecutarse** en cada render se marcan:

````
```{bash}
#| eval: false
#| echo: true
oconv materials/materials.rad scene.rad objects/scene.geom > octrees/scene.oct
```
````

Los que **sí ejecutan** y son idempotentes:

````
```{bash}
#| eval: true
#| cache: true
[ -f octrees/scene_validation.oct ] || oconv ... > octrees/scene_validation.oct
```
````

---

## 3. Convenciones de nomenclatura

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| Materiales | `materials_<variant>.rad` | `materials_calibrated.rad` |
| Octrees | `octrees/scene_<variant>.oct` | `scene_jun_optimal.oct` |
| DC matrix | `matrices/dc/illum_<variant>.mtx` | `illum_validation.mtx` |
| Iluminancia anual | `results/dc/annual_<variant>.ill` | `annual_validation.ill` |

`<variant>` ∈ `{validation, calibrated, jun_optimal, nov_optimal}` en fase 1.
En fase 2 se añadirá `{simulation_puerta, calibrated_puerta, ...}`.

---

## 4. Reglas de portabilidad

Para que `mv simulation_puerta /otra/ruta` siga funcionando:

1. **Bash**: todos los scripts empiezan con
   ```bash
   set -e
   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
   ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
   cd "$ROOT/edificio"
   ```
2. **Python**: todos los scripts resuelven paths con
   ```python
   from pathlib import Path
   ROOT = Path(__file__).resolve().parent.parent
   EDIFICIO = ROOT / "edificio"
   DATA = ROOT / "data"
   ```
3. **Quarto**: los `.qmd` usan `Path("edificio")` relativo al cwd y se renderizan **desde la raíz del folder**.
4. **Sin** rutas hard-codeadas a `/Users/...` ni a la ruta original del proyecto.
5. Los `.oct` registran paths con los que se compilaron — por eso se regeneran tras un `mv`. Documentar en `docs/PORTABILITY.md`.

**Test de portabilidad** (sección 9):
```bash
cp -R simulation_puerta /tmp/test
cd /tmp/test
rm -rf edificio/octrees/* edificio/matrices/dc/* edificio/results/dc/*
bash scripts/run_all.sh
```
Debe producir resultados numéricamente equivalentes (tolerancia ~1e-6).

---

## 5. Pipeline (fase 1)

El pipeline se ejecuta **renderizando `index.qmd`**. Todos los pasos viven dentro del qmd como chunks (Python o Bash). El orden lógico es:

```
quarto render index.qmd
   │
   ├─► §2  Setup (python)         imports, verificar Radiance en PATH
   ├─► §3  Insumos (bash echo)    documenta inputs (no ejecuta)
   ├─► §4  Sensor grid (python)   importa scripts/generate_sensor_grid.py
   ├─► §5  Octree (bash)          oconv → scene_<variant>.oct          [cache/freeze]
   ├─► §6  Sky matrix (bash)      epw2wea + gendaymtx → .smx           [cache/freeze]
   ├─► §7  DC matrix (bash)       rfluxmtx → illum_<variant>.mtx       [cache/freeze, lento]
   ├─► §8  Annual illuminance     dctimestep | rmtxop → annual_*.ill   [cache/freeze]
   ├─► §9–18 Análisis (python)    carga, métricas, plots, UDI, DGPs
   └─► §19 Resumen
   
   → produce: index.html (reporte) + edificio/{octrees,matrices,results}/* (artefactos)
```

**Búsqueda paramétrica (88+ simulaciones, 3+ horas)** se ejecuta aparte:
```bash
python scripts/run_parametric_search.py
```
Genera `data/parametric/grid_results.csv` que el `index.qmd` carga y visualiza.

---

## 6. Parámetros de simulación (referencia)

| Comando | Flag | Valor | Justificación |
|---------|------|-------|---------------|
| `rfluxmtx` | `-ab` | 5 | Rebotes ambient suficientes para salón con vidrio claro |
| `rfluxmtx` | `-ad` | 10000 | Divisiones ambient (precisión vs tiempo) |
| `rfluxmtx` | `-lw` | 0.0001 | Cutoff de peso de luz |
| `rfluxmtx` | `-n` | 8 | Hilos CPU (ajustar a la máquina) |
| `gendaymtx` | `-m` | 1 | Reinhart subdivision (146 patches) |
| `gendaymtx` | `-O1` | — | Sol + cielo |
| `rmtxop` | `-c` | 47.4 119.9 11.6 | RGB → lux fotópico |

Tiempo estimado por variant (63 sensores, 8 cores): ~3–5 min para `rfluxmtx`. Para 4 variants: ~15–20 min total.

---

## 7. Datos experimentales

### Formato crudo
- 1 archivo CSV por hora (`09h.csv` … `18h.csv` jun, `09h.csv` … `17h.csv` nov)
- Matriz 7×10: columnas `I1N, I2N, I3N, I4N, I5N, I1S, I2S, I3S, I4S, I5S`
- Unidades: kilolux (multiplicar ×1000 para lux)

### Tratamiento conocido
- **Excluir `I5N`** (sensor defectuoso: ~60 klux en jun, ceros en nov)
- **Invertir filas** en horas impares para alinear con sistema de coordenadas
- Convertir klux → lux antes de comparar

Documentar todo en `docs/EXPERIMENTAL_PROTOCOL.md`.

---

## 8. Métricas (ASHRAE Guideline 14)

```
NMBE [%]    = 100 × Σ(sim - exp) / (n × mean(exp))     # |NMBE| ≤ 10
CV(RMSE) [%] = 100 × √(Σ(sim - exp)² / n) / mean(exp)  # ≤ 30
R²          = 1 - SS_res / SS_tot                       # > 0.85
GOF [%]     = √(NMBE² + CV(RMSE)²)                      # objetivo: minimizar
```

**Convención**: NMBE positivo = simulación subestima. NMBE negativo = simulación sobreestima.

---

## 9. Test de portabilidad (definición de "fase 1 lista")

```bash
# 1. Copiar el folder a una ruta nueva
cp -R simulation_puerta /tmp/test_portable
cd /tmp/test_portable

# 2. Limpiar artefactos regenerables
rm -rf edificio/octrees/* edificio/matrices/dc/* edificio/results/dc/*
rm -rf _freeze/   # cache de Quarto
rm -f data/weather/nelier.wea edificio/skyVectors/nelier_annual.smx

# 3. Renderizar el documento central (esto ejecuta todo el pipeline)
quarto render index.qmd

# 4. Verificar que el HTML existe y los .ill se regeneraron
test -f index.html
test -f edificio/results/dc/annual_validation.ill

# 5. Comparar contra baseline (ruta original) con tolerancia numérica
diff <(head -100 edificio/results/dc/annual_validation.ill) \
     <(head -100 /Users/gbv/radiance_nelier_sims/validation/edificio/results/dc/annual_validation.ill)
# Debe coincidir (tolerancia ~1e-6)

# 6. Verificar métricas ASHRAE conocidas en index.html
# (las tablas del HTML deben mostrar los mismos NMBE/CV(RMSE) del estudio previo)
```

Si los 6 pasos pasan ✅ fase 1 está lista.

---

## 10. Cronograma sugerido (fase 1)

| Paso | Duración estimada | Entregable |
|------|-------------------|------------|
| 1. Crear estructura `simulation_puerta/` y READMEs | 1–2 h | Carpeta con docs base |
| 2. Copiar/limpiar insumos (rad, geom, csv, epw) | 1 h | Insumos en sus carpetas |
| 3. Scripts 00–02 (setup, grid, sky matrix) | 2 h | Sky matrix regenerada |
| 4. Scripts 03–05 (octree, DC, annual.ill) por 4 variants | 3 h | 4 .ill regenerados |
| 5. Script 06 (comparación experimental) + lib/metrics | 3 h | Métricas reproducidas |
| 6. Script run_all.sh + test de portabilidad | 2 h | Pipeline portable |
| 7. Reporte Quarto migrado | 3 h | HTML final |
| **Total fase 1** | **~2–3 días de trabajo** | Folder validado |

(Fase 2 se cronograma cuando empecemos.)

---

## 11. Qué heredar de `validation/` actual

**Reusar tal cual:**
- `data/experimental/005_26Junio/`, `006_20Nov/`
- Weather: `nelier_26jun_20novCST.epw`
- Geometría: `objects/scene.geom`, `glazing.geom`, `*.blindgrp`
- Sky dome: `skyDomes/skyglow.rad`
- Materiales: los 4 `.rad` (con limpieza/reorganización en `materials/`)
- Lógica de `scripts/run_parametric_grid_gof.py` (es el único parametrico bien hecho)
- Patrón de `scripts/run_udi_simulations.sh` para los `.sh`

**Reescribir con paths corregidos:**
- Todos los demás `.sh` y `.py` (los que tenían `cd` o `edificio_dir` mal)
- `validation_report.qmd` y `validation_gof.qmd` (verificar paths relativos)

**No traer:**
- `scripts/octrees/`, `scripts/matrices/`, `scripts/results/` (basura)
- Octrees viejos (`scene_parametric.oct`) — se regeneran

---

## 12. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Resultados numéricos no coinciden tras reconstrucción | Test de portabilidad con tolerancia. Si difieren, comparar parámetros de `rfluxmtx` y orden de objetos en `oconv` |
| Cómputo de calibración muy largo | Grid grueso primero, usar resultados existentes si los parámetros no cambian |
| Cambios de versión de Radiance | Pinear versión en `00_setup.sh`, documentar en `docs/METHODOLOGY.md` |
| Quarto falla por falta de paquetes Python | `pyproject.toml` debe declarar todas las deps; test de portabilidad valida |
| Olvido de algún insumo al migrar | Checklist explícito en el script de migración (paso 2 de cronograma) |

---

## 13. Próximos pasos inmediatos

1. **Tú**: revisar este plan y aprobar/ajustar.
2. **Yo (Claude)**: cuando apruebes, crear `simulation_puerta/` con la estructura de la sección 2, READMEs base y scripts 00–02.
3. **Yo (Claude)**: implementar 03–05, correr para `variant=validation` y verificar contra el `annual_validation.ill` actual.
4. **Yo (Claude)**: implementar 06, reproducir métricas ASHRAE conocidas.
5. **Yo (Claude)**: implementar `run_all.sh` y correr test de portabilidad.
6. **Yo (Claude)**: migrar reporte Quarto.
7. **Tú**: revisar reporte final → aprobar fase 1.
8. **Tú + yo**: definir geometría/material de puerta → empezar fase 2.
