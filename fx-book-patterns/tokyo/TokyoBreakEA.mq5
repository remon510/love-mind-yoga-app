//+------------------------------------------------------------------+
//| TokyoBreakEA.mq5                                                 |
//| 東京ブレイク：東京時間の高値・安値を、ロンドン以降に15分足の      |
//| 終値で抜けたら、抜けた方向へ1日1回だけエントリー                 |
//|                                                                  |
//| 時刻はすべてサーバー時刻。初期値は GMT+2/+3（NYクローズ=0時）    |
//| の業者向け。それ以外の業者は時刻の設定を必ず合わせること         |
//|   東京の値幅   : RangeStartHour 〜 RangeEndHour の前まで          |
//|   エントリー   : RangeEndHour 〜 EntryEndHour の前までに確定した  |
//|                  15分足の終値が値幅を抜けたら、次の足の始値で      |
//|   損切り       : 値幅の反対側                                    |
//|   決済         : ExitHour になったら必ず決済（利確の指値なし）    |
//+------------------------------------------------------------------+
#include <Trade/Trade.mqh>

input double PipSizeOverride = 0.0;    // 1pipsの価格幅 0なら自動
input int    RangeStartHour  = 3;      // 東京の値幅を測り始める時（サーバー時刻）
input int    RangeEndHour    = 10;     // 東京の値幅を測り終える時（この時の前まで）
input int    EntryEndHour    = 18;     // この時の前までに確定した足のブレイクだけ入る
input int    ExitHour        = 23;     // この時になったら必ず決済
input double RiskPercent     = 1.0;    // 1トレードの許容損失(残高の%) 0なら固定ロット
input double FixedLots       = 0.1;    // 固定ロット(RiskPercent=0のとき)
input double MaxSpreadPips   = 2.0;    // これより広いスプレッドではエントリーしない
input int    SlippagePips    = 3;      // 許容スリッページ(pips)
input ulong  Magic           = 20261108; // マジックナンバー

CTrade   trade;
datetime lastBarTime = 0;
int      doneDay     = -1;             // ブレイクを判定済みの日（1日1回）

double PipSize()
{
   if(PipSizeOverride > 0) return PipSizeOverride;
   if(StringFind(_Symbol, "XAU") >= 0 || StringFind(_Symbol, "GOLD") >= 0) return 0.1;
   return (_Digits == 3 || _Digits == 5) ? _Point * 10 : _Point;
}

int DayKey(datetime t)
{
   MqlDateTime s;
   TimeToStruct(t, s);
   return s.year * 1000 + s.day_of_year;
}

int HourOf(datetime t)
{
   MqlDateTime s;
   TimeToStruct(t, s);
   return s.hour;
}

// 今日の東京の値幅（足がそろっていなければ false）。r は新しい順
bool TokyoRange(const MqlRates &r[], int count, double &hi, double &lo)
{
   hi = -1; lo = DBL_MAX;
   int n = 0, today = DayKey(r[0].time);
   for(int i = 1; i < count; i++)
   {
      if(DayKey(r[i].time) != today) break;
      int h = HourOf(r[i].time);
      if(h >= RangeStartHour && h < RangeEndHour)
      {
         hi = MathMax(hi, r[i].high);
         lo = MathMin(lo, r[i].low);
         n++;
      }
   }
   return n >= (RangeEndHour - RangeStartHour) * 4 - 1 && hi > lo;
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

// 前の日から持ち越しているポジションがあるか（決済時刻に足が来なかった場合の保険）
bool OpenedBefore(int today)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0 && PositionGetString(POSITION_SYMBOL) == _Symbol
         && (ulong)PositionGetInteger(POSITION_MAGIC) == Magic
         && DayKey((datetime)PositionGetInteger(POSITION_TIME)) != today)
         return true;
   }
   return false;
}

void CloseAll()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0 || PositionGetString(POSITION_SYMBOL) != _Symbol
         || (ulong)PositionGetInteger(POSITION_MAGIC) != Magic)
         continue;
      if(!trade.PositionClose(ticket))
         Print("PositionClose failed: ", trade.ResultRetcode());
   }
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
   if(RangeStartHour < 0 || RangeEndHour <= RangeStartHour || EntryEndHour <= RangeEndHour
      || ExitHour <= EntryEndHour || ExitHour > 23)
      return INIT_PARAMETERS_INCORRECT;
   trade.SetExpertMagicNumber(Magic);
   trade.SetDeviationInPoints((ulong)(SlippagePips * PipSize() / _Point));
   return INIT_SUCCEEDED;
}

void OnTick()
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   int count = CopyRates(_Symbol, PERIOD_M15, 0, 120, r);
   if(count < 3) return;
   if(r[0].time == lastBarTime) return;            // 15分足の始まりでだけ判定
   lastBarTime = r[0].time;

   if(HourOf(r[0].time) >= ExitHour || OpenedBefore(DayKey(r[0].time))) { CloseAll(); return; }
   if(HasPosition() || doneDay == DayKey(r[0].time)) return;

   int sh = HourOf(r[1].time);                      // 確定した1本前の足
   if(DayKey(r[1].time) != DayKey(r[0].time) || sh < RangeEndHour || sh >= EntryEndHour) return;

   double hi, lo;
   if(!TokyoRange(r, count, hi, lo)) { doneDay = DayKey(r[0].time); return; }
   double c = r[1].close;
   int side = c > hi ? 1 : (c < lo ? -1 : 0);
   if(side == 0) return;
   doneDay = DayKey(r[0].time);                     // その日の最初のブレイクだけ使う

   double pip = PipSize();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(ask - bid > MaxSpreadPips * pip) return;
   double minStop = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   if(side > 0)
   {
      double risk = ask - lo;
      if(risk <= minStop || risk <= ask - bid) return;
      if(!trade.Buy(CalcLots(risk), _Symbol, 0, NormalizeDouble(lo, _Digits), 0, "TokyoBreak"))
         Print("Buy failed: ", trade.ResultRetcode());
   }
   else
   {
      double risk = hi - bid;
      if(risk <= minStop || risk <= ask - bid) return;
      if(!trade.Sell(CalcLots(risk), _Symbol, 0, NormalizeDouble(hi, _Digits), 0, "TokyoBreak"))
         Print("Sell failed: ", trade.ResultRetcode());
   }
}
