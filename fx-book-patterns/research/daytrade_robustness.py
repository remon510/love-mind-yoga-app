"""東京ブレイク（tokyo_break, フィルターなし）の頑健性チェック: スプレッド感度・年別・売買別・他の通貨ペア
  cd research && python daytrade_robustness.py（データの場所は D を書き換え）"""
import sys, os
sys.path.insert(0, os.getcwd())
import pandas as pd
from daytrade import simulate, summarize, load_csv, add_htf_slope
D="/tmp/claude-0/-home-user-love-mind-yoga-app/dab08b7a-92b8-51a0-928e-11d9273c089a/scratchpad/dl"
pd.set_option("display.width",250)
uj=add_htf_slope(load_csv(D+"/USDJPYm15.csv")/1000)
print("== USDJPY tokyo_break none: スプレッド感度")
rows=[]
for sl in ("far","mid"):
    for sp in (0.3,0.5,0.8,1.0):
        t=simulate(uj,"tokyo_break","none",sl,0,sp)
        rows.append(dict(sl=sl,spread=sp,**summarize(t)))
print(pd.DataFrame(rows).to_string(index=False))
print("== 年別（far, 利確なし, spread 0.3）")
t=simulate(uj,"tokyo_break","none","far",0,0.3)
t["year"]=t.date.dt.year
print(t.groupby("year").apply(lambda g: pd.Series(summarize(g))).to_string())
print("== 買い/売り別")
print(t.groupby("side").apply(lambda g: pd.Series(summarize(g))).to_string())
print("== 他の通貨ペア（far, 利確なし）")
rows=[]
for sym,sc,pip,sp in (("EURJPY",1000,.01,.6),("GBPJPY",1000,.01,1.0),("AUDJPY",1000,.01,.7),("EURUSD",1e5,1e-4,.3),("GBPUSD",1e5,1e-4,.6)):
    df=add_htf_slope(load_csv(f"{D}/{sym}m15.csv")/sc)
    for sl in ("far","mid"):
        t=simulate(df,"tokyo_break","none",sl,0,sp,pip=pip)
        tr,te=t[t.date<"2018-01-01"],t[t.date>="2018-01-01"]
        rows.append(dict(sym=sym,sl=sl,**{"all_"+k:v for k,v in summarize(t).items() if k in("trades","win","pf","cagr","maxdd")},
                         train_pf=summarize(tr)["pf"],test_pf=summarize(te)["pf"]))
print(pd.DataFrame(rows).to_string(index=False))
