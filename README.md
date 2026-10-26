# La Niña × energy watch

**Research / watch only. No paper trading. No live trading. No orders.**

Public companion to [alt-signal-research](https://github.com/karthikvepuriphoto-gif/alt-signal-research) Phase 1–2 ENSO findings (crude & energy-state firms in La Niña). Rules were **preregistered** in [`PREREGISTRATION.md`](PREREGISTRATION.md) and committed **before** the backtest (`2b078e4`, 2026-10-25 21:00 CDT).

## Decision (vs prereg success criteria)

| Criterion | Result |
|---|---|
| U1 OOS Sharpe > 0.30 | **Fail** — OOS 2016+ Sharpe = **0.26** |
| H1 oil-hedged OOS t > 1.5 | Pass — OOS t = **1.84** |
| El Niño control (C1) not stronger than U1 | Pass — C1 full Sharpe −0.12 vs U1 +0.33 |
| Not driven only by 2021–22 | **Fail** — H1 Sharpe without 2021–22 = **−0.11** |

**Recommendation: not even watch.** The unhedged sleeve misses the OOS Sharpe bar; the oil-hedged residual is almost entirely the 2021–22 energy shock; and the hypothesis was chosen after seeing EN2 among 310 prior tests (BH q≈0.15, did not survive 5%). Keep the code as a negative / archival result.

## Preregistered rules (summary)

- **Signal:** NOAA CPC ONI, usable at end of month after season-end (**LAG=1**). La Niña = ONI ≤ −0.5 for **5 consecutive** overlapping seasons (CPC-style, real-time).
- **Entry / exit:** month-end close when the 5-season condition is first met / first broken.
- **U1:** long equal-weight EQ basket (`XLE, XOP, OIH, XES, IEO, FCG` + coal `BTU, AMR, ACI`) in La Niña; **cash** otherwise. 10 bp on flips / turnover.
- **H1 (primary science test):** same window, long EQ short β̂·CL (β from prior ~36 months of daily returns; median β≈0.50), plus 10 bp/month roll proxy and 5 bp on |Δβ|.
- **Controls:** C1 = same rules in El Niño; also neutral-month EQ means.
- **Costs, IS/OOS (2016 and 2019), leave-out 2021–22, threshold/streak/lag grid:** see prereg and `results/`.

## Results (net of costs, sample with ≥3 EQ names and CL, ~2006–2026, n=245 months)

| Strategy | n | CAGR | Sharpe | MaxDD | NW t | OOS CAGR | OOS Sharpe | OOS t |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| U1_EQ_cash | 245 | 5.4% | 0.33 | -19.5% | 2.40 | 5.3% | 0.26 | 1.72 |
| U2_STATE_cash | 245 | 4.4% | 0.27 | -21.3% | 2.15 | 4.4% | 0.20 | 1.54 |
| U3_EQ_SPY | 245 | 15.6% | 0.77 | -53.1% | 4.28 | 19.7% | 0.91 | 5.37 |
| H1_EQ_oilhedged | 245 | 3.6% | 0.23 | -15.7% | 2.05 | 5.6% | 0.30 | 1.84 |
| H2_STATE_oilhedged | 245 | 2.8% | 0.16 | -17.6% | 1.63 | 4.7% | 0.24 | 1.59 |
| H3_EQ_residual | 245 | 3.3% | 0.20 | -15.7% | 1.91 | 5.7% | 0.30 | 1.86 |
| C1_ElNino_EQ_cash | 245 | -1.1% | -0.12 | -53.9% | -0.04 | 1.7% | 0.04 | 0.59 |
| BH_SPY | 245 | 11.2% | 0.67 | -50.8% | 3.49 | 14.7% | 0.84 | 4.52 |
| BH_XLE | 245 | 7.7% | 0.35 | -64.0% | 1.98 | 12.3% | 0.46 | 2.14 |

**Active months only (descriptive):** EQ basket mean **+3.34%/month** in La Niña (n=47, Sharpe 1.27) vs **+0.04%** in El Niño (n=44) vs **+0.52%** in neutral. Crude (`CL`) itself is **+2.07%/month** in La Niña, so much of the equity move is oil. XLE−CL in La Niña is only **+0.47%/month** (Sharpe 0.24).

### Oil-hedged alpha (monthly regression, OOS 2016+)

| | Ann. α | t | β |
|---|---:|---:|---:|
| U1 vs SPY | 2.4% | 0.71 | 0.25 |
| U1 vs XLE | 3.5% | 1.17 | 0.17 |
| H1 vs SPY | 2.9% | 1.05 | 0.22 |
| H1 vs XLE | 3.9% | 1.57 | 0.14 |

H1 vs XLE OOS α ≈ 3.9%/yr (t 1.57) — does not clear conventional significance once oil and XLE are controlled, and vanishes without 2021–22.

### Leave-out 2021–22 (exploratory)

| | CAGR | Sharpe | NW t |
|---|---:|---:|---:|
| U1_no_2021_22 | 2.9% | 0.17 | 1.62 |
| U1_full | 5.4% | 0.33 | 2.40 |
| H1_no_2021_22 | 1.0% | -0.11 | 1.16 |
| H1_full | 3.6% | 0.23 | 2.05 |

## Charts

- [`charts/equity_curves.png`](charts/equity_curves.png) — U1, U2, H1 vs SPY and XLE buy-and-hold (log); ONI with La Niña bands.
- [`charts/hedged_vs_unhedged.png`](charts/hedged_vs_unhedged.png) — U1 vs H1.

## Current status

See [`current_status.md`](current_status.md). Refresh anytime:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python watch.py
```

`watch.py` pulls NOAA CPC `oni.ascii.txt`, applies LAG=1 and the 5-season rule, and prints whether the rules would hold the energy basket or cash. **It never places orders.**

## Reproduce the backtest

```bash
# prices are downloaded on first run of backtest (or restore data/prices.parquet)
python - <<'PY'
import yfinance as yf, pandas as pd
eq="XLE XOP OIH XES IEO FCG BTU AMR ACI SPY USO".split()
st="APA AR CHRD COP CVX DVN EOG EXE FANG HAL MTDR MUR OVV OXY PR PSX RRC SLB VLO VNOM XOM".split()
d=yf.download(eq+st+["CL=F"],start="1999-12-01",auto_adjust=True,progress=False)["Close"]
d=d.rename(columns={"CL=F":"CL"})
d.to_parquet("data/prices.parquet")
PY
curl -s "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3" -o data/dtb3.csv
python backtest.py
```

## Multiple-testing / selection note

This repo exists because Phase 1 crude-in-La-Niña and Phase 2 EN2 looked interesting among **310** tests. EN2’s BH q-value was ≈0.15 (not a 5% survivor). Treating a cleaned-up version as a new independent discovery would be false. Numbers here are for transparency and for a pre-registered kill-criteria check — which the strategy fails.

## Caveats

- Survivorship: STATE names are today’s S&P-ish energy list, not point-in-time.
- `CL=F` is a Yahoo continuous contract, not a careful back-adjusted series; roll cost is a flat 10 bp/month proxy.
- KOL delisted; coal sleeve is BTU/AMR/ACI only (short history for AMR/ACI).
- Real-time ONI still uses the latest CPC file (includes revisions to recent seasons).
- 2020–23 “triple-dip” La Niña is split by our strict 5-in-a-row rule when ONI briefly > −0.5 in mid-2021.
- No trading authority is granted by this repository.
