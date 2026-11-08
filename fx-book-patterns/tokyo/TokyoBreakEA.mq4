//+------------------------------------------------------------------+
//| TokyoBreakEA.mq4                                                 |
//| 東京ブレイク：東京時間の高値・安値を、ロンドン以降に15分足の      |
//| 終値で抜けたら、抜けた方向へ1日1回だけエントリー                 |
//|                                                                  |
//| 時刻はすべてサーバー時刻。初期値は GMT+2/+3（NYクローズ=0時）    |
//| の業者向け。それ以外の業者は時刻の設定を必ず合わせること         |
//|   東京の値幅   : RangeStartHour 〜 RangeEndHour の前まで          |
//|   エントリー   : RangeEndHour 〜 EntryEndHour の前までに確定した  |
//|                  15分足の終値が値幅を抜けたら、次の足の始値で      |
//|   損切り       : 値幅の反対側                                    |
//|   利確         : TakeProfitRangeX>0 なら、ブレイクした側の端から  |
//|                  東京の値幅×TakeProfitRangeX で利確（0なら利確なし）|
//|   決済         : ExitHour になったら必ず決済                      |
//+------------------------------------------------------------------+
#property strict

input double PipSizeOverride = 0.0;    // 1pipsの価格幅 0なら自動
input int    RangeStartHour  = 3;      // 東京の値幅を測り始める時（サーバー時刻）
input int    RangeEndHour    = 10;     // 東京の値幅を測り終える時（この時の前まで）
input int    EntryEndHour    = 18;     // この時の前までに確定した足のブレイクだけ入る
input int    ExitHour        = 23;     // この時になったら必ず決済
input double TakeProfitRangeX = 0.0;   // 利確: 東京の値幅の何倍か（ブレイクした側の端から）0なら利確なし
input double RiskPercent     = 1.0;    // 1トレードの許容損失(残高の%) 0なら固定ロット
input double FixedLots       = 0.1;    // 固定ロット(RiskPercent=0のとき)
input double MaxSpreadPips   = 2.0;    // これより広いスプレッドではエントリーしない
input int    SlippagePips    = 3;      // 許容スリッページ(pips)
input int    Magic           = 20261108; // マジックナンバー

datetime lastBarTime = 0;
int      doneDay     = -1;             // ブレイクを判定済みの日（1日1回）

double PipSize()
{
   if(PipSizeOverride > 0) return PipSizeOverride;
   if(StringFind(Symbol(), "XAU") >= 0 || StringFind(Symbol(), "GOLD") >= 0) return 0.1;
   return (Digits == 3 || Digits == 5) ? Point * 10 : Point;
}

int DayKey(datetime t) { return TimeYear(t) * 1000 + TimeDayOfYear(t); }

// 今日の東京の値幅（足がそろっていなければ false）
bool TokyoRange(datetime now, double &hi, double &lo)
{
   hi = -1; lo = DBL_MAX;
   int n = 0, today = DayKey(now);
   for(int i = 1; i < 200; i++)
   {
      datetime t = iTime(NULL, PERIOD_M15, i);
      if(t == 0 || DayKey(t) != today) break;
      int h = TimeHour(t);
      if(h >= RangeStartHour && h < RangeEndHour)
      {
         hi = MathMax(hi, iHigh(NULL, PERIOD_M15, i));
         lo = MathMin(lo, iLow(NULL, PERIOD_M15, i));
         n++;
      }
   }
   return n >= (RangeEndHour - RangeStartHour) * 4 - 1 && hi > lo;
}

bool HasPosition()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)
         && OrderSymbol() == Symbol() && OrderMagicNumber() == Magic)
         return true;
   return false;
}

// 前の日から持ち越しているポジションがあるか（決済時刻に足が来なかった場合の保険）
bool OpenedBefore(int today)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES) && OrderSymbol() == Symbol()
         && OrderMagicNumber() == Magic && DayKey(OrderOpenTime()) != today)
         return true;
   return false;
}

void CloseAll()
{
   int slippage = (int)(SlippagePips * PipSize() / Point);
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != Magic) continue;
      double price = OrderType() == OP_BUY ? Bid : Ask;
      if(!OrderClose(OrderTicket(), OrderLots(), price, slippage, clrGray))
         Print("OrderClose failed: ", GetLastError());
   }
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
   if(TakeProfitRangeX < 0 || RangeStartHour < 0 || RangeEndHour <= RangeStartHour || EntryEndHour <= RangeEndHour
      || ExitHour <= EntryEndHour || ExitHour > 23)
      return INIT_PARAMETERS_INCORRECT;
   return INIT_SUCCEEDED;
}

void OnTick()
{
   datetime bar = iTime(NULL, PERIOD_M15, 0);
   if(bar == 0 || bar == lastBarTime) return;      // 15分足の始まりでだけ判定
   lastBarTime = bar;

   if(TimeHour(bar) >= ExitHour || OpenedBefore(DayKey(bar))) { CloseAll(); return; }
   if(HasPosition() || doneDay == DayKey(bar)) return;

   datetime sig = iTime(NULL, PERIOD_M15, 1);       // 確定した1本前の足
   int sh = TimeHour(sig);
   if(DayKey(sig) != DayKey(bar) || sh < RangeEndHour || sh >= EntryEndHour) return;

   double hi, lo;
   if(!TokyoRange(bar, hi, lo)) { doneDay = DayKey(bar); return; }
   double c = iClose(NULL, PERIOD_M15, 1);
   int side = c > hi ? 1 : (c < lo ? -1 : 0);
   if(side == 0) return;
   doneDay = DayKey(bar);                           // その日の最初のブレイクだけ使う

   double pip = PipSize();
   if(Ask - Bid > MaxSpreadPips * pip) return;
   double minStop = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   int slippage = (int)(SlippagePips * pip / Point);
   int ticket = -1;
   if(side > 0)
   {
      double risk = Ask - lo;
      if(risk <= minStop || risk <= Ask - Bid) return;
      double tp = TakeProfitRangeX > 0 ? hi + (hi - lo) * TakeProfitRangeX : 0;
      if(tp > 0 && tp - Ask <= minStop) tp = 0;    // すでに目標を超えているときは利確なし
      ticket = OrderSend(Symbol(), OP_BUY, CalcLots(risk), Ask, slippage,
                         NormalizeDouble(lo, Digits), NormalizeDouble(tp, Digits), "TokyoBreak", Magic, 0, clrRed);
   }
   else
   {
      double risk = hi - Bid;
      if(risk <= minStop || risk <= Ask - Bid) return;
      double tp = TakeProfitRangeX > 0 ? lo - (hi - lo) * TakeProfitRangeX : 0;
      if(tp > 0 && Bid - tp <= minStop) tp = 0;    // すでに目標を超えているときは利確なし
      ticket = OrderSend(Symbol(), OP_SELL, CalcLots(risk), Bid, slippage,
                         NormalizeDouble(hi, Digits), NormalizeDouble(tp, Digits), "TokyoBreak", Magic, 0, clrBlue);
   }
   if(ticket < 0) Print("OrderSend failed: ", GetLastError());
}
