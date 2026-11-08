"""東京ブレイク: 利確を「東京の値幅の何倍か」にした場合の検証（ドル円15分足）
  python daytrade_tp_width.py DATA_DIR"""
import os
import sys

import pandas as pd

from daytrade import add_htf_slope, load_csv, simulate, summarize

df = add_htf_slope(load_csv(os.path.join(sys.argv[1], "USDJPYm15.csv")) / 1000)
rows = []
cases = [("利確なし（今のルール）", 0, "edge")] + \
        [(f"値幅×{k:g}（端から）", k, "edge") for k in (1, 1.5, 2, 3)] + \
        [(f"値幅×{k:g}（エントリーから）", k, "entry") for k in (2,)]
for name, k, base in cases:
    for sp in (0.3, 1.0):
        t = simulate(df, "tokyo_break", "none", "far", 0, sp, tp_width=k, tp_from=base)
        s = summarize(t)
        tr, te = t[t.date < "2018-01-01"], t[t.date >= "2018-01-01"]
        rows.append(dict(rule=name, spread=sp, trades=s["trades"], win=s["win"], pf=s["pf"], pips=s["pips"],
                         cagr=s["cagr"], maxdd=s["maxdd"], tp_rate=round((t.exit_reason == "利確").mean() * 100, 1),
                         sl_rate=round((t.exit_reason == "損切り").mean() * 100, 1),
                         pf_前半=summarize(tr)["pf"], pf_後半=summarize(te)["pf"],
                         plus_years=int((t.groupby(t.date.dt.year).r.sum() > 0).sum()),
                         final_1pct=round(((1 + t.r / 100).cumprod()).iloc[-1] * 100)))
res = pd.DataFrame(rows)
res.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "daytrade_tp_width_result.csv"),
           index=False, encoding="utf-8-sig")
pd.set_option("display.width", 250)
print(res.to_string(index=False))
t = simulate(df, "tokyo_break", "none", "far", 0, 0.3, tp_width=2)
print("\n値幅×2（端から）年別"); print(t.groupby(t.date.dt.year).apply(lambda g: pd.Series(summarize(g)))[["trades", "win", "pf", "pips", "cagr"]].to_string())
print("値幅（pips）中央値", round(((t.range_hi - t.range_lo) / 0.01).median(), 1))
s = (t.r <= 0).astype(int); mx = c = 0
for v in s:
    c = c + 1 if v else 0; mx = max(mx, c)
print("最大連敗", mx, " 決済理由", t.exit_reason.value_counts().to_dict())
