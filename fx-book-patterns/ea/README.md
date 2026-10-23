# OutsideReversal EA

高値更新アウトサイド陰線で売り／安値更新アウトサイド陽線で買い。

| ファイル | 内容 |
|---|---|
| `OutsideReversalEA.mq4` | MT4用（MQL4/Experts に置いてコンパイル） |
| `OutsideReversalEA.mq5` | MT5用（MQL5/Experts に置いてコンパイル） |
| `backtest.py` | 同じルールの Python バックテスト |
| `backtest_result_usdjpy.csv` | USDJPY 日足/4時間足/1時間足 × パラメータの結果 |
| `backtest_result_xauusd_m15.csv` | XAUUSD 15分足の結果（全設定マイナス） |
| `equity_usdjpy_h4.png` | USDJPY 4時間足の残高推移 |

## ルール
- エントリー: パターン確定の次の足の始値
- 損切り: パターン足の高値(売り)/安値(買い) ± 2pips
- 利確: 損切り幅 × RR（初期値 2.0）
- ポジションは同時に1つ、1回のリスクは残高の1%

## Pythonでの再実行
```
python backtest.py --csv USDJPYh4.csv --scale 1000
python backtest.py --csv XAUUSDm15.csv --scale 100 --pip 0.1 --spread 2.5   # ゴールド15分足（1pips=0.1ドル）
```
データ: https://github.com/ejtraderLabs/historical-data（2012/11〜2022/03、価格は1000倍で記録）
