"""
「高値更新アウトサイド陰線／安値更新アウトサイド陽線」EA の Python バックテスト
MQL版（OutsideReversalEA.mq4 / .mq5）と同じ売買ルール

  エントリー: パターン確定足の次の足の始値
  損切り    : 売りならパターン足の高値 + バッファ（買いは安値 - バッファ）
  利確      : 損切り幅 × RR
  ポジション: 同時に1つまで

使い方:
  python backtest.py --csv USDJPYd1.csv --scale 1000
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from extract_patterns import load_csv  # noqa: E402


class OutsideReversal(Strategy):
    lookback = 20
    rr = 1.5
    buffer = 0.02          # 損切りバッファ（価格。ドル円なら0.02=2pips）
    risk_pct = 1.0         # 1トレードのリスク（口座残高に対する%）
    ma_period = 0          # >0 で「MAが横ばいの時だけ」エントリー
    ma_slope_bars = 10     # 傾きを測る本数
    flat_atr = 0.5         # |MA[今] - MA[slope_bars本前]| / ATR(14) がこれ未満なら横ばい

    def init(self):
        if self.ma_period:
            close = pd.Series(self.data.Close)
            self.ma = self.I(lambda: close.rolling(self.ma_period).mean().values, name="MA")
            hl = pd.Series(self.data.High) - pd.Series(self.data.Low)
            self.atr = self.I(lambda: hl.rolling(14).mean().values, name="ATR")

    def ma_is_flat(self):
        if not self.ma_period:
            return True
        n = self.ma_slope_bars
        if len(self.ma) <= n or np.isnan(self.ma[-1 - n]) or not self.atr[-1]:
            return False
        return abs(self.ma[-1] - self.ma[-1 - n]) / self.atr[-1] < self.flat_atr

    def next(self):
        if self.position or self.orders:
            return
        i = len(self.data) - 1
        if i < self.lookback + 1:
            return
        o, h, l, c = self.data.Open, self.data.High, self.data.Low, self.data.Close
        p_top, p_bot = max(o[i-1], c[i-1]), min(o[i-1], c[i-1])
        engulf = max(o[i], c[i]) >= p_top and min(o[i], c[i]) <= p_bot \
            and abs(c[i] - o[i]) > abs(c[i-1] - o[i-1])
        if not engulf or not self.ma_is_flat():
            return
        risk_cash = self.equity * self.risk_pct / 100
        if h[i] > h[i-self.lookback:i].max() and c[i] < o[i] and c[i-1] > o[i-1]:
            sl = h[i] + self.buffer
            risk = sl - c[i]
            self.sell(sl=sl, tp=c[i] - risk * self.rr, size=max(1, int(risk_cash / risk)))
        elif l[i] < l[i-self.lookback:i].min() and c[i] > o[i] and c[i-1] < o[i-1]:
            sl = l[i] - self.buffer
            risk = c[i] - sl
            self.buy(sl=sl, tp=c[i] + risk * self.rr, size=max(1, int(risk_cash / risk)))


class RegimeSwitch(Strategy):
    """
    MA100の傾きで相場を判定して手法を切り替える（RegimeSwitchEA.mq4 / .mq5 と同じルール）
      傾き = (MA[今] - MA[10本前]) / 直近14本の平均値幅
      |傾き| < flat_atr        : レンジ → 高値更新アウトサイド陰線で売り（安値は逆）
      傾き >= trend_atr        : 上昇トレンド → MA20まで押して陽の包み足、MA20より上で引けたら買い
      傾き <= -trend_atr       : 下降トレンド → 上記の逆で売り
      その間                   : 何もしない
    """
    lookback = 20
    range_rr = 2.0
    trend_rr = 2.0
    buffer = 0.02
    risk_pct = 1.0
    ma_period = 100
    fast_ma = 20
    ma_slope_bars = 10
    flat_atr = 0.5
    trend_atr = 1.0
    use_range = True
    use_trend = True

    def init(self):
        close = pd.Series(self.data.Close)
        self.ma = self.I(lambda: close.rolling(self.ma_period).mean().values, name="MA")
        self.fma = self.I(lambda: close.rolling(self.fast_ma).mean().values, name="FastMA")
        hl = pd.Series(self.data.High) - pd.Series(self.data.Low)
        self.atr = self.I(lambda: hl.rolling(14).mean().values, name="ATR")

    def next(self):
        if self.position or self.orders:
            return
        i = len(self.data) - 1
        n = self.ma_slope_bars
        if i < max(self.lookback + 1, self.ma_period + n) or not self.atr[-1]:
            return
        slope = (self.ma[-1] - self.ma[-1 - n]) / self.atr[-1]
        o, h, l, c = self.data.Open, self.data.High, self.data.Low, self.data.Close
        p_top, p_bot = max(o[i-1], c[i-1]), min(o[i-1], c[i-1])
        engulf = max(o[i], c[i]) >= p_top and min(o[i], c[i]) <= p_bot \
            and abs(c[i] - o[i]) > abs(c[i-1] - o[i-1])
        if not engulf:
            return
        bull = c[i] > o[i] and c[i-1] < o[i-1]
        bear = c[i] < o[i] and c[i-1] > o[i-1]
        risk_cash = self.equity * self.risk_pct / 100

        if abs(slope) < self.flat_atr:
            if not self.use_range:
                return
            if bear and h[i] > h[i-self.lookback:i].max():
                self._sell(h[i] + self.buffer, c[i], self.range_rr, risk_cash)
            elif bull and l[i] < l[i-self.lookback:i].min():
                self._buy(l[i] - self.buffer, c[i], self.range_rr, risk_cash)
        elif self.use_trend:
            f = self.fma[-1]
            if slope >= self.trend_atr and bull and l[i] <= f < c[i]:
                self._buy(l[i] - self.buffer, c[i], self.trend_rr, risk_cash)
            elif slope <= -self.trend_atr and bear and h[i] >= f > c[i]:
                self._sell(h[i] + self.buffer, c[i], self.trend_rr, risk_cash)

    def _buy(self, sl, entry, rr, risk_cash):
        risk = entry - sl
        self.buy(sl=sl, tp=entry + risk * rr, size=max(1, int(risk_cash / risk)))

    def _sell(self, sl, entry, rr, risk_cash):
        risk = sl - entry
        self.sell(sl=sl, tp=entry - risk * rr, size=max(1, int(risk_cash / risk)))


def run(df, pip=0.01, spread_pips=0.4, strategy=OutsideReversal, **params):
    bt = Backtest(df, strategy, cash=1_000_000, margin=1/25,
                  spread=spread_pips * pip / df.Close.mean(), finalize_trades=True)
    st = bt.run(**params)
    t = st._trades
    pips = ((t.ExitPrice - t.EntryPrice) * np.sign(t.Size) / pip)
    wins, losses = pips[pips > 0].sum(), -pips[pips <= 0].sum()
    return dict(trades=len(t), win_rate=round((pips > 0).mean() * 100, 1) if len(t) else 0,
                pf=round(wins / losses, 2) if losses else np.inf,
                total_pips=round(pips.sum()), avg_pips=round(pips.mean(), 1) if len(t) else 0,
                return_pct=round(st["Return [%]"], 1), max_dd_pct=round(st["Max. Drawdown [%]"], 1)), st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", nargs="+", required=True, help="複数の時間足CSVを並べて比較可")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--pip", type=float, default=0.01)
    ap.add_argument("--spread", type=float, default=0.4, help="スプレッド（pips）")
    a = ap.parse_args()

    rows = []
    for path in a.csv:
        df = load_csv(path) / a.scale
        for lb in (10, 20):
            for rr in (1.0, 1.5, 2.0, 3.0):
                r, _ = run(df, a.pip, a.spread, lookback=lb, rr=rr, buffer=2 * a.pip)
                rows.append(dict(data=os.path.basename(path), lookback=lb, rr=rr, **r))
    res = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(res.to_string(index=False))
    res.to_csv(os.path.join(os.path.dirname(__file__), "backtest_result_%s.csv" % os.path.splitext(os.path.basename(a.csv[0]))[0]),
               index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
