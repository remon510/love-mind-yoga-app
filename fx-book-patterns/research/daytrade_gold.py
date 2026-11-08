"""
東京ブレイクをゴールドドル（XAUUSD）と、合成したゴールド円（XAUUSD×USDJPY）で検証する
  python daytrade_gold.py DATA_DIR
ゴールド円は始値・終値は正確、高値・安値は両方の高値どうし・安値どうしの積で近似（値幅は広めに出る）
"""
import os
import sys

import pandas as pd

from daytrade import add_htf_slope, load_csv, simulate, summarize


def xaujpy(gold, uj):
    j = gold.join(uj, how="inner", lsuffix="_g", rsuffix="_j")
    return pd.DataFrame({"Open": j.Open_g * j.Open_j, "High": j.High_g * j.High_j,
                         "Low": j.Low_g * j.Low_j, "Close": j.Close_g * j.Close_j})


def report(name, df, pip, spreads):
    rows = []
    for sl in ("far", "mid"):
        for sp in spreads:
            t = simulate(df, "tokyo_break", "none", sl, 0, sp, pip=pip)
            tr, te = t[t.date < "2018-01-01"], t[t.date >= "2018-01-01"]
            s = summarize(t)
            rows.append(dict(data=name, sl=sl, spread=sp, trades=s["trades"], win=s["win"], pf=s["pf"],
                             cagr=s["cagr"], maxdd=s["maxdd"], med_sl=s["med_sl"],
                             pf_前半=summarize(tr)["pf"], pf_後半=summarize(te)["pf"]))
    return pd.DataFrame(rows), t


def main():
    d = sys.argv[1]
    gold = load_csv(os.path.join(d, "XAUUSDm15.csv")) / 100
    uj = load_csv(os.path.join(d, "USDJPYm15.csv")) / 1000
    out = []
    r, _ = report("XAUUSD", add_htf_slope(gold), 0.1, (0, 3.0, 5.0))           # 1pips=0.1ドル
    out.append(r)
    r, _ = report("XAUJPY(合成)", add_htf_slope(xaujpy(gold, uj)), 10, (0, 4.0, 6.0))  # 1pips=10円
    out.append(r)
    res = pd.concat(out)
    res.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "daytrade_gold_result.csv"),
               index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 220)
    print(res.to_string(index=False))
    for name, df, pip, sp in (("XAUUSD", add_htf_slope(gold), 0.1, 3.0),
                              ("XAUJPY(合成)", add_htf_slope(xaujpy(gold, uj)), 10, 4.0)):
        t = simulate(df, "tokyo_break", "none", "far", 0, sp, pip=pip)
        print("\n==", name, "年別（far・利確なし）")
        print(t.groupby(t.date.dt.year).apply(lambda g: pd.Series(summarize(g)))[["trades", "win", "pf", "cagr"]].to_string())
        print("買い/売り:", {k: summarize(g)["pf"] for k, g in t.groupby("side")})


if __name__ == "__main__":
    main()
