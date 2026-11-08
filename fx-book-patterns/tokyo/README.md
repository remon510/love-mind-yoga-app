# 東京ブレイク

ドル円15分足のデイトレ。東京時間（サーバー3:00〜9:59）の高値・安値を、10:00〜17:45の足の終値で抜けたら次の足で入る。
損切りは値幅の反対側、利確なし、サーバー23:00に決済。1日1回。サーバー時刻はGMT+2/+3。

| ファイル | 内容 |
|---|---|
| `trades.csv` | 全2,053トレード（スプレッド0.3pips） |
| `TokyoBreakEA.mq4` / `.mq5` | EA（MT4/MT5での動作確認はまだ） |
| `content.js` | 教材本文（../book/build_book.js で Word に組む） |
| `render_examples.py` | 実例チャート（日本時間表示） |
| `make_charts.py` | 残高推移・年別グラフ |
| `jst.py` | サーバー時刻→日本時間 |
| `figures/` | 画像 |

検証コードは `../research/daytrade.py`。trades.csv は次で作り直せる:
`simulate(df, "tokyo_break", "none", "far", 0, 0.3)`（df はドル円15分足に `add_htf_slope` をかけたもの）
