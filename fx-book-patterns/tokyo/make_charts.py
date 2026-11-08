"""東京ブレイクの成績グラフ（残高推移・年別・リスク別）"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = "IPAGothic"
HERE = os.path.dirname(os.path.abspath(__file__))
t = pd.read_csv(os.path.join(HERE, "trades.csv"), parse_dates=["date"])
out = os.path.join(HERE, "figures")

# 残高推移（リスク0.5%・1%・2%）
fig, ax = plt.subplots(figsize=(10, 4.8))
for rp, c in ((0.5, "#999999"), (1.0, "#e67e00"), (2.0, "#1f77b4")):
    eq = (1 + t.r * rp / 100).cumprod() * 100
    dd = (eq / eq.cummax() - 1).min() * 100
    ax.plot(t.date, eq, color=c, lw=1.5, label=f"リスク{rp:g}%/回：{eq.iloc[-1]:.0f}万円（最大の落ち込み{dd:.0f}%）")
ax.axhline(100, color="black", lw=0.8, ls=":")
ax.axvline(pd.Timestamp("2018-01-01"), color="black", lw=0.8, ls=":")
ax.text(pd.Timestamp("2018-01-01"), ax.get_ylim()[1], " 2018年〜", va="top")
ax.set_title("東京ブレイク　口座残高の推移（元本100万円・ドル円15分足・2012/11〜2022/03）", loc="left", fontsize=12)
ax.set_ylabel("万円")
ax.grid(alpha=0.3)
ax.legend(loc="upper left", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(out, "equity.png"), dpi=200)
plt.close(fig)

# 年別損益（pips）
y = t.groupby(t.date.dt.year).pips.sum()
fig, ax = plt.subplots(figsize=(10, 4))
bars = ax.bar(y.index.astype(str), y.values, color=["#1e8449" if v > 0 else "#c0392b" for v in y.values])
for b, v in zip(bars, y.values):
    ax.text(b.get_x() + b.get_width() / 2, v + (25 if v > 0 else -25), f"{v:+.0f}", ha="center",
            va="bottom" if v > 0 else "top", fontsize=10)
ax.axhline(0, color="black", lw=0.8)
ax.set_ylim(y.min() - 160, y.max() + 160)
ax.set_title("東京ブレイク　年ごとの損益（pips、スプレッド0.3pips込み）", loc="left", fontsize=12)
ax.text(0.99, 0.02, "2012年・2022年は一部の期間のみ", transform=ax.transAxes, ha="right", fontsize=9, color="#666666")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(out, "yearly.png"), dpi=200)
plt.close(fig)
