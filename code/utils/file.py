import json
import os
import sys
import traceback
from khl import Message, Event
from .gtime import GetTime
from .myLog import _log


def open_file(path):
    """打开文件"""
    with open(path, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    return tmp


def write_file(path: str, value):
    """写入文件,仅支持json格式的dict或者list"""
    with open(path, 'w+', encoding='utf-8') as fw2:
        json.dump(value, fw2, indent=2, sort_keys=True, ensure_ascii=False)


# 刷新缓冲区
def logFlush():
    sys.stdout.flush()  # 刷新缓冲区
    sys.stderr.flush()  # 刷新缓冲区


# 设置日志文件的重定向
def logDup(path: str = './log/log.txt'):
    file = open(path, 'a')
    sys.stdout = file
    sys.stderr = file
    _log.info(f"stdout/stderr dup to {path}")
    logFlush()


def logging(msg: Message):
    """打印msg内容，用作日志"""
    _log.info(
        f"G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} - content:{msg.content}"
    )


def loggingE(e: Event, func=" "):
    """打印event的日志"""
    _log.info(f"{func} | Event:{e.body}")


def create_logFile(path: str, content):
    """创建根文件/文件夹

    Retrun value
    - False: path exist but keyerr / create false
    - True: path exist / path not exist, create success
    """
    try:
        # 如果文件路径存在
        if os.path.exists(path):
            tmp = open_file(path)  # 打开文件
            for key in content:  # 遍历默认的键值
                if key not in tmp:  # 判断是否存在
                    _log.info(
                        f"[create_logFile] ERR! files exists, but key '{key}' not in {path} files!"
                    )
                    return False
            return True
        # 文件路径不存在，通过content写入path
        write_file(path, content)
        return True
    except Exception as result:
        _log.exception(f"create logFile ERR")
        return False



###############################################################################################

# 所有文件如下
Botconf = open_file('config/config.json')
"""机器人配置文件"""
TKconf = open_file('config/TicketConf.json')
"""工单配置文件/表情角色配置文件"""
ColorIdDict = {}
"""记录用户在某个消息下获取的角色"""

# 日志文件路径
LogPath = './log'
"""根路径"""
TKlogPath = './log/TicketLog.json'
"""工单日志 TicketLog.json"""
TKMsgLogPath = './log/TicketMsgLog.json'
"""工单消息日志 TicketMsgLog.json"""
TKLogFilePath = './log/ticket'
"""存放ticket消息记录日志的文件夹"""
ColorIdPath = './log/ColorID.json'
"""表情上角色日志 ColorID.json"""
EMOJI_ROLES_ON:bool = 'emoji' in TKconf and TKconf['emoji'] != {}
"""是否开启了表情回应上角色的功能"""

try:
    # 如果log路径不存在，创建log文件夹
    if (not os.path.exists(LogPath)):
        os.makedirs(LogPath)  # 文件夹不存在，创建
    # 自动创建TicketLog和TicketMsgLog日志文件
    if (not create_logFile(TKlogPath, {
            "TKnum": 0,
            "data": {},
            "msg_pair": {},
            "TKchannel": {}
    })):
        os._exit(-1)  # err,退出进程
    if (not create_logFile(TKMsgLogPath, {"TKMsgChannel": {}, "data": {}})):
        os._exit(-1)  # err,退出进程
    # 创建 ./log/ticket 文件夹，用于存放ticket的日志记录
    if (not os.path.exists(TKLogFilePath)):
        os.makedirs(TKLogFilePath)  # 文件夹不存在，创建

    # 创建日志文件成功，打开
    TKlog = open_file(TKlogPath) 
    """ticket 历史记录"""
    TKMsgLog = open_file(TKMsgLogPath) 
    """ticket 消息记录"""

    # 配置文件中，EMOJI键值存在才会加载
    if EMOJI_ROLES_ON:
        # 自动创建ColorID日志文件
        if (not create_logFile(ColorIdPath, {"data": {}})):
            os._exit(-1)  # err,退出进程
        # 没有错误，打开文件
        ColorIdDict = open_file(ColorIdPath)  # 记录用户在某个消息下获取的角色

    _log.info(f"[BOT.START] open log.files success!")
except:
    _log.info(f"[BOT.START] open log.files ERR")
    os._exit(-1)


def write_all_files():
    """写入所有文件"""
    write_file(TKMsgLogPath, TKMsgLog)
    write_file(ColorIdPath, ColorIdDict)
    write_file(TKlogPath,TKlog)