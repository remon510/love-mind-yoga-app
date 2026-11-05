"""
手法探索: 12銘柄ポートフォリオで、2013-2017年（学習）で設定を選び、2018-2022年（検証）で答え合わせ
  python search.py DATA_DIR [d1|h4]
"""
import itertools
import os
import sys
import warnings

import numpy as np
import pandas as pd
from backtesting import Backtest

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from extract_patterns import load_csv  # noqa: E402
import strategies as S  # noqa: E402

# 銘柄: (価格の倍率, 1pips, スプレッドpips)
SPEC = {"USDJPY": (1000, .01, .4), "EURUSD": (1e5, 1e-4, .4), "GBPUSD": (1e5, 1e-4, .8),
        "AUDUSD": (1e5, 1e-4, .6), "USDCAD": (1e5, 1e-4, 1.0), "USDCHF": (1e5, 1e-4, 1.0),
        "EURGBP": (1e5, 1e-4, 1.0), "EURCHF": (1e5, 1e-4, 1.2), "EURJPY": (1000, .01, .8),
        "GBPJPY": (1000, .01, 1.5), "AUDJPY": (1000, .01, 1.0), "XAUUSD": (100, .1, 2.5)}
TRAIN, TEST = ("2012", "2017"), ("2018", "2022")


def load(data_dir, tf="d1"):
    out = {}
    for sym, (sc, pip, sp) in SPEC.items():
        out[sym] = (load_csv(os.path.join(data_dir, f"{sym}{tf}.csv")) / sc, pip, sp)
    return out


def portfolio(data, strat, params, period, risk_pct=1.0):
    """各銘柄に同額の資金を割り当て、残高の推移を平均したもの（日次）"""
    curves, trades = [], []
    for sym, (df, pip, sp) in data.items():
        part = df[period[0]:period[1]]
        bt = Backtest(part, strat, cash=1_000_000, margin=1 / 25,
                      spread=sp * pip / part.Close.mean(), finalize_trades=True)
        st = bt.run(risk_pct=risk_pct, **params)
        eq = st._equity_curve.Equity / 1_000_000
        curves.append(eq.resample("1D").last().ffill().rename(sym))
        trades.append(st._trades.assign(sym=sym))
    eq = pd.concat(curves, axis=1).ffill().bfill().mean(axis=1)
    return eq, pd.concat(trades)


def stats(eq, trades):
    ret = eq.pct_change().dropna()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = eq.iloc[-1] ** (1 / years) - 1
    dd = (eq / eq.cummax() - 1).min()
    sharpe = ret.mean() / ret.std() * np.sqrt(365) if ret.std() else 0
    w, l = trades.PnL[trades.PnL > 0].sum(), -trades.PnL[trades.PnL <= 0].sum()
    return dict(cagr=round(cagr * 100, 1), maxdd=round(dd * 100, 1), sharpe=round(sharpe, 2),
                pf=round(w / l, 2) if l else np.inf, trades=len(trades),
                win=round((trades.PnL > 0).mean() * 100, 1))


GRIDS = {
    "Donchian": (S.Donchian, dict(entry_n=[20, 55, 100], exit_n=[10, 20, 50], stop_atr=[2.0, 3.0])),
    "MACross": (S.MACross, dict(fast=[20, 50], slow=[100, 200], trail_atr=[3.0, 5.0], stop_atr=[3.0])),
    "RSI2": (S.RSI2, dict(trend_ma=[100, 200], exit_ma=[5], lo=[5, 10], hi=[90, 95], stop_atr=[2.0, 3.0])),
}


def grid(params):
    keys = list(params)
    for vals in itertools.product(*params.values()):
        p = dict(zip(keys, vals))
        if "exit_n" in p and p["exit_n"] >= p["entry_n"]:
            continue
        if "fast" in p and p["fast"] >= p["slow"]:
            continue
        yield p


def main():
    tf = sys.argv[2] if len(sys.argv) > 2 else "d1"
    data = load(sys.argv[1], tf)
    rows = []
    for fam, (strat, params) in GRIDS.items():
        for p in grid(params):
            tr = stats(*portfolio(data, strat, p, TRAIN))
            rows.append(dict(family=fam, params=p, **{"train_" + k: v for k, v in tr.items()}))
            print(fam, p, tr, flush=True)
    res = pd.DataFrame(rows)
    # 各手法で学習期間のシャープレシオ最上位の設定だけを、検証期間で答え合わせ
    best = res.loc[res.groupby("family").train_sharpe.idxmax()]
    out = []
    for _, r in best.iterrows():
        strat = GRIDS[r.family][0]
        te = stats(*portfolio(data, strat, r.params, TEST))
        out.append(dict(family=r.family, params=r.params,
                        **{k: r[k] for k in res.columns if k.startswith("train_")},
                        **{"test_" + k: v for k, v in te.items()}))
    pd.set_option("display.width", 250)
    final = pd.DataFrame(out)
    print("\n=== 学習期間で選んだ設定 → 検証期間 ===")
    print(final.to_string(index=False))
    res.to_csv(os.path.join(os.path.dirname(__file__), f"search_train_grid_{tf}.csv"), index=False, encoding="utf-8-sig")
    final.to_csv(os.path.join(os.path.dirname(__file__), f"search_result_{tf}.csv"), index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
