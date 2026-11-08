"""サーバー時刻（NY時刻＋7時間, GMT+2/+3）→ 日本時間"""
import pandas as pd


def to_jst(idx):
    idx = pd.DatetimeIndex(idx)
    ny = (idx - pd.Timedelta(hours=7)).tz_localize("America/New_York", ambiguous=True,
                                                    nonexistent="shift_forward")
    return ny.tz_convert("Asia/Tokyo").tz_localize(None)
