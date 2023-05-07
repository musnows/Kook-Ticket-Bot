from datetime import datetime,timezone,timedelta

def GetTime():
    """获取当前时间，格式为 `23-01-01 00:00:00`"""    
    utc_dt = datetime.now(timezone.utc) # 获取当前时间
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8))) # 转换为北京时间
    return bj_dt.strftime('%y-%m-%d %H:%M:%S')
    # use time.loacltime if you aren't using BeiJing Time
    # return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

def GetTimeStamp():
    """获取当前时间戳（北京时间）"""    
    utc_dt = datetime.now(timezone.utc) # 获取当前时间
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8))) # 转换为北京时间
    return bj_dt.timestamp()

def GetTimeStampFromStr(time_str:str):
    """从可读时间转为时间戳,格式 23-01-01 00:00:00
    - 如果传入的只有日期，如23-01-01，则会自动获取当日0点的时间戳
    """
    if len(time_str) == 8:
        time_str+=" 00:00:00"
    dt = datetime.strptime(time_str, '%y-%m-%d %H:%M:%S')
    tz = timezone(timedelta(hours=8))
    dt = dt.astimezone(tz)
    return dt.timestamp()

import time
print(GetTimeStamp())
print(time.time())