from datetime import datetime,timezone,timedelta
import logging # 采用logging来替换所有print

LOGGER_NAME = "bot-log"
LOGGER_FILE = "bot.log" # 如果想修改log文件的名字和路径，修改此变量

def beijing(sec, what):
    utc_dt = datetime.now(timezone.utc) # 获取当前时间
    beijing_time = utc_dt.astimezone(timezone(timedelta(hours=8))) # 转换为北京时间
    return beijing_time.timetuple()
# 日志时间改为北京时间
logging.Formatter.converter = beijing # type:ignore

# 只打印info以上的日志（debug低于info）
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(levelname)s:%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%y-%m-%d %H:%M:%S")
# 获取一个logger对象
_log = logging.getLogger(LOGGER_NAME)
"""自定义的logger对象"""
# 实例化控制台handler和文件handler，同时输出到控制台和文件
# cmd_handler = logging.StreamHandler() # 默认设置里面，就会往控制台打印信息;自己又加一个，导致打印俩次
file_handler = logging.FileHandler(LOGGER_FILE, mode="a", encoding="utf-8")
fmt = logging.Formatter(fmt="[%(asctime)s] %(levelname)s:%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%y-%m-%d %H:%M:%S")
file_handler.setFormatter(fmt)
_log.addHandler(file_handler)