"""
東京ブレイクの実例チャート（15分足、日本時間表示）
  python render_examples.py DATA_DIR
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from extract_patterns import load_csv  # noqa: E402
from jst import to_jst  # noqa: E402

FONT = "IPAGothic"
plt.rcParams["font.family"] = FONT
PIP = 0.01
EXAMPLES = ["2013-02-25", "2016-02-03", "2019-08-01", "2018-03-28", "2014-12-05", "2017-10-18",
            "2020-02-25", "2019-01-24", "2018-05-22", "2017-06-07", "2013-08-19"]


def render(m15, t, path):
    day = m15[m15.index.date == t.date.date()]
    s = day.index.searchsorted(t.date + pd.Timedelta(hours=1))
    e = min(len(day), day.index.searchsorted(t.exit_time) + 5)
    win = day.iloc[s:e].copy()
    win.index = to_jst(win.index)
    pos = lambda ts: int(pd.DatetimeIndex(to_jst([ts]))[0].to_pydatetime().timestamp())  # noqa: E731
    stamps = [int(x.timestamp()) for x in win.index.to_pydatetime()]
    k = lambda ts: stamps.index(pos(ts))  # noqa: E731
    rs, re_ = k(t.date + pd.Timedelta(hours=3)), k(t.date + pd.Timedelta(hours=9, minutes=45))
    ks, ke, kx = k(t.signal_time), k(t.entry_time), k(t.exit_time)
    buy = t.side > 0
    won = t.pips > 0

    mc = mpf.make_marketcolors(up="#d62728", down="#1f77b4", edge="inherit", wick="inherit")
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle=":", gridcolor="#e3e3e3",
                               facecolor="white", rc={"font.family": FONT})
    fig, axes = mpf.plot(win, type="candle", style=style, returnfig=True, figsize=(10, 5.8),
                         datetime_format="%H:%M", xrotation=0, tight_layout=True, ylabel="")
    ax = axes[0]
    top = max(win.High.max(), t.stop, t.exit)
    bot = min(win.Low.min(), t.stop, t.exit)
    span = top - bot
    ax.set_ylim(bot - span * 0.10, top + span * 0.14)
    # 東京時間の値幅
    ax.add_patch(plt.Rectangle((rs - 0.5, t.range_lo), re_ - rs + 1, t.range_hi - t.range_lo,
                               fc="#f2c454", alpha=0.22, ec="#d9a521", lw=1.2))
    ax.text((rs + re_) / 2, t.range_hi - span * 0.01, "東京時間の値幅", ha="center", va="top",
            fontsize=10, color="#9a7413", bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5))
    for lvl in (t.range_hi, t.range_lo):
        ax.hlines(lvl, re_ + 0.5, len(win) - 0.5, colors="#d9a521", linestyles=":", lw=1.2)
    # ブレイクした足
    lvl = t.range_hi if buy else t.range_lo
    ax.annotate("ブレイク", xy=(ks, lvl),
                xytext=(ks + 3, lvl + (1 if buy else -1) * span * 0.08),
                fontsize=11, color="#e67e00", fontweight="bold",
                bbox=dict(fc="white", ec="#e67e00", alpha=0.9, boxstyle="round,pad=0.2"),
                arrowprops=dict(arrowstyle="->", color="#e67e00", lw=1.5))
    # エントリー・損切り・決済
    x1 = len(win) + 0.2
    ax.hlines(t.entry, ke - 0.4, x1, colors="black", lw=1.3)
    ax.hlines(t.stop, ke - 0.4, x1, colors="#c0392b", linestyles="--", lw=1.3)
    ax.annotate("", xy=(ke, t.entry), xytext=(ke, t.entry + (-1 if buy else 1) * span * 0.1),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))
    col = "#1e8449" if won else "#c0392b"
    ax.plot([kx], [t.exit], marker="X", ms=12, color=col, mec="white", zorder=6)
    lx = x1 + 0.4
    jt = lambda ts: to_jst([ts])[0].strftime("%H:%M")  # noqa: E731
    ax.text(lx, t.entry, f"エントリー {t.entry:.2f}\n{jt(t.entry_time)}", fontsize=9.5, va="center")
    if t.exit_reason == "損切り":
        ax.text(lx, t.stop, f"損切り {t.stop:.2f}\n{jt(t.exit_time)} −{abs(t.pips):.0f} pips", fontsize=9.5,
                va="center", color="#c0392b")
    else:
        ax.text(lx, t.stop, f"損切り {t.stop:.2f}\n（−{t.risk_pips:.0f} pips）", fontsize=9.5, va="center",
                color="#c0392b")
        y = t.exit
        if abs(t.exit - t.entry) < span * 0.09:          # エントリーのラベルと重ならないようにずらす
            y = t.entry + (span * 0.09 if t.exit >= t.entry else -span * 0.09)
        ax.text(lx, y, f"時間決済 {t.exit:.2f}\n{jt(t.exit_time)} {'＋' if won else '−'}{abs(t.pips):.0f} pips",
                fontsize=9.5, va="center", color=col)
    ax.set_xlim(-1, len(win) + 9)
    date_jst = to_jst([t.signal_time])[0]
    ax.set_title("USDJPY 15分足（日本時間）　%s　%s　結果 %s%d pips（%s）" % (
        date_jst.strftime("%Y/%m/%d"), "買い" if buy else "売り", "＋" if won else "−",
        abs(round(t.pips)), t.exit_reason), loc="left", fontsize=12, color=col)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    m15 = load_csv(os.path.join(sys.argv[1], "USDJPYm15.csv")) / 1000
    t = pd.read_csv(os.path.join(HERE, "trades.csv"),
                    parse_dates=["date", "signal_time", "entry_time", "exit_time"])
    out = os.path.join(HERE, "figures")
    os.makedirs(out, exist_ok=True)
    for d in EXAMPLES:
        row = t[t.date == d].iloc[0]
        render(m15, row, os.path.join(out, f"ex_{d}.png"))


if __name__ == "__main__":
    main()
