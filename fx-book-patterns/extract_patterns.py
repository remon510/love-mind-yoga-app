"""
FX書籍用チャートパターン画像抽出ツール

検出パターン:
  [売り] 高値更新アウトサイド陰線
      直近N本の最高値を上抜けたにもかかわらず陰線で引け、
      かつ前の足（陽線）を実体で包む「陰の包み足」
  [買い] 安値更新アウトサイド陽線（上記の逆）
      直近N本の最安値を下抜けたにもかかわらず陽線で引け、
      かつ前の足（陰線）を実体で包む「陽の包み足」

使い方:
  # 同梱サンプル（EURUSD 1時間足 2017-2018）で実行
  python extract_patterns.py

  # MT4/MT5 などから書き出したCSVで実行（列: Date/Time, Open, High, Low, Close）
  python extract_patterns.py --csv USDJPY_H4.csv --symbol USDJPY --tf H4

  # 白黒印刷向け
  python extract_patterns.py --mono
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

FONT = "IPAGothic"
plt.rcParams["font.family"] = FONT


def load_csv(path):
    df = pd.read_csv(path)
    cols = {c.lower().strip("<>"): c for c in df.columns}
    if "date" in cols and "time" in cols:
        idx = pd.to_datetime(df[cols["date"]].astype(str) + " " + df[cols["time"]].astype(str))
    else:
        key = next(k for k in ("datetime", "date", "time", "timestamp") if k in cols)
        idx = pd.to_datetime(df[cols[key]])
    out = pd.DataFrame({k.capitalize(): df[cols[k]].astype(float)
                        for k in ("open", "high", "low", "close")})
    out.index = pd.DatetimeIndex(idx)
    return out.sort_index()


def load_sample():
    from backtesting.test import EURUSD
    return EURUSD[["Open", "High", "Low", "Close"]].copy()


def resample(df, rule):
    return df.resample(rule).agg({"Open": "first", "High": "max",
                                  "Low": "min", "Close": "last"}).dropna()


def detect(df, lookback=20, require_opposite_prev=True, tol=0.0, gap=10):
    """パターンを検出し [(位置, 'sell'|'buy', 抜いた水準)] を返す"""
    o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
    hits, last = [], -10**9
    for i in range(lookback + 1, len(df)):
        if i - last < gap:
            continue
        prev_hi = h[i - lookback:i].max()
        prev_lo = l[i - lookback:i].min()
        p_top, p_bot = max(o[i-1], c[i-1]), min(o[i-1], c[i-1])
        engulf = max(o[i], c[i]) >= p_top - tol and min(o[i], c[i]) <= p_bot + tol \
            and abs(c[i] - o[i]) > abs(c[i-1] - o[i-1])
        if not engulf:
            continue
        if h[i] > prev_hi and c[i] < o[i] and (not require_opposite_prev or c[i-1] > o[i-1]):
            hits.append((i, "sell", prev_hi)); last = i
        elif l[i] < prev_lo and c[i] > o[i] and (not require_opposite_prev or c[i-1] < o[i-1]):
            hits.append((i, "buy", prev_lo)); last = i
    return hits


def render(df, i, side, level, path, symbol, tf, before=40, after=15, mono=False, lookback=20):
    s, e = max(0, i - before), min(len(df), i + after + 1)
    win = df.iloc[s:e]
    k = i - s  # ウィンドウ内での位置

    if mono:
        mc = mpf.make_marketcolors(up="white", down="black", edge="black", wick="black")
    else:
        mc = mpf.make_marketcolors(up="#d62728", down="#1f77b4", edge="inherit", wick="inherit")
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle=":", gridcolor="#dddddd",
                               facecolor="white", rc={"font.family": FONT})

    fig, axes = mpf.plot(win, type="candle", style=style, returnfig=True,
                         figsize=(10, 5.6), datetime_format="%m/%d %H:%M",
                         xrotation=0, tight_layout=True, ylabel="")
    ax = axes[0]
    accent = "black" if mono else "#e67e00"

    # 抜かれた直近高値/安値ライン
    ax.hlines(level, max(0, k - lookback), k + 0.5, colors="gray", linestyles="--", lw=1.2)
    ax.text(max(0, k - lookback), level, " 直近%d本の%s" % (lookback, "高値" if side == "sell" else "安値"),
            va="bottom" if side == "sell" else "top", fontsize=10, color="gray")

    # パターン2本を枠で囲む
    seg = win.iloc[k-1:k+1]
    lo, hi = seg["Low"].min(), seg["High"].max()
    pad = (win["High"].max() - win["Low"].min()) * 0.015
    ax.add_patch(plt.Rectangle((k - 1.5, lo - pad), 2, hi - lo + 2 * pad,
                               fill=False, ec=accent, lw=2))

    # 注釈
    label = "高値を抜けたのに陰線＋包み足\n→ 売りサイン" if side == "sell" \
        else "安値を割ったのに陽線＋包み足\n→ 買いサイン"
    y = hi + pad * 6 if side == "sell" else lo - pad * 6
    ax.annotate(label, xy=(k, hi + pad if side == "sell" else lo - pad), xytext=(k - 12, y),
                fontsize=12, color=accent, fontweight="bold",
                va="bottom" if side == "sell" else "top",
                arrowprops=dict(arrowstyle="->", color=accent, lw=1.5))
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(min(ymin, y - pad * 8), max(ymax, y + pad * 8))

    ax.set_title("%s %s  %s" % (symbol, tf, df.index[i].strftime("%Y-%m-%d %H:%M")),
                 fontsize=12, loc="left")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--tf", nargs="+", default=["H1", "H4"],
                    help="CSVの足をそのまま使うなら --tf raw")
    ap.add_argument("--lookback", type=int, default=20)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "images"))
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--max", type=int, default=30, help="時間足ごとの最大枚数")
    a = ap.parse_args()

    base = load_csv(a.csv) if a.csv else load_sample()
    rules = {"H1": "1h", "H4": "4h", "D1": "1D"}
    os.makedirs(a.out, exist_ok=True)
    rows = []
    for tf in a.tf:
        df = base if tf == "raw" else resample(base, rules[tf])
        hits = detect(df, lookback=a.lookback)[:a.max]
        count = {"sell": 0, "buy": 0}
        for i, side, level in hits:
            count[side] += 1
            name = "%s_%s_%s_%02d.png" % (a.symbol, tf, side, count[side])
            render(df, i, side, level, os.path.join(a.out, name), a.symbol, tf,
                   mono=a.mono, lookback=a.lookback)
            # その後10本の値動き（売りなら下落幅をプラスで表記）
            fwd = df["Close"].iloc[i+1:i+11]
            move = (df["Close"].iloc[i] - fwd.iloc[-1]) if side == "sell" else (fwd.iloc[-1] - df["Close"].iloc[i])
            rows.append(dict(file=name, tf=tf, side=side, time=df.index[i],
                             level=level, close=df["Close"].iloc[i],
                             move_after_10bars=round(move, 5) if len(fwd) else None))
        print("%s: %d 件" % (tf, len(hits)))
    pd.DataFrame(rows).to_csv(os.path.join(a.out, "list.csv"), index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
