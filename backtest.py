"""La Niña × energy watch backtest. Implements PREREGISTRATION.md. No trading."""
import os, json, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lib.oni import load_oni, episodes, episode_bounds

EQ = [t for t in "XLE XOP OIH XES IEO FCG".split()]
COAL = [t for t in "BTU AMR ACI".split()]
STATE = "APA AR CHRD COP CVX DVN EOG EXE FANG HAL MTDR MUR OVV OXY PR PSX RRC SLB VLO VNOM XOM".split()
P = pd.read_parquet("data/prices.parquet").sort_index()
P = P[P.index >= "2000-01-01"]
R = P.pct_change(fill_method=None).mask(lambda x: x.abs() > 0.5)  # drop glitches
# monthly
Pm = P.resample("ME").last()
Rm = Pm.pct_change(fill_method=None).mask(lambda x: x.abs() > 1.5)
# T-bill monthly rf
tb = pd.read_csv("data/dtb3.csv", parse_dates=["observation_date"]).set_index("observation_date")["DTB3"]
tb = pd.to_numeric(tb, errors="coerce") / 100.0
rf_m = (1 + tb.resample("ME").last() / 12).pow(0) * tb.resample("ME").last() / 12  # approx monthly yield
rf_m = tb.resample("ME").last() / 12  # simple

oni, oni_raw = load_oni("data/oni.txt", lag=1)
oni = oni.reindex(Rm.index).ffill()
LN = episodes(oni, thr=-0.5, streak=5, sign=-1)
EN = episodes(oni, thr=0.5, streak=5, sign=+1)
print("La Niña months", int(LN.sum()), "El Niño months", int(EN.sum()))
print("LN episodes", episode_bounds(LN))
print("EN episodes", episode_bounds(EN))

def basket_ret(tickers, rets):
    cols = [t for t in tickers if t in rets.columns]
    return rets[cols].mean(axis=1)

def apply_costs(w, cost_bp=10):
    """w: weight series 0/1 (or portfolio weight). turnover * cost."""
    to = w.diff().abs().fillna(w.abs())
    return to * (cost_bp / 1e4)

def ew_basket_monthly(tickers):
    cols = [t for t in tickers if t in Rm.columns]
    # equal weight among available that month
    X = Rm[cols]
    n = X.notna().sum(1).replace(0, np.nan)
    r = X.mean(1)
    # turnover: membership changes
    mem = X.notna().astype(float)
    w = mem.div(n, axis=0)
    to = w.diff().abs().sum(1).fillna(0)
    cost = to * 0.001  # 10bp one-way
    return r - cost, n

eq_r, eq_n = ew_basket_monthly(EQ + COAL)
st_r, st_n = ew_basket_monthly(STATE)
spy = Rm["SPY"]
xle = Rm["XLE"]
clm = Rm["CL"]

def strat(signal, asset, alt=None, name=""):
    """Long asset when signal, else alt (0 if None). Net already in asset."""
    sig = signal.reindex(asset.index).fillna(False).astype(bool)
    if alt is None:
        r = asset.where(sig, 0.0)
    else:
        r = asset.where(sig, alt.reindex(asset.index))
    # entry/exit already month-end: one extra 10bp when signal flips
    flip = sig.astype(int).diff().abs().fillna(0)
    r = r - flip * 0.001
    return r.rename(name)

def stats(r, rf=None, label=""):
    r = r.dropna()
    if len(r) < 6:
        return dict(label=label, n=len(r))
    ann = 12
    cagr = (1 + r).prod() ** (ann / len(r)) - 1
    vol = r.std(ddof=1) * np.sqrt(ann)
    if rf is not None:
        ex = r - rf.reindex(r.index).fillna(0)
    else:
        ex = r
    sharpe = ex.mean() / ex.std(ddof=1) * np.sqrt(ann) if ex.std(ddof=1) > 0 else np.nan
    wealth = (1 + r).cumprod()
    dd = wealth / wealth.cummax() - 1
    maxdd = dd.min()
    # NW t on mean
    try:
        res = sm.OLS(r.values, np.ones((len(r), 1))).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
        t = float(res.tvalues[0]); p = float(res.pvalues[0])
    except Exception:
        t = p = np.nan
    return dict(label=label, n=len(r), cagr=cagr, vol=vol, sharpe=sharpe, maxdd=maxdd,
                mean_m=r.mean(), t_nw=t, p_nw=p)

