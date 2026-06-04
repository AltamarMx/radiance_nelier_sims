"""
metrics.py — Métricas de validación experimental vs simulación.

Convención de signo (E_s = simulado, E_m = medido):

    NMBE = Σ(E_s - E_m) / Σ(E_m)        # residual = sim - exp
    NMAE = Σ|E_s - E_m| / Σ(E_m)

  -> NMBE positivo = simulación SOBREESTIMA respecto al experimento.

(Antes el residual era exp - sim, signo opuesto. Se cambió para coincidir con
la definición de NMBE/NMAE del paper. NMAE, CV(RMSE) y R² no dependen del signo.)

Métricas implementadas:
  - NMBE [%]      Normalized Mean Bias Error          (ASHRAE G14: |NMBE| <= 10)
  - CV(RMSE) [%]  Coef. de variación del RMSE          (ASHRAE G14: <= 30)
  - R^2           Coef. de determinación               (ASHRAE G14: > 0.85)
  - NMAE [%]      Error absoluto medio normalizado     (= MAE_norm; usado en GOF)
  - GOF [%]       sqrt(NMBE^2 + NMAE^2)                (objetivo a minimizar)
  - GOF_cvrmse [%] sqrt(NMBE^2 + CV(RMSE)^2)           (variante ASHRAE, referencia)
"""

import numpy as np


def _flatten(list_of_dfs):
    """Concatena DataFrames (lista) en un único array 1D."""
    return np.concatenate([df.values.flatten() for df in list_of_dfs])


def compute_metrics(exp_list, sim_list):
    """Calcula todas las métricas dado dos listas paralelas de DataFrames (por hora).

    Cada DataFrame es 7x9 (puntos x columnas de sensores). Se aplanan y comparan
    elemento a elemento.
    """
    exp = _flatten(exp_list)
    sim = _flatten(sim_list)

    n = len(exp)
    mean_exp = exp.mean()
    errors = sim - exp  # residual = E_s - E_m (NMBE>0 => sim sobreestima)

    nmbe = (errors.sum() / (n * mean_exp)) * 100.0
    rmse = np.sqrt((errors ** 2).mean())
    cvrmse = (rmse / mean_exp) * 100.0
    mae_norm = (np.abs(errors).mean() / mean_exp) * 100.0  # NMAE [%]

    ss_res = (errors ** 2).sum()
    ss_tot = ((exp - mean_exp) ** 2).sum()
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')

    # GOF objetivo: GOF = sqrt(NMBE^2 + NMAE^2)
    gof = np.sqrt(nmbe ** 2 + mae_norm ** 2)
    gof_cvrmse = np.sqrt(nmbe ** 2 + cvrmse ** 2)  # variante ASHRAE (referencia)

    meets_ashrae = bool(abs(nmbe) <= 10 and cvrmse <= 30)

    return {
        'n': n,
        'mean_exp': float(mean_exp),
        'rmse': float(rmse),
        'nmbe': float(nmbe),
        'cvrmse': float(cvrmse),
        'mae_norm': float(mae_norm),
        'nmae': float(mae_norm),
        'r2': float(r2),
        'gof': float(gof),
        'gof_cvrmse': float(gof_cvrmse),
        'meets_ashrae': meets_ashrae,
    }
