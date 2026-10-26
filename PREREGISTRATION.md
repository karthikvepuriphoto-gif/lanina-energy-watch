# Pre-registration — La Niña × energy watch (NO trading)

Committed **before** any return test in this repository. Timestamp of this commit is the proof.
This is a **watch / research** backtest only. No paper trading. No live trading. No orders.

## Mechanism (literature + Phase 1)
1. La Niña (ONI ≤ −0.5) is associated with a cooler equatorial Pacific and a suite of tropical/extratropical teleconnections that historically raise Northern Hemisphere winter heating demand and disrupt Atlantic hurricane tracks (NOAA CPC ENSO composites).
2. In `alt-signal-research` Phase 1 (branch `enso-weather`), PPI crude and the FF Coal portfolio had higher next-month returns in La Niña months than in other months (both survived BH across 283 tests; crude also confirmed OOS). Phase 2 EN2 (branch `state-signals`) found TX/OK/ND/LA/CO HQ energy firms +4.1%/month vs SPY in La Niña months (t 2.4, q 0.15 vs 310 tests; OOS +6.9%, t 3.0).
3. Economic channel under test: La Niña → higher expected energy cash flows / risk premium → positive excess return of energy equity baskets, **not solely via concurrent oil-price moves**. The oil-hedged version is therefore the primary scientific test.

## Prediction (direction)
During declared La Niña episodes (definition below), an equal-weight energy equity basket outperforms (a) cash and (b) SPY on a calendar-time basis. The **oil-hedged** residual (long basket, short β·CL or residualized vs CL returns) is also positive. Sign predicted: **positive** for both unhedged and hedged.

## Universe (fixed at preregistration)
- **Primary basket EQ** (equal-weight, monthly rebalance): liquid energy ETFs + sector proxies
  `XLE, XOP, OIH, XES, IEO, FCG` and, when price history exists, coal / thermal proxies `KOL` (or successor), `BTU`, `ARCH`/`AMR`.
- **Secondary basket STATE**: Phase 2 energy firms HQ in TX/OK/ND/LA/CO with SIC in {1311, 1381, 1389, 2911}:
  `APA, AR, CHRD, COP, CVX, DVN, EOG, EXE, FANG, HAL, MTDR, MUR, OVV, OXY, PR, PSX, RRC, SLB, VLO, VNOM, XOM`
  (equal-weight among names with valid prices that month; survivorship caveat noted in README).
- **Oil hedge instrument**: front continuous crude, proxied by `CL=F` (Yahoo continuous) and cross-checked with `USO` when CL gaps. Primary hedge uses daily CL returns.
- **Benchmarks**: `SPY`, buy-and-hold `XLE`.
- History target: 2000–present where available (ETF inception limits XOP/OIH/etc.).

## When ONI / La Niña is known (no lookahead)
- Source: NOAA CPC Oceanic Niño Index, 3-month seasonal means (`data/oni.txt`, same file as Phase 1).
- Season labeled by its center month. Season ending month = center + 1. **Usable at the end of the month after the season-ending month** (LAG = 1 calendar month after season end). Example: the JJA season (center July, ends August) is first usable at end of September. This matches Phase 1 `enso_backtest.py` LAG=1.
- **La Niña episode (CPC-style):** ONI ≤ −0.5 for **5 consecutive overlapping seasons**, as known in real time. **El Niño episode:** ONI ≥ +0.5 for 5 consecutive seasons. Neutral = neither.
- **Entry:** at the month-end close of the first month in which the 5-season condition is met under the LAG=1 knowledge rule.
- **Exit:** at the month-end close of the first month in which the 5-season streak is broken (ONI rises above −0.5 for La Niña, or the usable series no longer shows 5 consecutive ≤ −0.5).
- Between entry and exit the strategy is fully invested in the basket; otherwise it holds **cash (0% return)** in the primary specification, with an alternate that holds SPY.

## Variants (all preregistered)
| id | description |
|---|---|
| U1 | Long EQ basket during La Niña; cash otherwise. Monthly rebalance. |
| U2 | Long STATE basket during La Niña; cash otherwise. |
| U3 | Long EQ during La Niña; SPY otherwise. |
| H1 | Oil-hedged EQ: each La Niña month, long EQ and short β̂·CL, where β̂ is estimated from the prior 36 months of daily EQ−cash vs CL returns (expanding to 36 then rolling). Outside La Niña: flat. |
| H2 | Same as H1 on STATE basket. |
| H3 | Residualized monthly: EQ excess return on CL excess return (36m rolling β); take residual only in La Niña months. |
| C1 | Control: same U1 rules but during **El Niño** episodes (predicted: ≤0 or weaker than La Niña). |
| C2 | Control: random 5-season windows matched in length (null distribution; report percentile). |

## Costs and frictions
- Monthly rebalance of equity basket: **10 bp one-way** on the turnover of weights (equal-weight turnover ≈ 0 when membership stable; ETF-only basket ~0 beyond inception adds).
- Oil hedge: **5 bp one-way** on CL notional when β changes, plus **roll cost approximation of 10 bp per month** while the hedge is on (proxy for contango/backwardation friction; conservative).
- No short-rebate modeling beyond the CL roll proxy.
- Primary stats reported **net of these costs**.

## Evaluation plan
- Sample: first available prices through latest complete month.
- **IS / OOS split:** IS = through 2015-12; OOS = 2016-01 onward (publication-year style relative to classical ENSO–commodity papers; also matches Phase 1 commodity split). Secondary split: IS through 2018-12 / OOS 2019+.
- Metrics: CAGR, annualized volatility, Sharpe (rf≈0 for simplicity, also report vs 3M T-bill if FRED available), max drawdown, hit rate of La Niña months, Newey–West t-stat of monthly active return, calendar-time alpha vs SPY and vs XLE.
- Oil-hedged: report mean monthly residual, NW t, Sharpe of residual stream.
- Robustness (labelled exploratory if beyond the table above): leave-out 2021–2022 energy-shock months; leave-out 2008; threshold −0.4 / −0.6; streak length 3 / 6 seasons; LAG=0 and LAG=2.
- **Multiple testing:** this strategy was selected after seeing Phase 1/2 results among **310 prior hypotheses**. BH across those 310 already gave EN2 q≈0.15 (did not survive 5%). Any claim here is **post-selection**. Report that fact prominently; do not invent a new BH that pretends EN2 was not previously tested.

## Success criteria (decision rule for the watch)
- **Watch:** OOS Sharpe of U1 > 0.3 **and** H1 mean residual t > 1.5 OOS **and** C1 (El Niño) not stronger than U1.
- **Not even watch:** fails any of the three, or depends entirely on 2021–22.
- Never: trade, paper-trade, or size a book.
