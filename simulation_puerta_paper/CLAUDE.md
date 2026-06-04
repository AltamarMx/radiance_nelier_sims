# CLAUDE.md — simulation_puerta

Esta carpeta es **autocontenida** y **portable**. Nada en su código fuente debe depender de rutas absolutas (`/Users/...`) ni de archivos fuera de `simulation_puerta/`.

## Flujo de uso (dos pasos)

```bash
# 1) Pipeline Radiance — lento (~15-20 min), idempotente.
bash scripts/run_radiance.sh

# 2) Análisis y reporte — rápido.
quarto render index.qmd
```

`scripts/run_radiance.sh` es el **único lugar** donde viven los comandos `oconv`, `gendaymtx`, `rfluxmtx`, `dctimestep`. El `index.qmd` solo verifica que sus salidas existan y hace análisis (carga, métricas, plots).

`index.qmd` documenta el pipeline conceptualmente (qué hace cada paso, parámetros) pero **no lo ejecuta**.

## Reglas para futuros cambios

- **Sin rutas absolutas**. Python: `Path(__file__).resolve().parent` o paths relativos al cwd. Bash: `SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"`.
- **Insumos vs artefactos**:
  - Insumos (no se regeneran): `.rad`, `.geom`, `.epw`, `.csv` experimentales, `.smx`. Se commitean.
  - Artefactos (regenerables por el qmd): `.oct`, `.mtx`, `.ill`. Pueden borrarse y rehacerse.
- **Pipeline Radiance** vive solo en `scripts/run_radiance.sh` (no en chunks bash del qmd). El qmd solo lee sus salidas.
- La búsqueda paramétrica (88+ simulaciones) **no** vive en el qmd; corre en `scripts/run_parametric_search.py` y deposita un CSV que el qmd carga.

## Métricas (ASHRAE Guideline 14)

```
NMBE [%]    = 100 × Σ(sim - exp) / (n × mean(exp))     # |NMBE| ≤ 10
CV(RMSE) [%] = 100 × √(Σ(sim - exp)² / n) / mean(exp)  # ≤ 30
NMAE [%]    = 100 × mean(|sim - exp|) / mean(exp)       # error absoluto medio normalizado
R²          = 1 - SS_res / SS_tot                       # > 0.85
GOF [%]     = √(NMBE² + NMAE²)                          # objetivo: minimizar
```
NMBE positivo = simulación subestima.

## Datos experimentales — formato

- 1 CSV por hora en `data/experimental/{005_26Junio,006_20Nov}/`
- Matriz 7×10: columnas `I1N..I5N, I1S..I5S`. Unidad: kilolux (multiplicar ×1000).
- **Excluir `I5N`** (sensor defectuoso).
- **Invertir filas en horas impares** para alinear con el sistema de coordenadas.

## Variantes de materiales

| Variante | τ (vidrio) | ρ_floor | ρ_hall |
|----------|------------|---------|--------|
| `materials.rad` (original) | 0.88 | 0.65 | 0.36 |
| `materials_calibrated.rad` | 0.80 | 0.19 | 0.13 |
| `materials_jun_optimal.rad` | 0.82 | 0.11 | 0.17 |
| `materials_nov_optimal.rad` | 0.78 | 0.17 | 0.13 |

## Parámetros de simulación

| Comando | Flag | Valor |
|---------|------|-------|
| `rfluxmtx` | `-ab -ad -lw -n` | 5 / 10000 / 0.0001 / 8 |
| `gendaymtx` | `-m` | 1 (Reinhart 146). **Sin `-O1`**: la salida default (`-O0`, radiancia visible) es la que asume la conversión fotópica de `rmtxop`; con `-O1` (solar total) la iluminancia sale ~57% inflada |
| `rmtxop` | `-c` | 47.4 119.9 11.6 (RGB → lux fotópico) |

## Fase 2 (puerta) — pendiente

No tocar la geometría de la puerta hasta que la fase 1 esté validada (mismos números que el estudio previo, test de portabilidad pasando).
