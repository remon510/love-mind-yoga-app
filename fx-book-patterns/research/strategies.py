"""
手法探索用の売買ルール（backtesting.py の Strategy）
すべて「足の確定で判断 → 次の足の始値で約定」。1回のリスクは残高の risk_pct%。
"""
import numpy as np
import pandas as pd
from backtesting import Strategy


def atr(data, n=20):
    h, l, c = pd.Series(data.High), pd.Series(data.Low), pd.Series(data.Close)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean().values


class Base(Strategy):
    risk_pct = 1.0
    stop_atr = 2.0

    def size_for(self, risk):
        return max(1, int(self.equity * self.risk_pct / 100 / risk))


class Donchian(Base):
    """N本高値ブレイクで買い・N本安値ブレイクで売り。M本の逆側チャネルでトレーリング決済（タートル型）"""
    entry_n = 55
    exit_n = 20

    def init(self):
        h, l = pd.Series(self.data.High), pd.Series(self.data.Low)
        self.hi = self.I(lambda: h.rolling(self.entry_n).max().shift(1).values, name="HiN")
        self.lo = self.I(lambda: l.rolling(self.entry_n).min().shift(1).values, name="LoN")
        self.xhi = self.I(lambda: h.rolling(self.exit_n).max().values, name="HiM")
        self.xlo = self.I(lambda: l.rolling(self.exit_n).min().values, name="LoM")
        self.atr = self.I(atr, self.data, name="ATR")

    def next(self):
        c, a = self.data.Close[-1], self.atr[-1]
        if np.isnan(self.hi[-1]) or np.isnan(a) or not a:
            return
        for t in self.trades:                       # トレーリング（逆側Mチャネル）
            if t.is_long:
                t.sl = max(t.sl, self.xlo[-1])
            else:
                t.sl = min(t.sl, self.xhi[-1])
        if self.position or self.orders:
            return
        risk = self.stop_atr * a
        if c > self.hi[-1]:
            self.buy(sl=c - risk, size=self.size_for(risk))
        elif c < self.lo[-1]:
            self.sell(sl=c + risk, size=self.size_for(risk))


class MACross(Base):
    """短期MAが長期MAの上なら買い・下なら売り（ドテン）。ATRの倍数でトレーリングストップ"""
    fast = 50
    slow = 200
    trail_atr = 3.0

    def init(self):
        c = pd.Series(self.data.Close)
        self.f = self.I(lambda: c.rolling(self.fast).mean().values, name="Fast")
        self.s = self.I(lambda: c.rolling(self.slow).mean().values, name="Slow")
        self.atr = self.I(atr, self.data, name="ATR")

    def next(self):
        c, a = self.data.Close[-1], self.atr[-1]
        if np.isnan(self.s[-1]) or np.isnan(a) or not a:
            return
        up = self.f[-1] > self.s[-1]
        for t in self.trades:
            if t.is_long:
                t.sl = max(t.sl, c - self.trail_atr * a)
                if not up:
                    t.close()
            else:
                t.sl = min(t.sl, c + self.trail_atr * a)
                if up:
                    t.close()
        if self.trades or self.orders:
            return
        # クロスした直後だけ入る（トレーリングで切られたあとは次のクロスを待つ）
        crossed = (self.f[-2] > self.s[-2]) != up if len(self.f) > 2 and not np.isnan(self.s[-2]) else False
        if not crossed:
            return
        risk = self.stop_atr * a
        if up:
            self.buy(sl=c - risk, size=self.size_for(risk))
        else:
            self.sell(sl=c + risk, size=self.size_for(risk))


class RSI2(Base):
    """長期MAの方向に、RSI(2)の売られすぎ（買われすぎ）で押し目買い（戻り売り）。短期MA回帰で決済"""
    trend_ma = 200
    exit_ma = 5
    lo = 10
    hi = 90

    def init(self):
        c = pd.Series(self.data.Close)
        d = c.diff()
        up = d.clip(lower=0).ewm(alpha=1 / 2, adjust=False).mean()
        dn = (-d.clip(upper=0)).ewm(alpha=1 / 2, adjust=False).mean()
        self.rsi = self.I(lambda: (100 - 100 / (1 + up / dn.replace(0, np.nan))).values, name="RSI2")
        self.tm = self.I(lambda: c.rolling(self.trend_ma).mean().values, name="TrendMA")
        self.em = self.I(lambda: c.rolling(self.exit_ma).mean().values, name="ExitMA")
        self.atr = self.I(atr, self.data, name="ATR")

    def next(self):
        c, a = self.data.Close[-1], self.atr[-1]
        if np.isnan(self.tm[-1]) or np.isnan(a) or not a or np.isnan(self.rsi[-1]):
            return
        for t in self.trades:
            if (t.is_long and c > self.em[-1]) or (t.is_short and c < self.em[-1]):
                t.close()
        if self.trades or self.orders:
            return
        risk = self.stop_atr * a
        if c > self.tm[-1] and self.rsi[-1] < self.lo:
            self.buy(sl=c - risk, size=self.size_for(risk))
        elif c < self.tm[-1] and self.rsi[-1] > self.hi:
            self.sell(sl=c + risk, size=self.size_for(risk))
