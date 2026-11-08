"""
東京ブレイク用の Brain 広告画像
  python make_ads_tokyo.py <フォントのフォルダ>
出力: images/tokyo_thumbnail_1280x670.png, images/tokyo_x_post_1200x675.png, images/tokyo_square_1080x1080.png
"""
import os
import sys

import pandas as pd
from PIL import ImageDraw

import make_ads as A

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = "※2012年11月〜2022年3月のドル円15分足バックテスト（スプレッド0.3pips、1回のリスク1%）。将来の利益を保証するものではありません。"


def footnote(d, w, h, size=14):
    A.text(d, (w // 2, h - 14), NOTE, A.font("Medium", size), A.GRAY, anchor="md")


def thumbnail(eq, path):
    w, h = 1280, 670
    img = A.background(w, h)
    d = ImageDraw.Draw(img)
    A.badge(d, (60, 50), "ドル円デイトレ・1日1回", A.font("ExtraBold", 28), A.NAVY1, A.GOLD)
    A.text(d, (60, 118), "東京で溜めて、ロンドンで放つ。", A.font("Bold", 42), A.WHITE)
    A.text(d, (52, 190), "東京ブレイク", A.font("Black", 128), A.GOLD2, stroke=3, stroke_fill=(120, 80, 10))
    A.text(d, (62, 352), "日本時間の夕方に判断 → 翌朝には決済", A.font("Bold", 32), A.WHITE)
    x = A.badge(d, (62, 430), "9年・2,053トレード検証", A.font("ExtraBold", 28), A.WHITE, (180, 50, 45))
    A.badge(d, (x + 24, 430), "EA付き", A.font("ExtraBold", 28), A.NAVY1, A.WHITE)
    A.text(d, (62, 500), "勝率48%でも残高が増えた理由を、全部見せます", A.font("Bold", 26), A.GRAY)
    card = (790, 60, 1230, 560)
    A.panel(img, card)
    d = ImageDraw.Draw(img)
    A.text(d, (card[0] + 28, card[1] + 24), "口座残高の推移（バックテスト）", A.font("Bold", 24), A.WHITE)
    A.text(d, (card[0] + 28, card[1] + 62), "9年で 約3倍", A.font("Black", 52), A.GOLD2)
    A.text(d, (card[0] + 28, card[1] + 128), "リスク1%/回・最大の落ち込み −24%", A.font("Bold", 22), A.GRAY)
    A.equity_curve(img, (card[0] + 30, card[1] + 190, card[2] - 30, card[3] - 50), eq)
    footnote(d, w, h)
    img.save(path)


def x_post(t, path):
    w, h = 1200, 675
    img = A.background(w, h)
    d = ImageDraw.Draw(img)
    A.text(d, (w // 2, 46), "ドル円「東京ブレイク」9年間の年別成績", A.font("Bold", 36), A.WHITE, anchor="ma")
    A.text(d, (w // 2, 96), "9年中7年プラス。負けた年も隠しません", A.font("Black", 50), A.GOLD2, anchor="ma")
    y = t.groupby(t.date.dt.year).pips.sum()
    x0, x1, base, scale = 90, 1110, 430, 0.2          # 1pips = 0.2px
    bw = (x1 - x0) / len(y)
    d.line([(x0 - 10, base), (x1 + 10, base)], fill=(255, 255, 255, 160), width=2)
    for i, (yr, v) in enumerate(y.items()):
        cx = x0 + bw * i + bw / 2
        top = base - v * scale
        d.rounded_rectangle([cx - bw * 0.32, min(top, base), cx + bw * 0.32, max(top, base)], radius=4,
                            fill=A.GOLD if v > 0 else A.RED)
        A.text(d, (cx, top - 8 if v > 0 else top + 8), f"{v:+.0f}", A.font("Black", 22),
               A.GOLD2 if v > 0 else (240, 140, 130), anchor="md" if v > 0 else "ma")
        A.text(d, (cx, 560), str(yr), A.font("Bold", 20), A.GRAY, anchor="ma")
    A.text(d, (x0, 600), "年ごとの損益（pips）　※「9年中7年」は丸1年ある2013〜2021年。2012年・2022年は一部の期間のみ", A.font("Medium", 18), A.GRAY)
    footnote(d, w, h)
    img.save(path)


def square(path):
    w, h = 1080, 1080
    img = A.background(w, h)
    d = ImageDraw.Draw(img)
    A.badge(d, (70, 70), "Brainで公開中", A.font("ExtraBold", 32), A.NAVY1, A.GOLD)
    A.text(d, (70, 150), "ドル円デイトレ", A.font("Black", 72), A.WHITE)
    A.text(d, (62, 234), "東京ブレイク", A.font("Black", 140), A.GOLD2, stroke=3, stroke_fill=(120, 80, 10))
    items = ["ルールは3つだけ。夕方に判断、翌朝に決済", "東京の値幅・ブレイク・損切りを図で解説",
             "実例チャート11枚（負け4例も解説）", "9年・2,053トレードの検証データ",
             "連敗・負け年の乗り越え方とロット計算", "そのまま使えるEA（MT4/MT5）"]
    for i, s in enumerate(items):
        yy = 440 + i * 70
        d.ellipse([74, yy + 8, 102, yy + 36], fill=A.GOLD)
        A.text(d, (88, yy + 22), "✓", A.font("Black", 22), A.NAVY1, anchor="mm")
        A.text(d, (124, yy), s, A.font("Bold", 34), A.WHITE)
    A.text(d, (w // 2, 900), "勝率48%。それでも資産は増えた。", A.font("Black", 42), A.GOLD2, anchor="ma")
    footnote(d, w, h, 13)
    img.save(path)


def main():
    A.FONT_DIR = sys.argv[1] if len(sys.argv) > 1 else A.FONT_DIR
    t = pd.read_csv(os.path.join(HERE, "..", "tokyo", "trades.csv"), parse_dates=["date"])
    eq = pd.Series((1 + t.r / 100).cumprod().values * 100, index=t.date)
    out = os.path.join(HERE, "images")
    thumbnail(eq, os.path.join(out, "tokyo_thumbnail_1280x670.png"))
    x_post(t, os.path.join(out, "tokyo_x_post_1200x675.png"))
    square(os.path.join(out, "tokyo_square_1080x1080.png"))


if __name__ == "__main__":
    main()
