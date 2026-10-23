//+------------------------------------------------------------------+
//| OutsideReversalEA.mq5                                            |
//| 高値更新アウトサイド陰線で売り／安値更新アウトサイド陽線で買い  |
//|                                                                  |
//| 売り: 確定足が直近Lookback本の高値を上抜け、陰線で引け、         |
//|       前の陽線を実体で包んだら次の足の始値で売り                 |
//| 買い: 上記の逆                                                   |
//| 損切り: パターン足の高値（買いは安値）± BufferPips              |
//| 利確  : 損切り幅 × RR                                            |
//+------------------------------------------------------------------+
#include <Trade/Trade.mqh>

input int    Lookback      = 20;       // 直近何本の高値/安値を基準にするか
input double RR            = 2.0;      // 利確 = 損切り幅 × RR
input double BufferPips    = 2.0;      // 損切りをパターン足の外側に置く幅(pips)
input double RiskPercent   = 1.0;      // 1トレードの許容損失(残高の%) 0なら固定ロット
input double FixedLots     = 0.1;      // 固定ロット(RiskPercent=0のとき)
input double MaxSpreadPips = 3.0;      // これより広いスプレッドではエントリーしない
input int    SlippagePips  = 3;        // 許容スリッページ(pips)
input ulong  Magic         = 20261023; // マジックナンバー

CTrade   trade;
datetime lastBarTime = 0;

double PipSize()
{
   return (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
}

// 1=買い -1=売り 0=なし（確定した1本前の足で判定）
int Signal(const MqlRates &r[])
{
   double o1 = r[1].open, c1 = r[1].close, o2 = r[2].open, c2 = r[2].close;
   bool engulf = MathMax(o1, c1) >= MathMax(o2, c2) && MathMin(o1, c1) <= MathMin(o2, c2)
                 && MathAbs(c1 - o1) > MathAbs(c2 - o2);
   if(!engulf) return 0;

   double hh = r[2].high, ll = r[2].low;
   for(int k = 3; k <= Lookback + 1; k++)
   {
      hh = MathMax(hh, r[k].high);
      ll = MathMin(ll, r[k].low);
   }
   if(r[1].high > hh && c1 < o1 && c2 > o2) return -1;
   if(r[1].low  < ll && c1 > o1 && c2 < o2) return 1;
   return 0;
}

bool HasPosition()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol
         && (ulong)PositionGetInteger(POSITION_MAGIC) == Magic)
         return true;
   }
   return false;
}

double NormalizeLots(double lots)
{
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double mn   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double mx   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   lots = MathFloor(lots / step) * step;
   return MathMax(mn, MathMin(mx, lots));
}

double CalcLots(double slDistance)
{
   if(RiskPercent <= 0) return NormalizeLots(FixedLots);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickValue <= 0 || tickSize <= 0) return NormalizeLots(FixedLots);
   double riskMoney = AccountInfoDouble(ACCOUNT_BALANCE) * RiskPercent / 100.0;
   return NormalizeLots(riskMoney / (slDistance / tickSize * tickValue));
}

int OnInit()
{
   if(Lookback < 2 || RR <= 0) return INIT_PARAMETERS_INCORRECT;
   trade.SetExpertMagicNumber(Magic);
   trade.SetDeviationInPoints((ulong)(SlippagePips * PipSize() / _Point));
   return INIT_SUCCEEDED;
}

void OnTick()
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   if(CopyRates(_Symbol, _Period, 0, Lookback + 3, r) < Lookback + 3) return;
   if(r[0].time == lastBarTime) return;   // 新しい足の始まりでだけ判定
   lastBarTime = r[0].time;

   if(HasPosition()) return;
   int sig = Signal(r);
   if(sig == 0) return;

   double pip = PipSize();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask - bid > MaxSpreadPips * pip) return;

   double minStop = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;

   if(sig < 0)
   {
      double sl   = r[1].high + BufferPips * pip;
      double risk = sl - bid;
      if(risk <= minStop) return;
      double tp = bid - risk * RR;
      if(!trade.Sell(CalcLots(risk), _Symbol, 0, NormalizeDouble(sl, _Digits),
                     NormalizeDouble(tp, _Digits), "OutsideReversal"))
         Print("Sell failed: ", trade.ResultRetcode());
   }
   else
   {
      double sl   = r[1].low - BufferPips * pip;
      double risk = ask - sl;
      if(risk <= minStop) return;
      double tp = ask + risk * RR;
      if(!trade.Buy(CalcLots(risk), _Symbol, 0, NormalizeDouble(sl, _Digits),
                    NormalizeDouble(tp, _Digits), "OutsideReversal"))
         Print("Buy failed: ", trade.ResultRetcode());
   }
}
