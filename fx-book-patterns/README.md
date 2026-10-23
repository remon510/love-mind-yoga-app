# FX書籍用 チャートパターン画像抽出

検出するパターン
- **売り**: 直近20本の高値を上抜けたのに陰線で引け、前の陽線を実体で包む（陰の包み足）
- **買い**: 直近20本の安値を割ったのに陽線で引け、前の陰線を実体で包む（陽の包み足）

出力
- `images/` カラー版（陽線＝赤、陰線＝青）300dpi PNG
- `images_mono/` 白黒印刷用（陽線＝白、陰線＝黒）
- `list.csv` 各画像の日時・抜いた水準・その後10本の値動き

実行
```
pip install mplfinance backtesting pandas
python extract_patterns.py                    # 同梱サンプル EURUSD
python extract_patterns.py --csv USDJPY.csv --symbol USDJPY --tf raw   # 自分のCSV
python extract_patterns.py --mono --lookback 30
```

## ドル円 日足（2012/12〜2022/03）
- `images_usdjpy_d1/` カラー版、`images_usdjpy_d1_mono/` 白黒版（各21枚）
- データ: https://github.com/ejtraderLabs/historical-data の USDJPY/USDJPYd1.csv（価格が1000倍で記録されているため `--scale 1000`）
```
python extract_patterns.py --csv USDJPYd1.csv --scale 1000 --symbol USDJPY --tf D1 --max 200 --out images_usdjpy_d1
```