def split_stats(r, split, rf=None, label=""):
    r = r.dropna()
    sp = pd.Timestamp(split)
    out = {}
    out["full"] = stats(r, rf, label)
    out["IS"] = stats(r[r.index < sp], rf, label + " IS")
    out["OOS"] = stats(r[r.index >= sp], rf, label + " OOS")
    return out

# ---- Unhedged
U1 = strat(LN, eq_r, None, "U1")
U2 = strat(LN, st_r, None, "U2")
U3 = strat(LN, eq_r, spy, "U3")
C1 = strat(EN, eq_r, None, "C1_EN")
# buy & hold benches on same sample
bh_spy = spy.copy()
bh_xle = xle.copy()

# ---- Oil hedge H1/H2: rolling 36m β of daily basket vs CL, apply in LN months
Rd = R.copy()
def daily_basket(tickers):
    cols = [t for t in tickers if t in Rd.columns]
    return Rd[cols].mean(1)

eq_d = daily_basket(EQ + COAL)
st_d = daily_basket(STATE)
cl_d = Rd["CL"]

def rolling_beta(y, x, window=36 * 21):
    df = pd.concat([y, x], axis=1).dropna(); df.columns = ["y", "x"]
    # monthly β snapshots at month-end using prior window days
    betas = {}
    for me in Rm.index:
        sub = df.loc[:me].tail(window)
        if len(sub) < 126:
            continue
        b = np.polyfit(sub.x.values, sub.y.values, 1)[0]
        betas[me] = b
    return pd.Series(betas)

b_eq = rolling_beta(eq_d, cl_d)
b_st = rolling_beta(st_d, cl_d)
print("beta EQ vs CL median", b_eq.median(), "STATE", b_st.median())

def hedged_monthly(asset_m, beta, cl_m, signal, roll_bp=10, beta_cost_bp=5):
    sig = signal.reindex(asset_m.index).fillna(False)
    b = beta.reindex(asset_m.index).ffill()
    # return = asset - b*CL when in signal; flat otherwise
    raw = (asset_m - b * cl_m).where(sig, 0.0)
    # costs: roll while on + beta change cost on notional |b|
    on = sig.astype(int)
    roll = on * (roll_bp / 1e4)
    db = b.diff().abs().fillna(0) * on
    bcost = db * (beta_cost_bp / 1e4)
    flip = on.diff().abs().fillna(0) * 0.001
    return (raw - roll - bcost - flip).rename("hedged")

H1 = hedged_monthly(eq_r, b_eq, clm, LN)
H2 = hedged_monthly(st_r, b_st, clm, LN)

# H3 residualized: rolling monthly β
def rolling_m_beta(y, x, win=36):
    df = pd.concat([y, x], axis=1).dropna(); df.columns = ["y", "x"]
    out = {}
    for i, me in enumerate(df.index):
        if i < win:
            continue
        sub = df.iloc[i - win:i]
        out[me] = np.polyfit(sub.x.values, sub.y.values, 1)[0]
    return pd.Series(out)

bm = rolling_m_beta(eq_r, clm)
resid = (eq_r - bm.reindex(eq_r.index).ffill() * clm).where(LN.reindex(eq_r.index).fillna(False), 0.0)
H3 = resid - LN.reindex(eq_r.index).fillna(False).astype(int).diff().abs().fillna(0) * 0.001

