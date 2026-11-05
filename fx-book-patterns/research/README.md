# 手法探索（12銘柄ポートフォリオ）

研究で効果が報告されている型だけを候補にし、**2013〜2017年で設定を選び、2018〜2022年で答え合わせ**した。

| ファイル | 内容 |
|---|---|
| `strategies.py` | 候補の売買ルール（ドンチャン・ブレイクアウト、MAクロス、RSI(2)逆張り） |
| `search.py` | 12銘柄に同額を割り当てた運用で、学習期間→検証期間の成績を出す |
| `search_result_d1.csv` / `search_result_h4.csv` | 各手法で学習期間に最も良かった設定の、検証期間の成績 |
| `search_train_grid_*.csv` | 学習期間の全設定の成績 |

```
python search.py <データフォルダ> d1
python search.py <データフォルダ> h4
```

対象: USDJPY EURUSD GBPUSD AUDUSD USDCAD USDCHF EURGBP EURCHF EURJPY GBPJPY AUDJPY XAUUSD
データ: https://github.com/ejtraderLabs/historical-data
