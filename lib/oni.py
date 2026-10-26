"""Real-time ONI and CPC-style episode detection (LAG=1 after season end)."""
import pandas as pd
import numpy as np

CEN = {"DJF":1,"JFM":2,"FMA":3,"MAM":4,"AMJ":5,"MJJ":6,"JJA":7,"JAS":8,"ASO":9,"SON":10,"OND":11,"NDJ":12}

def load_oni(path="data/oni.txt", lag=1):
    o = pd.read_csv(path, sep=r"\s+")
    o["cm"] = [pd.Timestamp(int(y), CEN[s], 1) for s, y in zip(o.SEAS, o.YR)]
    # season ends cm+1; usable at end of month cm+1+lag
    o["known"] = [(c + pd.DateOffset(months=1 + lag)) + pd.offsets.MonthEnd(0) for c in o.cm]
    oni = o.set_index("known").ANOM.sort_index()
    oni = oni[~oni.index.duplicated(keep="last")].asfreq("ME").ffill()
    return oni, o

def episodes(oni, thr=-0.5, streak=5, sign=-1):
    """Boolean monthly series: True when a CPC-style episode is active under real-time knowledge.
    sign=-1 La Niña (ONI<=thr), sign=+1 El Niño (ONI>=-thr if thr negative).
    Entry at first month where last `streak` known seasons all satisfy; exit when streak breaks.
    """
    if sign < 0:
        hit = (oni <= thr).astype(int)
    else:
        hit = (oni >= abs(thr)).astype(int)
    # consecutive count ending this month
    run = hit.groupby((hit != hit.shift()).cumsum()).cumsum() * hit
    active = (run >= streak).astype(bool)
    # Once active, stay until hit breaks (standard CPC: episode continues while threshold met,
    # but our prereg says exit when 5-season streak is broken. Equivalent: active while run>=streak
    # OR we already entered and still hit. Prereg: "exit when the 5-season streak is broken".
    # So active iff the trailing streak length >= streak at that month.
    return active

def episode_bounds(active):
    """List of (entry_month_end, exit_month_end) inclusive of last active month."""
    a = active.fillna(False).astype(int)
    edges = a.diff().fillna(a.iloc[0])
    starts = list(a.index[edges == 1])
    ends = list(a.index[edges == -1])
    # if currently active, last end is last True
    if a.iloc[-1] == 1:
        ends.append(a.index[a.astype(bool)].max())
    # pair: exit is month before the False, i.e. ends already are first False? 
    # edges==-1 is first False after True, so last active is prior month.
    out = []
    for s in starts:
        later = [e for e in ends if e > s]
        if not later:
            e = a.index[a.astype(bool)].max()
        else:
            e = later[0]
            # if e is first inactive, last active is previous month-end
            if not bool(a.loc[e]):
                e = a.index[a.index.get_loc(e) - 1]
        out.append((s, e))
    return out