# ---- Align sample from first EQ+CL available
start = max(eq_r.dropna().index.min(), clm.dropna().index.min(), pd.Timestamp("2006-07-31"))  # OIH/XOP era-ish; actually use 2000 for STATE
# Primary report window: 2000-08 (CL) to latest; ETF basket from when >=3 names
eq_ok = eq_n >= 3
sample = eq_ok & clm.notna() & spy.notna()

rows = []
for name, series in [("U1_EQ_cash", U1), ("U2_STATE_cash", U2), ("U3_EQ_SPY", U3),
                     ("H1_EQ_oilhedged", H1), ("H2_STATE_oilhedged", H2), ("H3_EQ_residual", H3),
                     ("C1_ElNino_EQ_cash", C1), ("BH_SPY", bh_spy), ("BH_XLE", bh_xle)]:
    s = series.reindex(Rm.index)[sample].dropna()
    for split in ["2016-01-01", "2019-01-01"]:
        st = split_stats(s, split, rf_m, name)
        for k, v in st.items():
            v = dict(v); v["split"] = split; v["period"] = k; v["strategy"] = name
            rows.append(v)

# Active-month only stats (La Niña months only)
for name, series in [("U1_active_months", eq_r), ("H1_active_months", H1.where(LN, np.nan)),
                     ("C1_EN_active", eq_r.where(EN, np.nan))]:
    if name.startswith("U1"):
        s = series.where(LN).dropna()
    elif name.startswith("H1"):
        s = H1.where(LN).dropna()
    else:
        s = eq_r.where(EN).dropna()
    v = stats(s, rf_m, name); v["split"] = "active"; v["period"] = "LN_or_EN"; v["strategy"] = name
    rows.append(v)

Rtab = pd.DataFrame(rows)
Rtab.to_csv("results/stats.csv", index=False)

# Alpha vs SPY / XLE (monthly regression of strategy on bench), full & OOS 2016
alphas = []
for name, series in [("U1", U1), ("U2", U2), ("H1", H1), ("H2", H2)]:
    s = series.reindex(Rm.index)[sample].dropna()
    for bench_name, bench in [("SPY", spy), ("XLE", xle)]:
        for period, mask in [("full", s.index >= s.index.min()),
                             ("OOS2016", s.index >= "2016-01-01"),
                             ("OOS2019", s.index >= "2019-01-01")]:
            y = s.loc[mask]; x = bench.reindex(y.index)
            d = pd.concat([y, x], axis=1).dropna(); d.columns = ["y", "x"]
            if len(d) < 24: continue
            res = sm.OLS(d.y, sm.add_constant(d.x)).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
            alphas.append(dict(strategy=name, bench=bench_name, period=period, n=len(d),
                               alpha_m=res.params["const"], alpha_ann=res.params["const"] * 12,
                               t=res.tvalues["const"], p=res.pvalues["const"], beta=res.params["x"]))
A = pd.DataFrame(alphas); A.to_csv("results/alphas.csv", index=False)

# Leave-out 2021-22
shock = (Rm.index.year.isin([2021, 2022]))
lo = []
for name, series in [("U1", U1), ("H1", H1)]:
    s = series.reindex(Rm.index)[sample & ~shock].dropna()
    lo.append(stats(s, rf_m, name + "_no_2021_22") | {"strategy": name})
    s2 = series.reindex(Rm.index)[sample].dropna()
    lo.append(stats(s2, rf_m, name + "_full") | {"strategy": name})
pd.DataFrame(lo).to_csv("results/leaveout_2021_22.csv", index=False)

# Threshold / streak robustness (exploratory)
rob = []
for thr in [-0.4, -0.5, -0.6]:
    for streak in [3, 5, 6]:
        for lag in [0, 1, 2]:
            o, _ = load_oni("data/oni.txt", lag=lag)
            o = o.reindex(Rm.index).ffill()
            sig = episodes(o, thr=thr, streak=streak, sign=-1)
            r = strat(sig, eq_r, None)
            r = r.reindex(Rm.index)[sample].dropna()
            st = stats(r, rf_m)
            rob.append(dict(thr=thr, streak=streak, lag=lag, **{k: st[k] for k in ["n", "cagr", "sharpe", "maxdd", "t_nw"]}))
