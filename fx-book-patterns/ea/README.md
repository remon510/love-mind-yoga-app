# OutsideReversal EA

高値更新アウトサイド陰線で売り／安値更新アウトサイド陽線で買い。

| ファイル | 内容 |
|---|---|
| `OutsideReversalEA.mq4` | MT4用（MQL4/Experts に置いてコンパイル） |
| `OutsideReversalEA.mq5` | MT5用（MQL5/Experts に置いてコンパイル） |
| `RegimeSwitchEA.mq4` / `.mq5` | MA100の傾きでレンジ手法／トレンド手法を切り替える版 |
| `backtest.py` | 同じルールの Python バックテスト |
| `backtest_result_usdjpy.csv` | USDJPY 日足/4時間足/1時間足 × パラメータの結果 |
| `backtest_result_xauusd_m15.csv` | XAUUSD 15分足の結果（全設定マイナス） |
| `equity_usdjpy_h4.png` | USDJPY 4時間足の残高推移 |
| `backtest_result_ma_flat.csv` | 「MA横ばい時のみ」フィルターの検証（2012-17 / 2018-22 に分割） |
| `backtest_result_m5_m1.csv` | XAUUSD/USDJPY 5分足・1分足（2026/03〜09、前半/後半に分割） |
| `backtest_result_lb10_rr1.csv` | 直近10本・損益1対1 で全データを検証 |
| `backtest_result_regime_switch.csv` | 切り替えロジックの検証（USDJPY・4時間足12銘柄・日足6銘柄） |
| `backtest_result_usdjpy_m15_aligned.csv` | USDJPY 15分足の型A（4時間足の向きに合わせたサインのみ）の検証 |
| `equity_usdjpy_h4_ma_flat.png` | USDJPY 4時間足 フィルターあり/なしの残高推移 |

## ルール
- エントリー: パターン確定の次の足の始値
- 損切り: パターン足の高値(売り)/安値(買い) ± 2pips
- 利確: 損切り幅 × RR（初期値 2.0）
- ポジションは同時に1つ、1回のリスクは残高の1%
- （任意）MAPeriod>0 で「MAが横ばいの時だけ」エントリー
  横ばい = |MA(確定足) − MA(MASlopeBars本前)| ÷ 直近14本の平均値幅(高値−安値) < FlatATR

## Pythonでの再実行
```
python backtest.py --csv USDJPYh4.csv --scale 1000
python backtest.py --csv XAUUSDm15.csv --scale 100 --pip 0.1 --spread 2.5   # ゴールド15分足（1pips=0.1ドル）
```
データ: https://github.com/ejtraderLabs/historical-data（2012/11〜2022/03、価格は1000倍で記録）

5分足・1分足のデータ: https://github.com/getdata-finance （xauusd-5m/1m-ohlcv-metals-historical-data, usdjpy-5m/1m-ohlcv-forex-historical-data の無料サンプル）
