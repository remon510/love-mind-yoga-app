"""
Brain 販売用の広告画像を作る
  python make_ads.py <フォントのフォルダ>
フォント: M PLUS 1p（Google Fonts / OFL）の Black・ExtraBold・Bold・Medium を使う
出力: thumbnail_1280x670.png（Brainサムネイル）, x_post_1200x675.png, square_1080x1080.png
"""
import os
import sys

import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "fonts")
NAVY1, NAVY2 = (8, 20, 43), (22, 44, 82)
GOLD, GOLD2 = (242, 196, 84), (255, 226, 140)
WHITE, GRAY = (245, 247, 250), (160, 172, 190)
RED = (235, 90, 80)
NOTE = "※2012年11月〜2022年3月のドル円4時間足バックテスト（1回のリスク3%）。将来の利益を保証するものではありません。"


def font(weight, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, f"MPLUS1p-{weight}.ttf"), size)


def background(w, h):
    img = Image.new("RGB", (w, h), NAVY1)
    d = ImageDraw.Draw(img)
    for y in range(h):                                   # 縦グラデーション
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(NAVY1, NAVY2)))
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))       # うっすらチャートの罫線
    g = ImageDraw.Draw(grid)
    for x in range(0, w, 64):
        g.line([(x, 0), (x, h)], fill=(255, 255, 255, 10))
    for y in range(0, h, 64):
        g.line([(0, y), (w, y)], fill=(255, 255, 255, 10))
    img.paste(grid, (0, 0), grid)
    return img


def text(d, xy, s, f, fill, anchor="la", stroke=0, stroke_fill=None):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def badge(d, xy, s, f, fg, bg, pad=(18, 8), radius=12):
    x, y = xy
    l, t, r, b = d.textbbox((x, y), s, font=f)
    d.rounded_rectangle([l - pad[0], t - pad[1], r + pad[0], b + pad[1]], radius=radius, fill=bg)
    d.text((x, y), s, font=f, fill=fg)
    return r + pad[0]


def equity_curve(img, box, eq, label=True):
    """box=(x0,y0,x1,y1) に残高推移を描く（金色の線＋下を薄く塗る）"""
    x0, y0, x1, y1 = box
    lo, hi = eq.min() * 0.95, eq.max() * 1.03
    n = len(eq)
    pts = [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0) * (v - lo) / (hi - lo)) for i, v in enumerate(eq.values)]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(pts + [(x1, y1), (x0, y1)], fill=GOLD + (45,))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).line(pts, fill=GOLD + (160,), width=10)
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    img.paste(glow, (0, 0), glow)
    d.line(pts, fill=GOLD2 + (255,), width=4)
    base_y = y1 - (y1 - y0) * (100 - lo) / (hi - lo)       # 元本ライン
    for xx in range(int(x0), int(x1), 14):
        d.line([(xx, base_y), (xx + 7, base_y)], fill=(255, 255, 255, 90), width=2)
    img.paste(layer, (0, 0), layer)
    d2 = ImageDraw.Draw(img)
    if label:
        f = font("Bold", 20)
        text(d2, (x0, base_y - 8), "元本 100万円", f, GRAY, anchor="ld")
        text(d2, (x1, pts[-1][1] - 14), f"約{eq.iloc[-1]:.0f}万円", font("Black", 30), GOLD2, anchor="rb")
        text(d2, (x0, y1 + 8), str(eq.index[0].year), font("Medium", 18), GRAY)
        text(d2, (x1, y1 + 8), str(eq.index[-1].year), font("Medium", 18), GRAY, anchor="ra")


