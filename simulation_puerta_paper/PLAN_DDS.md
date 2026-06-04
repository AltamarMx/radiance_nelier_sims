# Plan: preservar resultados validados e implementar corrección de sol directo (DDS)

**Fecha**: 2026-06-04
**Estado**: PROPUESTA — pendiente de aprobación
**Contexto**: la simulación 2PM está calibrada (26 jun 2024) y validada (20 nov 2024).
Antes de cualquier mejora, hay que proteger ese estado; después, evaluar si el
tratamiento explícito del sol directo (modelo DDS) mejora la fidelidad del modelo.

---

## 0. Antecedentes (hallazgos del 2026-06-04)

1. **Bug latente `-O1` (ya corregido).** `run_radiance.sh` generaba el sky matrix con
   `gendaymtx -m 1 -O1` (radiancia solar total), pero la conversión fotópica
   `rmtxop -c 47.4 119.9 11.6` (179 lm/W) asume radiancia **visible** (`-O0`, default).
   Verificado empíricamente: con `-O1` la iluminancia saldría **~57% inflada**
   (26 jun 12:00: 3,762 lx vs 2,382 lx; ratio anual medio 1.52).
   - Los resultados actuales **no** están afectados: el header de
     `edificio/skyVectors/nelier_annual.smx` confirma que se generó con
     `gendaymtx -m 1` (sin `-O1`) y la idempotencia del script nunca lo regeneró.
   - Corregido en: `scripts/run_radiance.sh`, `index_v2.qmd`, `CLAUDE.md`.
2. **El folder no está en git.** `simulation_puerta_paper/` aparece como untracked:
   105 MB de resultados, 8 h de búsqueda paramétrica y las figuras del paper no
   tienen ni un commit. Este es el riesgo #1.
3. **Limitación del 2PM con `-m 1`** (motivación del DDS): los 146 parches Reinhart
   difuminan el disco solar (0.53°) sobre un parche de ~12°×12°. Para UDI anual es
   aceptable, pero la calibración compara **horas puntuales contra luxómetros** en
   Temixco (cielos mayormente despejados, componente directa fuerte por ventanas
   N/S). El error de posición/nitidez de las manchas de sol lo absorbe la búsqueda
   paramétrica en parámetros poco físicos (ρ_floor 0.65→0.17, τ 0.88→0.82), y al
   ser estacional podría explicar por qué `jun_optimal` ≠ `nov_optimal`.

Referencia: tutorial LBNL de métodos matriciales (Subramaniam 2017),
`radTutorialFiles-master/room/commands/2PM_DDS.sh` — implementación Radiance del
modelo DDS (Bourgeois, Reinhart & Ward, 2008, *Building Research & Information* 36.1).

---

## Fase 1 — Congelar el estado validado (ANTES de tocar nada)

```bash
cd /Users/gbv/radiance_nelier_sims
git add simulation_puerta_paper/
git commit -m "Estado validado 2PM: calibración jun (GOF mín) + validación nov + evaluación anual"
git tag v1-2pm-validado
git push origin main --tags
```

- **Se commitea todo, incluidos artefactos** (`.ill`, `.mtx`, `.oct`, `.smx`).
  Ningún archivo supera el límite de GitHub (máximo: `annual_jun_optimal_480.ill`,
  60 MB < 100 MB). Aunque CLAUDE.md los declara regenerables, son la evidencia
  exacta de las cifras del paper y regenerarlos cuesta 15–20 min por corrida.
- Irreemplazables (prioridad absoluta en cualquier escenario):
  `data/experimental/`, `data/parametric/grid_results*.csv` (8 h de cómputo),
  `edificio/skyVectors/nelier_annual.smx` (el correcto, sin `-O1`),
  `img_paper/`, `edificio/materials/materials_*.rad`.
- El tag da un punto de retorno con nombre: `git checkout v1-2pm-validado`
  recupera el estado del paper, siempre.

**Criterio de salida**: `git status` limpio para `simulation_puerta_paper/` y tag
visible en `git tag -l`.

## Fase 2 — Rama de trabajo

```bash
git checkout -b dds-direct-sun
```

Todo el experimento DDS vive en la rama. Si mejora → merge a `main`; si no → la
rama queda como registro y `main` nunca se enteró.

## Fase 3 — Implementación DDS (solo aditiva, nunca sobrescribir)

El modelo DDS descompone la iluminancia en tres corridas y las combina:

```
E_DDS = E_total(2PM, ab5, m1) − E_directa(escena negra, ab1, m1) + E_sol(rcontrib, discos solares reales, ab1)
```

