#!/usr/bin/env python3
"""Print today's La Niña × energy watch signal from free data. NO trading."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from lib.oni import load_oni, episodes, episode_bounds

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

def refresh_oni(path=ROOT / "data" / "oni.txt"):
    try:
        r = requests.get(ONI_URL, timeout=30)
        r.raise_for_status()
        path.write_text(r.text)
        return True, "refreshed from NOAA CPC"
    except Exception as e:
        return False, f"using cached oni.txt ({e})"

def main():
    ap = argparse.ArgumentParser(description="La Niña energy watch status (research only)")
    ap.add_argument("--no-refresh", action="store_true")
    args = ap.parse_args()
    if not args.no_refresh:
        ok, msg = refresh_oni()
    else:
        ok, msg = False, "cached (--no-refresh)"
    oni, raw = load_oni(ROOT / "data" / "oni.txt", lag=1)
    LN = episodes(oni, thr=-0.5, streak=5, sign=-1)
    EN = episodes(oni, thr=0.5, streak=5, sign=+1)
    last_t, last_v = oni.dropna().index[-1], float(oni.dropna().iloc[-1])
    in_ln, in_en = bool(LN.dropna().iloc[-1]), bool(EN.dropna().iloc[-1])
    # streak counters
    def streak(cond):
        h = cond.astype(int)
        run = h.groupby((h != h.shift()).cumsum()).cumsum() * h
        return int(run.iloc[-1])
    ln_streak = streak(oni <= -0.5)
    en_streak = streak(oni >= 0.5)
    if in_ln:
        hold = "LONG energy basket (EQ: XLE/XOP/OIH/XES/IEO/FCG + BTU/AMR/ACI; or STATE energy names)"
        hedged = "LONG basket / SHORT β·CL (β≈0.5 from prior 36m daily)"
    else:
        hold = "CASH (flat) — primary rule U1/H1"
        hedged = "FLAT (no oil hedge)"
    print("=" * 64)
    print("La Niña × energy WATCH (research only — NO orders)")
    print("=" * 64)
    print(f"ONI file: {msg}")
    print(f"As-known ONI (LAG=1 after season end): {last_v:+.2f} as of {last_t.date()}")
    print(f"La Niña episode active (≤−0.5 for 5 seasons)? {in_ln}  (current streak={ln_streak})")
    print(f"El Niño episode active (≥+0.5 for 5 seasons)? {in_en}  (current streak={en_streak})")
    print(f"Rules would hold: {hold}")
    print(f"Oil-hedged sleeve: {hedged}")
    if en_streak >= 3 and not in_en:
        print(f"Note: ONI≥0.5 streak is {en_streak}/5 — El Niño declaration approaching, not La Niña.")
    if ln_streak >= 3 and not in_ln:
        print(f"Note: ONI≤−0.5 streak is {ln_streak}/5 — La Niña declaration approaching.")
    print("Last La Niña episodes (real-time rule):")
    for a, b in episode_bounds(LN)[-4:]:
        print(f"  {a.date()} → {b.date()}")
    print("See PREREGISTRATION.md and README.md. Decision from backtest: NOT EVEN WATCH.")
    print("=" * 64)
    # write status sidecar
    status = {
        "as_of": str(last_t.date()),
        "oni": last_v,
        "in_la_nina": in_ln,
        "in_el_nino": in_en,
        "ln_streak": ln_streak,
        "en_streak": en_streak,
        "hold": hold,
        "recommendation": "not_even_watch",
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "status.json").write_text(json.dumps(status, indent=2))
    (ROOT / "current_status.md").write_text(
        f"""# Current status (auto from `watch.py`)

- **As-known ONI (LAG=1):** {last_v:+.2f} as of {last_t.date()} (America/Chicago box clock; NOAA CPC).
- **In La Niña episode?** **{in_ln}** (streak of ONI≤−0.5 months = {ln_streak}; need 5).
- **In El Niño episode?** **{in_en}** (streak of ONI≥+0.5 months = {en_streak}; need 5).
- **What the rules would hold:** {hold}
- **Oil-hedged sleeve:** {hedged}
- **Watch recommendation (from backtest vs prereg success criteria):** **not even watch**.
  Unhedged OOS Sharpe missed the 0.30 bar; oil-hedged alpha collapses when 2021–22 is removed;
  the idea was selected after seeing it among 310 prior tests (EN2 q≈0.15, did not survive BH).

Last La Niña episodes under the real-time rule:
"""
        + "\n".join(f"- {a.date()} → {b.date()}" for a, b in episode_bounds(LN)[-6:])
        + "\n"
    )

if __name__ == "__main__":
    main()