def panel(img, box):
    """半透明のカード"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=22, fill=(255, 255, 255, 18),
                                            outline=(255, 255, 255, 60), width=2)
    img.paste(layer, (0, 0), layer)


def footnote(d, w, h, size=15):
    text(d, (w // 2, h - 14), NOTE, font("Medium", size), GRAY, anchor="md")


def thumbnail(eq, path):
    w, h = 1280, 670
    img = background(w, h)
    d = ImageDraw.Draw(img)
    badge(d, (60, 52), "9年分のデータで検証", font("ExtraBold", 28), NAVY1, GOLD)
    text(d, (60, 120), "勝てない手法を9割捨てたら、", font("Bold", 40), WHITE)
    text(d, (60, 172), "残ったのはこの「型」だけだった。", font("Bold", 40), WHITE)
    text(d, (56, 238), "ドル円4時間足", font("Black", 64), WHITE)
    text(d, (52, 312), "包み足の型", font("Black", 118), GOLD2, stroke=3, stroke_fill=(120, 80, 10))
    x = badge(d, (62, 482), "全トレード公開", font("ExtraBold", 30), WHITE, (180, 50, 45))
    x = badge(d, (x + 26, 482), "負けも全部見せる", font("ExtraBold", 30), NAVY1, WHITE)
    text(d, (62, 548), "チャート画像16枚 × エントリー・損切り・利確のpips解説", font("Bold", 26), GRAY)
    # 右: 残高推移
    card = (790, 70, 1230, 560)
    panel(img, card)
    d = ImageDraw.Draw(img)
    text(d, (card[0] + 28, card[1] + 26), "口座残高の推移（バックテスト）", font("Bold", 24), WHITE)
    text(d, (card[0] + 28, card[1] + 64), "9年で 約2倍", font("Black", 52), GOLD2)
    text(d, (card[0] + 28, card[1] + 130), "最大の落ち込み −12.8%", font("Bold", 24), GRAY)
    equity_curve(img, (card[0] + 30, card[1] + 200, card[2] - 30, card[3] - 50), eq)
    footnote(d, w, h)
    img.save(path)


def x_post(eq, path):
    """有名手法と同じ条件で比べた PF（前半=設定を選んだ期間、後半=答え合わせ）"""
    w, h = 1200, 675
    img = background(w, h)
    d = ImageDraw.Draw(img)
    text(d, (w // 2, 50), "有名なFX手法と、同じ条件で比べてみた", font("Bold", 36), WHITE, anchor="ma")
    text(d, (w // 2, 100), "大事なのは「後半」の成績", font("Black", 58), GOLD2, anchor="ma")
    rows = [("ドル円4H 包み足の型", 2.54, 1.19, True), ("RSI(2)逆張り 日足", 1.06, 1.35, False),
            ("RSI(2)逆張り 4H", 1.02, 0.89, False), ("MAクロス 4H", 1.13, 0.94, False),
            ("ブレイクアウト 4H", 1.16, 0.91, False), ("MAクロス 日足", 1.45, 0.68, False),
            ("ブレイクアウト 日足", 1.62, 0.48, False)]
    x0, y0, step, scale = 60, 232, 52, 120            # scale: PF 1.0 あたりの横幅
    bx = x0 + 250
    one = bx + scale
    text(d, (x0, y0 - 46), "PF（1超えでプラス）", font("Bold", 20), GRAY)
    lx = badge(d, (bx + 40, y0 - 50), "前半 2012-17", font("Bold", 17), NAVY1, (120, 134, 160), pad=(10, 4), radius=6)
    badge(d, (lx + 24, y0 - 50), "後半 2018-22", font("Bold", 17), NAVY1, GOLD, pad=(10, 4), radius=6)
    for i, (name, tr, te, mine) in enumerate(rows):
        y = y0 + i * step
        text(d, (x0, y + 6), name, font("Bold", 21), WHITE if mine else GRAY)
        d.rectangle([bx, y + 2, bx + int(scale * min(tr, 2.6)), y + 18], fill=(120, 134, 160))
        d.rectangle([bx, y + 22, bx + int(scale * te), y + 40], fill=GOLD if te > 1 else (200, 120, 110))
        text(d, (bx + int(scale * min(tr, 2.6)) + 8, y + 10), f"{tr:.2f}", font("Bold", 16), GRAY, anchor="lm")
        text(d, (bx + int(scale * te) + 8, y + 31), f"{te:.2f}", font("Black", 19),
             GOLD2 if te > 1 else (230, 150, 140), anchor="lm")
    for yy in range(y0 - 4, y0 + step * len(rows) - 8, 12):
        d.line([(one, yy), (one, yy + 6)], fill=(255, 255, 255, 140), width=2)
    text(d, (one, y0 - 8), "1.0", font("Bold", 15), GRAY, anchor="md")
    text(d, (760, 214), "包み足の型：口座残高の推移", font("Bold", 22), WHITE)
    equity_curve(img, (770, 270, 1150, 560), eq)
    text(d, (w // 2, h - 38), "PFは損益ベース。包み足の型はドル円のみ、他の手法は12銘柄（FX11種＋ゴールド）に分散した成績。",
         font("Medium", 14), GRAY, anchor="md")
    footnote(d, w, h, 14)
    img.save(path)


def square(eq, path):
    w, h = 1080, 1080
    img = background(w, h)
    d = ImageDraw.Draw(img)
    badge(d, (70, 70), "Brainで公開中", font("ExtraBold", 32), NAVY1, GOLD)
    text(d, (70, 150), "ドル円4時間足", font("Black", 72), WHITE)
    text(d, (64, 232), "包み足の型", font("Black", 140), GOLD2, stroke=3, stroke_fill=(120, 80, 10))
    items = ["レンジ逆張り・順張り押し目の2つの型", "エントリー・損切り・利確をpipsで明示",
             "勝ち7例＋負け3例＋順張り6例のチャート", "「こんな時どうする？」Q&A 10項目",
             "9年分・全トレードの検証データ", "そのまま使えるEA（MT4/MT5）"]
    f = font("Bold", 34)
    for i, s in enumerate(items):
        y = 440 + i * 70
        d.ellipse([74, y + 8, 102, y + 36], fill=GOLD)
        text(d, (88, y + 22), "✓", font("Black", 22), NAVY1, anchor="mm")
        text(d, (124, y), s, f, WHITE)
    text(d, (w // 2, 900), "派手な約束はしません。数字で見せます。", font("Black", 40), GOLD2, anchor="ma")
    footnote(d, w, h, 14)
    img.save(path)


def main():
    eq = pd.read_csv(os.path.join(HERE, "equity_typeA_risk3.csv"), index_col=0, parse_dates=True).iloc[:, 0]
    out = os.path.join(HERE, "images")
    os.makedirs(out, exist_ok=True)
    thumbnail(eq, os.path.join(out, "thumbnail_1280x670.png"))
    x_post(eq, os.path.join(out, "x_post_1200x675.png"))
    square(eq, os.path.join(out, "square_1080x1080.png"))


if __name__ == "__main__":
    main()