La 1ª corrida **ya existe** (es el 2PM actual). Las 2 nuevas son `-ab 1` → rápidas.

### 3.1 Insumos nuevos

| Archivo | Contenido |
|---------|-----------|
| `edificio/materials/materials_black.rad` | Todos los materiales opacos en `plastic 0 0 0` (negro); el **vidrio conserva su τ real** para que el sol directo entre |
| `edificio/skies/suns_MF6.rad` | 5,165 discos solares (subdivisión MF:6): `cnt 5165 \| rcalc -e MF:6 -f reinsrc.cal ...` |

### 3.2 Artefactos nuevos (sufijos — los existentes NO se tocan)

| Paso | Comando | Salida nueva |
|------|---------|--------------|
| Octree negro | `oconv materials_black.rad + vidrio real` | `octrees/scene_<v>_black.oct` |
| Octree negro + soles | `oconv -f ... suns_MF6.rad` | `octrees/scene_<v>_suns.oct` |
| DC directa | `rfluxmtx -ab 1 -ad 10000` (skyglow m1) | `matrices/dcd/illum_<v>_direct.mtx` |
| Coef. de sol | `rcontrib -ab 1 -ad 256 -dc 1 -dt 0 -dj 0 -e MF:6 -f reinhart.cal -b rbin -m solar` | `matrices/cds/cds_<v>.mtx` |
| Sun matrix | `gendaymtx -5 0.533 -d -m 6` (sin `-O1`) | `skyVectors/nelier_sun_m6.smx` |
| Sky matrix directa | `gendaymtx -m 1 -d` (sin `-O1`) | `skyVectors/nelier_direct.smx` |
| Combinación | `rmtxop total + -s -1 directa + sol` | `results/dc/annual_<v>_dds.ill` |

- Script: `scripts/run_radiance_dds.sh` (nuevo), misma estructura idempotente que
  `run_radiance.sh`. **No se modifica** `run_radiance.sh` más allá del fix `-O1` ya hecho.
- `index_v2.qmd` **no se toca**: la comparación 2PM vs DDS va en `compare_dds.qmd`
  (documento nuevo) que carga ambos `.ill`.
- Precedente de la convención: `annual_jun_optimal_dgps.ill` ya coexiste sin conflicto.

### 3.3 Orden de ejecución (mínimo primero)

1. Variante `validation` (materiales originales, sin calibrar) con DDS.
2. Comparar métricas jun/nov del modelo original: 2PM vs DDS.
   - **Si DDS mejora** NMBE/GOF del modelo *sin calibrar* → el error de sol directo
     era real → continuar al paso 3.
   - **Si no mejora** → documentar el resultado negativo en `compare_dds.qmd`,
     archivar la rama, fin.
3. Re-correr la búsqueda paramétrica sobre el pipeline DDS
   (`run_parametric_search.py` adaptado, CSV nuevo:
   `data/parametric/grid_results_dds_<fecha>.csv`).
4. Evaluar: ¿parámetros óptimos más físicos? ¿mejor transferencia jun→nov
   (óptimos de jun y nov más cercanos entre sí)?

## Fase 4 — Decisión y cierre

| Resultado | Acción |
|-----------|--------|
| DDS mejora GOF y/o da parámetros más físicos | Merge a `main`, tag `v2-dds`, actualizar paper |
| DDS no mejora (o empata) | Resultado negativo documentado en `compare_dds.qmd`; rama archivada; `main` intacto en `v1-2pm-validado` |

En ambos casos el estado del paper sigue recuperable con `git checkout v1-2pm-validado`.

## Reglas de seguridad permanentes

1. **Nunca sobrescribir** un `.ill`/`.mtx`/`.oct` existente: variante nueva ⇒ nombre nuevo.
2. **No borrar** `edificio/{octrees,matrices,results}` como "limpieza" mientras la
   rama DDS esté activa.
3. **No alterar timestamps** de insumos sin cambio real (`touch`, re-guardar sin
   editar): dispararía regeneraciones idempotentes en cadena.
4. Cualquier sky matrix nuevo: **sin `-O1`** (ver Antecedentes, punto 1).
5. Commit al final de cada fase, no solo al final del proyecto.

## Estimación de tiempos

| Tarea | Tiempo |
|-------|--------|
| Fase 1 (commit + tag + push) | 5 min |
| materials_black.rad + suns + script DDS | ~1 h de implementación |
| Corridas DDS por variante (2 × `-ab 1`) | ~5–10 min |
| Comparación 2PM vs DDS (1 variante) | ~30 min |
| Re-búsqueda paramétrica DDS (si procede) | ~horas (como la original, pero las corridas extra son `-ab 1`) |
