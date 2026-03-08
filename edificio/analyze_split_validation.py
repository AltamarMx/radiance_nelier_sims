#!/usr/bin/env python3
"""
analyze_split_validation.py - Split-sample calibration vs validation analysis

Compares three approaches:
  A) Calibrate with BOTH days (current approach): minimize GOF_avg
  B) Calibrate with June 26, validate with November 20
  C) Calibrate with November 20, validate with June 26

Uses existing grid_results_extended.csv (2,704 combinations).
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path

# Load results
results_dir = Path(__file__).parent / "results" / "parametric"
df = pd.read_csv(results_dir / "grid_results_extended.csv")
df = df[df['success'] == True].copy()

print(f"Total successful simulations: {len(df)}")
print()

# Compute per-day GOF (currently only combined GOF exists in the CSV)
df['gof_jun'] = np.sqrt(df['nmbe_jun']**2 + df['cvrmse_jun']**2)
df['gof_nov'] = np.sqrt(df['nmbe_nov']**2 + df['cvrmse_nov']**2)

# Also compute ASHRAE compliance per day
df['ashrae_jun'] = (df['nmbe_jun'].abs() <= 10) & (df['cvrmse_jun'] <= 30)
df['ashrae_nov'] = (df['nmbe_nov'].abs() <= 10) & (df['cvrmse_nov'] <= 30)

# ============================================================
# APPROACH A: Calibrate with BOTH days (current approach)
# ============================================================
idx_both = df['gof'].idxmin()
opt_both = df.loc[idx_both]

# ============================================================
# APPROACH B: Calibrate with June 26 only
# ============================================================
idx_jun = df['gof_jun'].idxmin()
opt_cal_jun = df.loc[idx_jun]

# ============================================================
# APPROACH C: Calibrate with November 20 only
# ============================================================
idx_nov = df['gof_nov'].idxmin()
opt_cal_nov = df.loc[idx_nov]


def print_approach(label, row, cal_day, val_day):
    """Print detailed metrics for an approach."""
    print(f"  Parameters:  tau={row['tau']:.2f}, rho_floor={row['rho_floor']:.2f}, rho_hall={row['rho_hall']:.2f}")
    print()

    # June metrics
    jun_label = f"{'[CAL]' if cal_day == 'jun' else '[VAL]' if val_day == 'jun' else '[---]'}"
    print(f"  June 26 {jun_label}:")
    print(f"    NMBE      = {row['nmbe_jun']:+.2f}%")
    print(f"    CV(RMSE)  = {row['cvrmse_jun']:.2f}%")
    print(f"    R²        = {row['r2_jun']:.4f}")
    print(f"    GOF       = {row['gof_jun']:.2f}%")
    ashrae_jun = abs(row['nmbe_jun']) <= 10 and row['cvrmse_jun'] <= 30
    print(f"    ASHRAE    = {'PASS' if ashrae_jun else 'FAIL'} (|NMBE|<=10%: {abs(row['nmbe_jun']):.1f}%, CV<=30%: {row['cvrmse_jun']:.1f}%)")

    print()

    # November metrics
    nov_label = f"{'[CAL]' if cal_day == 'nov' else '[VAL]' if val_day == 'nov' else '[---]'}"
    print(f"  Nov 20 {nov_label}:")
    print(f"    NMBE      = {row['nmbe_nov']:+.2f}%")
    print(f"    CV(RMSE)  = {row['cvrmse_nov']:.2f}%")
    print(f"    R²        = {row['r2_nov']:.4f}")
    print(f"    GOF       = {row['gof_nov']:.2f}%")
    ashrae_nov = abs(row['nmbe_nov']) <= 10 and row['cvrmse_nov'] <= 30
    print(f"    ASHRAE    = {'PASS' if ashrae_nov else 'FAIL'} (|NMBE|<=10%: {abs(row['nmbe_nov']):.1f}%, CV<=30%: {row['cvrmse_nov']:.1f}%)")

    print()

    # Combined
    print(f"  Combined (avg of both days):")
    print(f"    NMBE      = {row['nmbe_combined']:+.2f}%")
    print(f"    CV(RMSE)  = {row['cvrmse_combined']:.2f}%")
    print(f"    R²        = {row['r2_combined']:.4f}")
    print(f"    GOF       = {row['gof']:.2f}%")
    print()


# ============================================================
# PRINT RESULTS
# ============================================================
print("=" * 70)
print("SPLIT-SAMPLE CALIBRATION/VALIDATION ANALYSIS")
print("=" * 70)
print()

print("-" * 70)
print("APPROACH A: Calibrate with BOTH days (minimize GOF_combined)")
print("-" * 70)
print_approach("Both", opt_both, cal_day='both', val_day='both')

print("-" * 70)
print("APPROACH B: Calibrate with JUNE 26 → Validate with NOVEMBER 20")
print("-" * 70)
print_approach("Jun→Nov", opt_cal_jun, cal_day='jun', val_day='nov')

print("-" * 70)
print("APPROACH C: Calibrate with NOVEMBER 20 → Validate with JUNE 26")
print("-" * 70)
print_approach("Nov→Jun", opt_cal_nov, cal_day='nov', val_day='jun')


# ============================================================
# COMPARISON TABLE
# ============================================================
print("=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)
print()

header = f"{'Approach':<35} {'tau':>5} {'rho_f':>6} {'rho_h':>6} │ {'GOF_cal':>8} {'GOF_val':>8} {'GOF_avg':>8}"
print(header)
print("─" * len(header))

# Approach A
print(f"{'A: Both days (current)':<35} {opt_both['tau']:>5.2f} {opt_both['rho_floor']:>6.2f} {opt_both['rho_hall']:>6.2f} │ {'--':>8} {'--':>8} {opt_both['gof']:>8.2f}")

# Approach B: calibrate June, validate November
gof_cal_b = opt_cal_jun['gof_jun']
gof_val_b = opt_cal_jun['gof_nov']
gof_avg_b = (gof_cal_b + gof_val_b) / 2
print(f"{'B: Cal June → Val November':<35} {opt_cal_jun['tau']:>5.2f} {opt_cal_jun['rho_floor']:>6.2f} {opt_cal_jun['rho_hall']:>6.2f} │ {gof_cal_b:>8.2f} {gof_val_b:>8.2f} {gof_avg_b:>8.2f}")

# Approach C: calibrate November, validate June
gof_cal_c = opt_cal_nov['gof_nov']
gof_val_c = opt_cal_nov['gof_jun']
gof_avg_c = (gof_cal_c + gof_val_c) / 2
print(f"{'C: Cal November → Val June':<35} {opt_cal_nov['tau']:>5.2f} {opt_cal_nov['rho_floor']:>6.2f} {opt_cal_nov['rho_hall']:>6.2f} │ {gof_cal_c:>8.2f} {gof_val_c:>8.2f} {gof_avg_c:>8.2f}")

print()
print("GOF_cal = GOF on calibration day, GOF_val = GOF on validation day")
print()

# ============================================================
# KEY DIFFERENCES
# ============================================================
print("=" * 70)
print("KEY OBSERVATIONS")
print("=" * 70)
print()

# Check how much worse validation is vs calibration
diff_b = gof_val_b - gof_cal_b
diff_c = gof_val_c - gof_cal_c

print(f"Approach B: Validation GOF is {diff_b:+.2f}% {'worse' if diff_b > 0 else 'better'} than calibration GOF")
print(f"Approach C: Validation GOF is {diff_c:+.2f}% {'worse' if diff_c > 0 else 'better'} than calibration GOF")
print()

# Overfitting indicator
print("Overfitting assessment:")
print(f"  B (Jun→Nov): GOF gap = {abs(diff_b):.2f}%  {'← large gap suggests overfitting to June' if abs(diff_b) > 10 else '← moderate gap' if abs(diff_b) > 5 else '← small gap, good generalization'}")
print(f"  C (Nov→Jun): GOF gap = {abs(diff_c):.2f}%  {'← large gap suggests overfitting to November' if abs(diff_c) > 10 else '← moderate gap' if abs(diff_c) > 5 else '← small gap, good generalization'}")
print()

# Parameter stability
print("Parameter stability across approaches:")
taus = [opt_both['tau'], opt_cal_jun['tau'], opt_cal_nov['tau']]
rho_fs = [opt_both['rho_floor'], opt_cal_jun['rho_floor'], opt_cal_nov['rho_floor']]
rho_hs = [opt_both['rho_hall'], opt_cal_jun['rho_hall'], opt_cal_nov['rho_hall']]
print(f"  tau:      range [{min(taus):.2f}, {max(taus):.2f}], spread = {max(taus)-min(taus):.2f}")
print(f"  rho_floor: range [{min(rho_fs):.2f}, {max(rho_fs):.2f}], spread = {max(rho_fs)-min(rho_fs):.2f}")
print(f"  rho_hall:  range [{min(rho_hs):.2f}, {max(rho_hs):.2f}], spread = {max(rho_hs)-min(rho_hs):.2f}")
print()

if max(taus) - min(taus) <= 0.04 and max(rho_fs) - min(rho_fs) <= 0.04 and max(rho_hs) - min(rho_hs) <= 0.04:
    print("  → Parameters are STABLE: similar optimal values regardless of calibration day.")
    print("    This suggests robust calibration, not overfitted to a specific day.")
else:
    print("  → Parameters VARY across approaches: optimal values depend on which day is used.")
    print("    This suggests the two days have different characteristics that pull")
    print("    parameters in different directions.")
print()

# ============================================================
# TOP 5 FOR EACH APPROACH
# ============================================================
print("=" * 70)
print("TOP 5 PARAMETER SETS FOR EACH CALIBRATION APPROACH")
print("=" * 70)

for label, col, val_col in [
    ("Calibrate with June 26 (GOF_jun)", 'gof_jun', 'gof_nov'),
    ("Calibrate with November 20 (GOF_nov)", 'gof_nov', 'gof_jun'),
    ("Calibrate with Both (GOF_combined)", 'gof', None),
]:
    print(f"\n{label}:")
    top5 = df.nsmallest(5, col)
    for i, (_, row) in enumerate(top5.iterrows(), 1):
        if val_col:
            print(f"  {i}. tau={row['tau']:.2f}, rho_f={row['rho_floor']:.2f}, rho_h={row['rho_hall']:.2f} | "
                  f"GOF_cal={row[col]:.2f}%, GOF_val={row[val_col]:.2f}%, "
                  f"NMBE_jun={row['nmbe_jun']:+.1f}%, NMBE_nov={row['nmbe_nov']:+.1f}%")
        else:
            print(f"  {i}. tau={row['tau']:.2f}, rho_f={row['rho_floor']:.2f}, rho_h={row['rho_hall']:.2f} | "
                  f"GOF={row['gof']:.2f}%, "
                  f"GOF_jun={row['gof_jun']:.2f}%, GOF_nov={row['gof_nov']:.2f}%, "
                  f"NMBE_jun={row['nmbe_jun']:+.1f}%, NMBE_nov={row['nmbe_nov']:+.1f}%")

print()

# ============================================================
# ASHRAE COMPLIANCE CHECK
# ============================================================
print("=" * 70)
print("ASHRAE COMPLIANCE")
print("=" * 70)
print()

for label, row in [
    ("A: Both days", opt_both),
    ("B: Cal June → Val Nov", opt_cal_jun),
    ("C: Cal Nov → Val June", opt_cal_nov),
]:
    ashrae_jun = abs(row['nmbe_jun']) <= 10 and row['cvrmse_jun'] <= 30
    ashrae_nov = abs(row['nmbe_nov']) <= 10 and row['cvrmse_nov'] <= 30
    ashrae_both = abs(row['nmbe_combined']) <= 10 and row['cvrmse_combined'] <= 30
    print(f"  {label}:")
    print(f"    June ASHRAE:     {'PASS' if ashrae_jun else 'FAIL'}")
    print(f"    November ASHRAE: {'PASS' if ashrae_nov else 'FAIL'}")
    print(f"    Combined ASHRAE: {'PASS' if ashrae_both else 'FAIL'}")
    print()
