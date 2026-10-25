"""書籍用: 型A・型Bの模式図"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = "IPAGothic"
HERE = os.path.dirname(os.path.abspath(__file__))
UP, DN = "#d62728", "#1f77b4"


def candles(ax, ohlc):
    for i, (o, h, l, c) in enumerate(ohlc):
        col = UP if c >= o else DN
        ax.vlines(i, l, h, color=col, lw=1.4, zorder=2)
        ax.add_patch(plt.Rectangle((i - 0.32, min(o, c)), 0.64, max(abs(c - o), 0.02),
                                   fc=col, ec=col, zorder=3))


def finish(ax, path, title):
    ax.set_title(title, loc="left", fontsize=13)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    plt.tight_layout()
    plt.savefig(path, dpi=200, facecolor="white")
    plt.close()


def range_diagram(path):
    ohlc = [(100.6, 101.0, 100.3, 100.9), (100.9, 101.5, 100.8, 101.4), (101.4, 101.9, 101.2, 101.8),
            (101.8, 102.0, 101.3, 101.4), (101.4, 101.5, 100.8, 100.9), (100.9, 101.0, 100.2, 100.3),
            (100.3, 100.5, 99.9, 100.1), (100.1, 100.7, 100.0, 100.6), (100.6, 101.2, 100.5, 101.1),
            (101.1, 101.3, 100.7, 100.8), (100.8, 101.0, 100.4, 100.5), (100.5, 101.1, 100.4, 101.0),
            (101.0, 101.6, 100.9, 101.5), (101.5, 101.8, 101.3, 101.7),
            (101.7, 102.35, 101.15, 101.25)]      # 陰の包み足
    nxt = [(101.25, 101.4, 100.8, 100.9), (100.9, 101.0, 100.3, 100.4), (100.4, 100.6, 99.9, 100.0)]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    candles(ax, ohlc + nxt)
    x = np.arange(len(ohlc) + len(nxt))
    ax.plot(x, 101.0 + 0.04 * np.sin(x / 3), color="#7f7f7f", lw=2, label="MA100（ほぼ水平）")
    k = len(ohlc) - 1
    ax.hlines(102.0, 2, k + 0.4, colors="#555555", linestyles=":", lw=1.5)
    ax.text(2, 102.03, "直近20本の高値", fontsize=10, color="#555555", va="bottom")
    ax.add_patch(plt.Rectangle((k - 1.5, 101.05), 2, 1.45, fill=False, ec="#e67e00", lw=2.2))
    sl, entry = 102.35 + 0.08, 101.25
    tp = entry - (sl - entry) * 2
    xe = k + 1
    ax.hlines(entry, xe - 0.4, x[-1] + 0.6, colors="black", lw=1.4)
    ax.hlines(sl, xe - 0.4, x[-1] + 0.6, colors="#c0392b", linestyles="--", lw=1.4)
    ax.hlines(tp, xe - 0.4, x[-1] + 0.6, colors="#1e8449", linestyles="--", lw=1.4)
    lx = x[-1] + 0.8
    ax.text(lx, entry, "③ 次の足の始値で売り", fontsize=11, va="center")
    ax.text(lx, sl, "損切り：パターン足の高値＋2pips", fontsize=11, va="center", color="#c0392b")
    ax.text(lx, tp, "利確：損切り幅の2倍", fontsize=11, va="center", color="#1e8449")
    ax.annotate("① 直近高値を上抜けたのに\n　 陰線で引けた", xy=(k, 102.35), xytext=(k - 9.5, 102.75),
                fontsize=11, arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.annotate("② 前の陽線を\n　 実体で包む", xy=(k - 0.9, 101.6), xytext=(k - 6.5, 100.0),
                fontsize=11, arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.text(0.2, 98.6, "前提：MA100が横ばい（レンジ相場）", fontsize=11,
            bbox=dict(boxstyle="round", fc="#f4f4f4", ec="#bbbbbb"))
    ax.set_xlim(-1, x[-1] + 9)
    ax.set_ylim(98.4, 103.2)
    ax.legend(loc="upper left", fontsize=10, frameon=False)
    finish(ax, path, "図A　型A：レンジ逆張り（売りの場合）")


def trend_diagram(path):
    base = np.linspace(100, 104, 22)
    ohlc = []
    for i in range(14):
        o = base[i] + 0.1
        c = o + (0.45 if i % 4 != 3 else -0.25)
        ohlc.append((o, max(o, c) + 0.12, min(o, c) - 0.1, c))
    # 押し目（下げ）
    last = ohlc[-1][3]
    for d in (-0.35, -0.3, -0.25):
        o = last; c = o + d
        ohlc.append((o, o + 0.08, c - 0.1, c)); last = c
    o = last; c = o + 0.7                                  # 陽の包み足（MA20にタッチして上で引ける）
    ohlc[-1] = (ohlc[-1][0], ohlc[-1][1], ohlc[-1][2], ohlc[-1][3])
    ohlc.append((o - 0.02, c + 0.08, o - 0.45, c))
    nxt = [(c, c + 0.5, c - 0.05, c + 0.45), (c + 0.45, c + 0.95, c + 0.4, c + 0.9),
           (c + 0.9, c + 1.5, c + 0.85, c + 1.45)]
    allc = ohlc + nxt
    x = np.arange(len(allc))
    closes = np.array([q[3] for q in allc])
    ma20 = np.array([closes[max(0, i - 5):i + 1].mean() for i in range(len(closes))]) - 0.15
    ma100 = 98.8 + x * 0.16
    fig, ax = plt.subplots(figsize=(10, 5.6))
    k0 = len(ohlc) - 1
    allc[k0] = (allc[k0][0], allc[k0][1], ma20[k0] - 0.12, allc[k0][3])
    candles(ax, allc)
    ax.plot(x, ma100, color="#7f7f7f", lw=2, label="MA100（右肩上がり）")
    ax.plot(x, ma20, color="#9467bd", lw=1.6, ls="--", label="MA20")
    k = len(ohlc) - 1
    lo, hi = allc[k][2], allc[k][1]
    ax.add_patch(plt.Rectangle((k - 1.5, min(lo, allc[k-1][2]) - 0.1), 2,
                               max(hi, allc[k-1][1]) - min(lo, allc[k-1][2]) + 0.2,
                               fill=False, ec="#e67e00", lw=2.2))
    entry, sl = allc[k][3], lo - 0.08
    tp = entry + (entry - sl) * 2
    xe = k + 1
    ax.hlines(entry, xe - 0.4, x[-1] + 0.6, colors="black", lw=1.4)
    ax.hlines(sl, xe - 0.4, x[-1] + 0.6, colors="#c0392b", linestyles="--", lw=1.4)
    ax.hlines(tp, xe - 0.4, x[-1] + 0.6, colors="#1e8449", linestyles="--", lw=1.4)
    lx = x[-1] + 0.8
    ax.text(lx, entry, "③ 次の足の始値で買い", fontsize=11, va="center")
    ax.text(lx, sl, "損切り：パターン足の安値−2pips", fontsize=11, va="center", color="#c0392b")
    ax.text(lx, tp, "利確：損切り幅の2倍", fontsize=11, va="center", color="#1e8449")
    ax.annotate("① MA20まで押す\n　 （安値がMA20に届く）", xy=(k, lo), xytext=(k - 8, lo - 1.4),
                fontsize=11, arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.annotate("② 陽の包み足が\n　 MA20より上で引ける", xy=(k, entry), xytext=(k - 12, entry + 1.0),
                fontsize=11, arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.text(0.2, ax.get_ylim()[1] if False else 106.6, "前提：MA100がはっきり右肩上がり（上昇トレンド）",
            fontsize=11, bbox=dict(boxstyle="round", fc="#f4f4f4", ec="#bbbbbb"))
    ax.set_xlim(-1, x[-1] + 9)
    ax.set_ylim(98.5, 107.2)
    ax.legend(loc="lower right", fontsize=10, frameon=False)
    finish(ax, path, "図B　型B：順張り押し目買い（上昇トレンドの場合）")


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
    range_diagram(os.path.join(HERE, "figures", "diagram_A.png"))
    trend_diagram(os.path.join(HERE, "figures", "diagram_B.png"))