pd.DataFrame(rob).to_csv("results/robustness_grid.csv", index=False)

# Neutral-period EQ return (control)
neutral = (~LN) & (~EN)
v = stats(eq_r.where(neutral).dropna(), rf_m, "EQ_neutral_months")
pd.DataFrame([v]).to_csv("results/neutral.csv", index=False)

# ---- Charts
fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=False)
# equity curves (growth of $1)
def wealth(r):
    r = r.reindex(Rm.index)[sample].fillna(0)
    return (1 + r).cumprod()

for lab, s in [("U1 EQ/cash", U1), ("U2 STATE/cash", U2), ("H1 oil-hedged", H1), ("SPY BH", bh_spy), ("XLE BH", bh_xle)]:
    wealth(s).plot(ax=ax[0], label=lab)
ax[0].legend(loc="upper left", fontsize=8); ax[0].set_yscale("log"); ax[0].set_title("Growth of $1 (log) — La Niña energy watch")
ax[0].axvspan(pd.Timestamp("2021-01-01"), pd.Timestamp("2022-12-31"), color="orange", alpha=0.15, label="2021-22")
# ONI + LN bands
oni.plot(ax=ax[1], color="k", lw=0.8)
ax[1].axhline(-0.5, color="b", ls="--", lw=0.7); ax[1].axhline(0.5, color="r", ls="--", lw=0.7)
for s, e in episode_bounds(LN):
    ax[1].axvspan(s, e, color="blue", alpha=0.2)
ax[1].set_title("ONI (real-time LAG=1) with La Niña episodes shaded")
fig.tight_layout(); fig.savefig("charts/equity_curves.png", dpi=120)

fig2, ax = plt.subplots(figsize=(11, 4))
for lab, s in [("H1 oil-hedged", H1), ("U1 unhedged", U1)]:
    wealth(s).plot(ax=ax, label=lab)
ax.legend(); ax.set_title("Unhedged vs oil-hedged (growth of $1)"); ax.set_yscale("log")
fig2.tight_layout(); fig2.savefig("charts/hedged_vs_unhedged.png", dpi=120)

# Save signals for watch.py
sig = pd.DataFrame({"oni": oni, "la_nina": LN.astype(int), "el_nino": EN.astype(int),
                    "eq_ret": eq_r, "u1": U1, "h1": H1})
sig.to_csv("results/monthly_signal.csv")
json.dump({"ln_episodes": [(str(a.date()), str(b.date())) for a, b in episode_bounds(LN)],
           "en_episodes": [(str(a.date()), str(b.date())) for a, b in episode_bounds(EN)],
           "last_oni": float(oni.dropna().iloc[-1]),
           "last_month": str(oni.dropna().index[-1].date()),
           "in_la_nina": bool(LN.dropna().iloc[-1]),
           "in_el_nino": bool(EN.dropna().iloc[-1])},
          open("results/status.json", "w"), indent=2)

# Pretty print primary table
prim = Rtab[(Rtab.period == "full") & (Rtab.split == "2016-01-01")][
    ["strategy", "n", "cagr", "vol", "sharpe", "maxdd", "t_nw", "p_nw"]].copy()
oos = Rtab[(Rtab.period == "OOS") & (Rtab.split == "2016-01-01")][
    ["strategy", "cagr", "sharpe", "maxdd", "t_nw"]].rename(
    columns=lambda c: c if c == "strategy" else c + "_oos2016")
m = prim.merge(oos, on="strategy", how="left")
print(m.to_string(index=False))
print("\nAlphas OOS2016:")
print(A[A.period == "OOS2016"].to_string(index=False))
print("\nLeave-out:")
print(pd.DataFrame(lo)[["label", "cagr", "sharpe", "maxdd", "t_nw"]].to_string(index=False))
print("\nStatus:", json.load(open("results/status.json")))
m.to_csv("results/primary_table.csv", index=False)
