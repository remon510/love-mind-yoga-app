# Brain 販売用素材

| ファイル | 使い道 |
|---|---|
| `images/thumbnail_1280x670.png` | Brain の商品サムネイル（1280×670px） |
| `images/x_post_1200x675.png` | X 告知用（有名手法との比較グラフ） |
| `images/square_1080x1080.png` | X・Instagram 告知用（中身の一覧） |
| `sales_page.md` | 販売ページの無料部分（タイトル案・セールス文・FAQ・免責） |
| `paid_content.md` | 有料部分（書籍原稿をBrain用に整えたもの。画像は ../book/figures/） |
| `x_posts.md` | X 告知文 5パターン |
| `make_ads.py` | 広告画像を作るスクリプト（`python make_ads.py <フォントフォルダ>`） |
| `equity_typeA_risk3.csv` | 画像に使った残高推移（型A・リスク3%） |

フォント: M PLUS 1p（https://github.com/google/fonts/tree/main/ofl/mplus1p）の Black / ExtraBold / Bold / Medium

## 東京ブレイク

| ファイル | 使い道 |
|---|---|
| `images/tokyo_thumbnail_1280x670.png` | Brain の商品サムネイル |
| `images/tokyo_x_post_1200x675.png` | X 告知用（年別成績） |
| `images/tokyo_square_1080x1080.png` | X・Instagram 告知用（中身の一覧） |
| `tokyo_sales_page.md` | 販売ページの無料部分 |
| `tokyo_paid_content.md` | 有料部分（画像は ../tokyo/figures/） |
| `tokyo_x_posts.md` | X 告知文 5パターン |
| `make_ads_tokyo.py` | 広告画像を作るスクリプト |

教材本文の元データは `../tokyo/content.js`。Word・Markdown は `../book/` で
`node build_book.js ../tokyo/content.js 東京ブレイク_教材` / `node export_markdown.js ../tokyo/content.js 東京ブレイク_教材`
