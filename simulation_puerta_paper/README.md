# simulation_puerta

Validación de simulación de iluminación natural con Radiance contra mediciones experimentales — preparada para incorporar la geometría de la puerta del salón en una segunda fase.

**Ubicación**: Temixco, Mexico (18.85°N, 99.14°W)
**Mediciones**: 26 junio 2024 y 20 noviembre 2024
**Rejilla de sensores**: 7 × 9 = 63 puntos a 0.75 m sobre el piso

## Cómo usar (dos pasos)

```bash
# 1) Pipeline Radiance — lento (~15-20 min con 8 cores), idempotente.
#    Genera octrees, DC matrices y archivos de iluminancia anual (.ill).
#    Solo se vuelve a correr cuando cambian geometría/materiales/weather.
bash scripts/run_radiance.sh

# 2) Análisis y reporte — rápido (~1 min). Carga los .ill, calcula
#    métricas, genera gráficas y produce el HTML.
quarto render index.qmd
```

El resultado del paso 2 es `_output/index.html`, que es el reporte y la documentación del proceso completo.

Para forzar regeneración total del paso 1:
```bash
rm -rf edificio/{octrees,matrices/dc,results/dc}/*
bash scripts/run_radiance.sh
```

Para correr una sola variante (más rápido para pruebas):
```bash
bash scripts/run_radiance.sh validation
```

## Requisitos

- **Radiance** (binarios en `PATH`): `oconv`, `rfluxmtx`, `dctimestep`, `rmtxop`, `gendaymtx`, `epw2wea`
- **Quarto** ≥ 1.4
- **Python** ≥ 3.11 con: `numpy`, `pandas`, `matplotlib`, `scipy`

## Estructura

```
simulation_puerta/
├── index.qmd            # Documento central: análisis + reporte (rápido)
├── _quarto.yml          # Configuración Quarto
├── scripts/
│   ├── run_radiance.sh  # Pipeline Radiance (lento, correr antes del qmd)
│   ├── generate_sensor_grid.py
│   └── lib/             # radiance_io.py, metrics.py
├── data/                # Insumos (experimental, weather) y procesados
├── edificio/            # Escena Radiance + artefactos regenerables
└── images/              # Visualizaciones generadas
```

Esta carpeta es **autocontenida** y **portable**: se puede mover a cualquier ruta y `quarto render index.qmd` sigue funcionando (los `.oct`, `.mtx`, `.ill` se regeneran).

## Fases

- **Fase 1 (actual)**: reproducir la validación con la geometría sin puerta y dejar todo limpio y reproducible.
- **Fase 2**: añadir la puerta del salón a la geometría, recalcular y comparar.
