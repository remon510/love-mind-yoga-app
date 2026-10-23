//+------------------------------------------------------------------+
//| OutsideReversalEA.mq4                                            |
//| 高値更新アウトサイド陰線で売り／安値更新アウトサイド陽線で買い  |
//|                                                                  |
//| 売り: 確定足が直近Lookback本の高値を上抜け、陰線で引け、         |
//|       前の陽線を実体で包んだら次の足の始値で売り                 |
//| 買い: 上記の逆                                                   |
//| 損切り: パターン足の高値（買いは安値）± BufferPips              |
//| 利確  : 損切り幅 × RR                                            |
//+------------------------------------------------------------------+
#property strict

input int    Lookback      = 20;       // 直近何本の高値/安値を基準にするか
input double RR            = 2.0;      // 利確 = 損切り幅 × RR
input double BufferPips    = 2.0;      // 損切りをパターン足の外側に置く幅(pips)
input double RiskPercent   = 1.0;      // 1トレードの許容損失(残高の%) 0なら固定ロット
input double FixedLots     = 0.1;      // 固定ロット(RiskPercent=0のとき)
input double MaxSpreadPips = 3.0;      // これより広いスプレッドではエントリーしない
input int    SlippagePips  = 3;        // 許容スリッページ(pips)
input int    Magic         = 20261023; // マジックナンバー

datetime lastBarTime = 0;

double PipSize()
{
   return (Digits == 3 || Digits == 5) ? Point * 10 : Point;
}

// 1=買い -1=売り 0=なし（確定した1本前の足で判定）
int Signal()
{
   double o1 = Open[1], c1 = Close[1], o2 = Open[2], c2 = Close[2];
   bool engulf = MathMax(o1, c1) >= MathMax(o2, c2) && MathMin(o1, c1) <= MathMin(o2, c2)
                 && MathAbs(c1 - o1) > MathAbs(c2 - o2);
   if(!engulf) return 0;

   double hh = High[iHighest(NULL, 0, MODE_HIGH, Lookback, 2)];
   double ll = Low[iLowest(NULL, 0, MODE_LOW, Lookback, 2)];
   if(High[1] > hh && c1 < o1 && c2 > o2) return -1;
   if(Low[1]  < ll && c1 > o1 && c2 < o2) return 1;
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
   if(Lookback < 2 || RR <= 0) return INIT_PARAMETERS_INCORRECT;
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(Time[0] == lastBarTime) return;   // 新しい足の始まりでだけ判定
   if(Bars < Lookback + 3) return;
   lastBarTime = Time[0];

   if(HasPosition()) return;
   int sig = Signal();
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
      double tp = Bid - risk * RR;
      ticket = OrderSend(Symbol(), OP_SELL, CalcLots(risk), Bid, slippage,
                         NormalizeDouble(sl, Digits), NormalizeDouble(tp, Digits),
                         "OutsideReversal", Magic, 0, clrBlue);
   }
   else
   {
      double sl   = Low[1] - BufferPips * pip;
      double risk = Ask - sl;
      if(risk <= minStop) return;
      double tp = Ask + risk * RR;
      ticket = OrderSend(Symbol(), OP_BUY, CalcLots(risk), Ask, slippage,
                         NormalizeDouble(sl, Digits), NormalizeDouble(tp, Digits),
                         "OutsideReversal", Magic, 0, clrRed);
   }
   if(ticket < 0) Print("OrderSend failed: ", GetLastError());
}
