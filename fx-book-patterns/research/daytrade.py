"""
デイトレ（1日1回・日をまたがない）のトレンド手法を、ドル円15分足で検証する
サーバー時刻は GMT+2/+3（NYクローズ=0:00）。東京=おおむね3〜9時、ロンドン=10時〜、NY=15時〜

手法（条件は先に決めて固定）
  tokyo_break : 東京時間（3:00〜9:59）の高値・安値を、ロンドン以降（10:00〜17:59）に15分足の終値で抜けたら、抜けた方向へ
  london_orb  : ロンドン最初の1時間（10:00〜10:59）の高値・安値を、11:00〜17:59に終値で抜けたら、抜けた方向へ
フィルター
  none   : 制限なし
  trend  : 4時間足MA100の傾きがプラスなら買いのみ、マイナスなら売りのみ（確定足の値）
決済
  損切り: レンジの反対側（sl=far）または中央（sl=mid）
  利確  : 損切り幅×RR（rr=0 なら利確なし）
  時間  : 23:00（NY時間の終わり）で必ず決済
  同じ足で損切りと利確の両方に届いたら、損切りとみなす（不利な側）

  python daytrade.py DATA_DIR
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ea"))
from extract_patterns import load_csv  # noqa: E402
from backtest import add_htf_slope  # noqa: E402

PIP = 0.01
SETUPS = {"tokyo_break": ((3, 0), (9, 45), (10, 0), (17, 45)),
          "london_orb": ((10, 0), (10, 45), (11, 0), (17, 45))}
EOD = (23, 0)


def hm(ts):
    return ts.hour * 60 + ts.minute


def simulate(df, setup, filt, sl_mode, rr, spread, pip=PIP):
    rs, re_, es, ee = [h * 60 + m for h, m in SETUPS[setup]]
    eod = EOD[0] * 60 + EOD[1]
    trades = []
    for day, g in df.groupby(df.index.date):
        mins = np.array([hm(t) for t in g.index])
        rng = g[(mins >= rs) & (mins <= re_)]
        if len(rng) < (re_ - rs) // 15:                 # 欠けている日は飛ばす
            continue
        hi, lo = rng.High.max(), rng.Low.min()
        width = hi - lo
        if width <= 0:
            continue
        o, h, l, c = g.Open.values, g.High.values, g.Low.values, g.Close.values
        htf = g.HTF.values
        idx = np.where((mins >= es) & (mins <= ee))[0]
        for i in idx:
            side = 1 if c[i] > hi else (-1 if c[i] < lo else 0)
            if not side:
                continue
            if filt == "trend" and np.sign(htf[i]) != side:
                break                                   # その日の最初のブレイクが逆向きなら見送り
            j = i + 1
            if j >= len(g) or mins[j] >= eod:
                break
            entry = o[j] + side * spread * pip / 2
            stop = (lo if side > 0 else hi) if sl_mode == "far" else (hi + lo) / 2
            risk = (entry - stop) * side
            if risk <= spread * pip:
                break
            tp = entry + side * risk * rr if rr else None
            exit_p, k, reason = None, j, "時間決済"
            for k in range(j, len(g)):
                if mins[k] >= eod:
                    exit_p = o[k]
                    break
                if (l[k] <= stop) if side > 0 else (h[k] >= stop):
                    exit_p, reason = stop, "損切り"
                    break
                if tp is not None and ((h[k] >= tp) if side > 0 else (l[k] <= tp)):
                    exit_p, reason = tp, "利確"
                    break
            if exit_p is None:
                exit_p = c[-1]
            exit_p -= side * spread * pip / 2
            pips = (exit_p - entry) * side / pip
            trades.append(dict(date=pd.Timestamp(day), side=side, risk_pips=risk / pip, pips=pips,
                               r=(exit_p - entry) * side / risk,
                               signal_time=g.index[i], entry_time=g.index[j],
                               exit_time=g.index[min(k, len(g) - 1)],
                               range_hi=hi, range_lo=lo, entry=entry, stop=stop, exit=exit_p,
                               exit_reason=reason))
            break
    return pd.DataFrame(trades)


def summarize(t, risk_pct=1.0):
    if t.empty:
        return dict(trades=0)
    eq = (1 + t.r * risk_pct / 100).cumprod()
    years = max((t.date.iloc[-1] - t.date.iloc[0]).days / 365.25, 0.5)
    w, l = t.r[t.r > 0].sum(), -t.r[t.r <= 0].sum()
    return dict(trades=len(t), win=round((t.r > 0).mean() * 100, 1), pf=round(w / l, 2) if l else np.inf,
                pips=round(t.pips.sum()), avg_r=round(t.r.mean(), 3),
                cagr=round((eq.iloc[-1] ** (1 / years) - 1) * 100, 1),
                maxdd=round(((eq / eq.cummax()) - 1).min() * 100, 1),
                med_sl=round(t.risk_pips.median(), 1))


def main():
    df = add_htf_slope(load_csv(os.path.join(sys.argv[1], "USDJPYm15.csv")) / 1000)
    rows = []
    grid = itertools.product(SETUPS, ["none", "trend"], ["far", "mid"], [0, 1.0, 1.5, 2.0])
    for setup, filt, sl_mode, rr in grid:
        t = simulate(df, setup, filt, sl_mode, rr, spread=0.3)
        tr, te = t[t.date < "2018-01-01"], t[t.date >= "2018-01-01"]
        row = dict(setup=setup, filter=filt, sl=sl_mode, rr=rr)
        row.update({"train_" + k: v for k, v in summarize(tr).items()})
        row.update({"test_" + k: v for k, v in summarize(te).items()})
        rows.append(row)
        print(row, flush=True)
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "daytrade_result.csv"),
               index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
