//+------------------------------------------------------------------+
//| RegimeSwitchEA.mq4                                               |
//| MA100の傾きで相場を判定して手法を切り替える                      |
//|                                                                  |
//| 傾き = (MA[1] - MA[1+MASlopeBars]) ÷ 直近14本の平均値幅          |
//|  |傾き| < FlatATR : レンジ → 高値更新アウトサイド陰線で売り       |
//|                           安値更新アウトサイド陽線で買い         |
//|  傾き >= TrendATR : 上昇トレンド → MA20まで押した陽の包み足が    |
//|                     MA20より上で引けたら買い                     |
//|  傾き <= -TrendATR: 下降トレンド → 上記の逆で売り                |
//|  その間           : 何もしない                                   |
//| 損切り: パターン足の高値（買いは安値）± BufferPips              |
//| 利確  : 損切り幅 × RangeRR / TrendRR                             |
//+------------------------------------------------------------------+
#property strict

input double PipSizeOverride = 0.0;    // 1pipsの価格幅 0なら自動(FX:0.01/0.0001, ゴールド:0.1)
input int    MAPeriod      = 100;      // 相場判定用MAの期間
input int    MASlopeBars   = 10;       // MAの傾きを測る本数
input double FlatATR       = 0.5;      // 傾きがこれ未満ならレンジ
input double TrendATR      = 1.0;      // 傾きがこれ以上ならトレンド
input bool   UseRange      = true;     // レンジ手法を使う
input bool   UseTrend      = true;     // トレンド手法を使う
input int    Lookback      = 20;       // レンジ手法: 直近何本の高値/安値を基準にするか
input int    FastMAPeriod  = 20;       // トレンド手法: 押し目/戻りを測るMAの期間
input double RangeRR       = 2.0;      // レンジ手法の利確 = 損切り幅 × RangeRR
input double TrendRR       = 2.0;      // トレンド手法の利確 = 損切り幅 × TrendRR
input double BufferPips    = 2.0;      // 損切りをパターン足の外側に置く幅(pips)
input double RiskPercent   = 1.0;      // 1トレードの許容損失(残高の%) 0なら固定ロット
input double FixedLots     = 0.1;      // 固定ロット(RiskPercent=0のとき)
input double MaxSpreadPips = 3.0;      // これより広いスプレッドではエントリーしない
input int    SlippagePips  = 3;        // 許容スリッページ(pips)
input int    Magic         = 20261024; // マジックナンバー

datetime lastBarTime = 0;

double PipSize()
{
   if(PipSizeOverride > 0) return PipSizeOverride;
   if(StringFind(Symbol(), "XAU") >= 0 || StringFind(Symbol(), "GOLD") >= 0) return 0.1;
   return (Digits == 3 || Digits == 5) ? Point * 10 : Point;
}

double SMA(int period, int shift)
{
   double sum = 0;
   for(int k = 0; k < period; k++) sum += Close[shift + k];
   return sum / period;
}

// 1=買い -1=売り 0=なし（確定した1本前の足で判定）。rrに使うRRを返す
int Signal(double &rr)
{
   double o1 = Open[1], c1 = Close[1], o2 = Open[2], c2 = Close[2];
   bool engulf = MathMax(o1, c1) >= MathMax(o2, c2) && MathMin(o1, c1) <= MathMin(o2, c2)
                 && MathAbs(c1 - o1) > MathAbs(c2 - o2);
   if(!engulf) return 0;
   bool bull = c1 > o1 && c2 < o2;
   bool bear = c1 < o1 && c2 > o2;

   double range = 0;
   for(int k = 1; k <= 14; k++) range += High[k] - Low[k];
   range /= 14;
   if(range <= 0) return 0;
   double slope = (SMA(MAPeriod, 1) - SMA(MAPeriod, 1 + MASlopeBars)) / range;

   if(MathAbs(slope) < FlatATR)
   {
      if(!UseRange) return 0;
      rr = RangeRR;
      double hh = High[iHighest(NULL, 0, MODE_HIGH, Lookback, 2)];
      double ll = Low[iLowest(NULL, 0, MODE_LOW, Lookback, 2)];
      if(bear && High[1] > hh) return -1;
      if(bull && Low[1]  < ll) return 1;
      return 0;
   }
   if(!UseTrend) return 0;
   rr = TrendRR;
   double f = SMA(FastMAPeriod, 1);
   if(slope >=  TrendATR && bull && Low[1]  <= f && f < c1) return 1;
   if(slope <= -TrendATR && bear && High[1] >= f && f > c1) return -1;
   return 0;
}

bool HasPosition()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)
         && OrderSymbol() == Symbol() && OrderMagicNumber() == Magic)
         return true;
   return false;
}

double NormalizeLots(double lots)
{
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);
   double mn   = MarketInfo(Symbol(), MODE_MINLOT);
   double mx   = MarketInfo(Symbol(), MODE_MAXLOT);
   lots = MathFloor(lots / step) * step;
   return MathMax(mn, MathMin(mx, lots));
}

double CalcLots(double slDistance)
{
   if(RiskPercent <= 0) return NormalizeLots(FixedLots);
   double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
   double tickSize  = MarketInfo(Symbol(), MODE_TICKSIZE);
   if(tickValue <= 0 || tickSize <= 0) return NormalizeLots(FixedLots);
   double riskMoney = AccountBalance() * RiskPercent / 100.0;
   return NormalizeLots(riskMoney / (slDistance / tickSize * tickValue));
}

int OnInit()
{
   if(Lookback < 2 || MAPeriod < 2 || FastMAPeriod < 2 || RangeRR <= 0 || TrendRR <= 0
      || FlatATR > TrendATR)
      return INIT_PARAMETERS_INCORRECT;
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(Time[0] == lastBarTime) return;   // 新しい足の始まりでだけ判定
   if(Bars < MathMax(Lookback, MAPeriod + MASlopeBars) + 16) return;
   lastBarTime = Time[0];

   if(HasPosition()) return;
   double rr = 0;
   int sig = Signal(rr);
   if(sig == 0) return;

   double pip = PipSize();
   if(Ask - Bid > MaxSpreadPips * pip) return;

   double minStop = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   int slippage = (int)(SlippagePips * pip / Point);
   int ticket = -1;

   if(sig < 0)
   {
      double sl   = High[1] + BufferPips * pip;
      double risk = sl - Bid;
      if(risk <= minStop) return;
      double tp = Bid - risk * rr;
      ticket = OrderSend(Symbol(), OP_SELL, CalcLots(risk), Bid, slippage,
                         NormalizeDouble(sl, Digits), NormalizeDouble(tp, Digits),
                         "RegimeSwitch", Magic, 0, clrBlue);
   }
   else
   {
      double sl   = Low[1] - BufferPips * pip;
      double risk = Ask - sl;
      if(risk <= minStop) return;
      double tp = Ask + risk * rr;
      ticket = OrderSend(Symbol(), OP_BUY, CalcLots(risk), Ask, slippage,
                         NormalizeDouble(sl, Digits), NormalizeDouble(tp, Digits),
                         "RegimeSwitch", Magic, 0, clrRed);
   }
   if(ticket < 0) Print("OrderSend failed: ", GetLastError());
}
