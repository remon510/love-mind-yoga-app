"""
書籍用: バックテストの各トレードを、エントリー・損切り・利確・結果(pips)入りのチャート画像にする
  python render_trades.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ea"))
from backtest import RegimeSwitch, load_csv, run  # noqa: E402

FONT = "IPAGothic"
plt.rcParams["font.family"] = FONT
PIP = 0.01
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("USDJPY_H4_CSV", os.path.join(HERE, "USDJPYh4.csv"))


def render(df, t, kind, path, before=45, after=6, max_len=90):
    eb, xb = int(t.EntryBar), int(t.ExitBar)
    sig = eb - 1
    s = max(0, sig - before)
    e = min(len(df), min(xb, eb + max_len) + after + 1)
    win = df.iloc[s:e].copy()
    k = sig - s                       # パターン足の位置
    ke, kx = eb - s, min(xb, e - 1) - s
    buy = t.Size > 0
    entry = df.Open.iloc[eb]
    sl, tp = t.SL, t.TP
    risk_p = abs(entry - sl) / PIP
    reward_p = abs(tp - entry) / PIP
    res_p = (t.ExitPrice - entry) / PIP * (1 if buy else -1)
    won = res_p > 0

    mc = mpf.make_marketcolors(up="#d62728", down="#1f77b4", edge="inherit", wick="inherit")
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle=":", gridcolor="#dddddd",
                               facecolor="white", rc={"font.family": FONT})
    ma100 = df.Close.rolling(100).mean().iloc[s:e]
    ma20 = df.Close.rolling(20).mean().iloc[s:e]
    aps = [mpf.make_addplot(ma100, color="#7f7f7f", width=1.6)]
    if kind == "trend":
        aps.append(mpf.make_addplot(ma20, color="#9467bd", width=1.2, linestyle="--"))
    fig, axes = mpf.plot(win, type="candle", style=style, addplot=aps, returnfig=True,
                         figsize=(10, 5.8), datetime_format="%Y/%m/%d", xrotation=0,
                         tight_layout=True, ylabel="")
    ax = axes[0]
    span = win.High.max() - win.Low.min()
    pad = span * 0.012

    # パターン2本を枠で囲む
    seg = win.iloc[k-1:k+1]
    ax.add_patch(plt.Rectangle((k - 1.5, seg.Low.min() - pad), 2,
                               seg.High.max() - seg.Low.min() + 2 * pad,
                               fill=False, ec="#e67e00", lw=2.2, zorder=5))
    if kind == "range":
        lb = 20
        lvl = win.High.iloc[k-lb:k].max() if not buy else win.Low.iloc[k-lb:k].min()
        ax.hlines(lvl, k - lb, k + 0.5, colors="#555555", linestyles=":", lw=1.3)
        ax.text(k - lb, lvl, "直近20本の%s " % ("安値" if buy else "高値"), fontsize=9,
                color="#555555", ha="left", va="top" if buy else "bottom")

    # エントリー・損切り・利確ライン（ラベルは右余白にまとめる）
    x0, x1 = ke - 0.4, len(win) + 0.2
    ax.hlines(entry, x0, x1, colors="black", lw=1.4)
    ax.hlines(sl, x0, x1, colors="#c0392b", linestyles="--", lw=1.4)
    ax.hlines(tp, x0, x1, colors="#1e8449", linestyles="--", lw=1.4)
    lx = x1 + 0.4
    ax.text(lx, entry, "エントリー\n%.2f" % entry, fontsize=10, va="center", linespacing=1.1)
    ax.text(lx, sl, "損切り %.2f\n−%d pips" % (sl, round(risk_p)), fontsize=10,
            va="center", color="#c0392b", linespacing=1.1)
    ax.text(lx, tp, "利確 %.2f\n＋%d pips" % (tp, round(reward_p)), fontsize=10,
            va="center", color="#1e8449", linespacing=1.1)
    ax.annotate("", xy=(ke, entry), xytext=(ke, entry + (-1 if buy else 1) * span * 0.08),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))
    ax.plot([kx], [t.ExitPrice], marker="X", ms=12, color="#1e8449" if won else "#c0392b",
            zorder=6, mec="white")

    # 環境認識（MA100の傾き）
    ma = df.Close.rolling(100).mean()
    atr = (df.High - df.Low).rolling(14).mean()
    slope = (ma.iloc[sig] - ma.iloc[sig - 10]) / atr.iloc[sig]
    regime = "横ばい（レンジ）" if abs(slope) < 0.5 else ("上昇トレンド" if slope > 0 else "下降トレンド")
    note = "MA100の傾き %+.2f → %s" % (slope, regime)
    if kind == "trend":
        note += "\n灰線: MA100　紫破線: MA20"
    else:
        note += "\n灰線: MA100"
    ax.text(0.01, 0.02 if not buy else 0.98, note, transform=ax.transAxes, fontsize=9.5,
            va="bottom" if not buy else "top",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#bbbbbb"))

    label = "%s　結果 %s%d pips（%s）" % ("買い" if buy else "売り", "＋" if won else "−",
                                     abs(round(res_p)), "利確" if won else "損切り")
    ax.set_title("USDJPY 4時間足　%s　%s" % (df.index[sig].strftime("%Y/%m/%d %H:%M"), label),
                 fontsize=12, loc="left", color="#1e8449" if won else "#c0392b")
    ax.set_xlim(-1, len(win) + 8)
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(min(ymin, sl - pad * 3, tp - pad * 3), max(ymax, sl + pad * 3, tp + pad * 3))
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return dict(sig_time=df.index[sig], side="買い" if buy else "売り", entry=round(entry, 3),
                sl=sl, tp=tp, risk_pips=round(risk_p), reward_pips=round(reward_p),
                result_pips=round(res_p), bars=xb - eb + 1, slope=round(slope, 2), exit_time=df.index[min(xb, len(df)-1)])


def main():
    df = load_csv(DATA) / 1000
    out = os.path.join(HERE, "trades")
    os.makedirs(out, exist_ok=True)
    rows = []
    for kind, kw in (("range", dict(use_trend=False)), ("trend", dict(use_range=False))):
        _, st = run(df, PIP, 0.4, strategy=RegimeSwitch, buffer=2 * PIP, **kw)
        for n, t in enumerate(st._trades.itertuples(), 1):
            name = "%s_%02d.png" % (kind, n)
            info = render(df, t, kind, os.path.join(out, name))
            rows.append(dict(file=name, kind=kind, **info))
    pd.DataFrame(rows).to_csv(os.path.join(out, "trades.csv"), index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
