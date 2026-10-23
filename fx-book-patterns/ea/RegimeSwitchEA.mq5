//+------------------------------------------------------------------+
//| RegimeSwitchEA.mq5                                               |
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
#include <Trade/Trade.mqh>

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
input ulong  Magic         = 20261024; // マジックナンバー

CTrade   trade;
datetime lastBarTime = 0;

double PipSize()
{
   if(PipSizeOverride > 0) return PipSizeOverride;
   if(StringFind(_Symbol, "XAU") >= 0 || StringFind(_Symbol, "GOLD") >= 0) return 0.1;
   return (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
}

double SMA(const MqlRates &r[], int period, int shift)
{
   double sum = 0;
   for(int k = 0; k < period; k++) sum += r[shift + k].close;
   return sum / period;
}

// 1=買い -1=売り 0=なし（確定した1本前の足で判定）。rrに使うRRを返す
int Signal(const MqlRates &r[], double &rr)
{
   double o1 = r[1].open, c1 = r[1].close, o2 = r[2].open, c2 = r[2].close;
   bool engulf = MathMax(o1, c1) >= MathMax(o2, c2) && MathMin(o1, c1) <= MathMin(o2, c2)
                 && MathAbs(c1 - o1) > MathAbs(c2 - o2);
   if(!engulf) return 0;
   bool bull = c1 > o1 && c2 < o2;
   bool bear = c1 < o1 && c2 > o2;

   double range = 0;
   for(int k = 1; k <= 14; k++) range += r[k].high - r[k].low;
   range /= 14;
   if(range <= 0) return 0;
   double slope = (SMA(r, MAPeriod, 1) - SMA(r, MAPeriod, 1 + MASlopeBars)) / range;

   if(MathAbs(slope) < FlatATR)
   {
      if(!UseRange) return 0;
      rr = RangeRR;
      double hh = r[2].high, ll = r[2].low;
      for(int k = 3; k <= Lookback + 1; k++)
      {
         hh = MathMax(hh, r[k].high);
         ll = MathMin(ll, r[k].low);
      }
      if(bear && r[1].high > hh) return -1;
      if(bull && r[1].low  < ll) return 1;
      return 0;
   }
   if(!UseTrend) return 0;
   rr = TrendRR;
   double f = SMA(r, FastMAPeriod, 1);
   if(slope >=  TrendATR && bull && r[1].low  <= f && f < c1) return 1;
   if(slope <= -TrendATR && bear && r[1].high >= f && f > c1) return -1;
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
   if(Lookback < 2 || MAPeriod < 2 || FastMAPeriod < 2 || RangeRR <= 0 || TrendRR <= 0
      || FlatATR > TrendATR)
      return INIT_PARAMETERS_INCORRECT;
   trade.SetExpertMagicNumber(Magic);
   trade.SetDeviationInPoints((ulong)(SlippagePips * PipSize() / _Point));
   return INIT_SUCCEEDED;
}

void OnTick()
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   int need = MathMax(MathMax(Lookback + 3, MAPeriod + MASlopeBars + 2), MathMax(FastMAPeriod + 2, 16));
   if(CopyRates(_Symbol, _Period, 0, need, r) < need) return;
   if(r[0].time == lastBarTime) return;   // 新しい足の始まりでだけ判定
   lastBarTime = r[0].time;

   if(HasPosition()) return;
   double rr = 0;
   int sig = Signal(r, rr);
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
      double tp = bid - risk * rr;
      if(!trade.Sell(CalcLots(risk), _Symbol, 0, NormalizeDouble(sl, _Digits),
                     NormalizeDouble(tp, _Digits), "RegimeSwitch"))
         Print("Sell failed: ", trade.ResultRetcode());
   }
   else
   {
      double sl   = r[1].low - BufferPips * pip;
      double risk = ask - sl;
      if(risk <= minStop) return;
      double tp = ask + risk * rr;
      if(!trade.Buy(CalcLots(risk), _Symbol, 0, NormalizeDouble(sl, _Digits),
                    NormalizeDouble(tp, _Digits), "RegimeSwitch"))
         Print("Buy failed: ", trade.ResultRetcode());
   }
}
