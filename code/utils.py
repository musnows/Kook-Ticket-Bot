import json
import os
import sys
import traceback
from khl import Message,Event

from datetime import datetime,timezone,timedelta

def GetTime():
    """获取当前时间，格式为 `23-01-01 00:00:00`"""    
    utc_dt = datetime.now(timezone.utc) # 获取当前时间
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8))) # 转换为北京时间
    return bj_dt.strftime('%y-%m-%d %H:%M:%S')
    # use time.loacltime if you aren't using BeiJing Time
    # return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

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
    sys.stdout.flush() # 刷新缓冲区
    sys.stderr.flush() # 刷新缓冲区

# 设置日志文件的重定向
def logDup(path:str='./log/log.txt'):
    file =  open(path, 'a')
    sys.stdout = file 
    sys.stderr = file
    print(f"stdout/stderr dup to {path}")
    logFlush()

def logging(msg: Message):
    """打印msg内容，用作日志"""
    print(f"[{GetTime()}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} - content:{msg.content}")
    logFlush() # 刷新缓冲区 


def loggingE(e: Event,func=""):
    """打印event的日志"""
    print(f"[{GetTime()}] {func} Event:{e.body}")
    logFlush() # 刷新缓冲区

def help_text():
    """help命令的内容"""
    text = "ticket-bot的命令操作\n"
    text+=f"`/ticket` 在本频道发送一条消息，作为ticket的开启按钮\n"
    text+=f"`/tkcm 工单id 备注` 对某一条已经关闭的工单进行备注\n"
    text+=f"`/aar @角色组` 将角色添加进入管理员角色\n"
    text+=f"```\nid获取办法：kook设置-高级设置-打开开发者模式；右键用户头像即可复制用户id，右键频道/分组即可复制id，角色id需要进入服务器管理面板的角色页面中右键复制\n```\n"
    text+=f"以上命令都需要管理员才能操作\n"
    text+=f"`/gaming 游戏选项` 让机器人开始打游戏(代码中指定了几个游戏)\n"
    text+=f"`/singing 歌名 歌手` 让机器人开始听歌\n"
    text+=f"`/sleeping 1(2)` 让机器人停止打游戏1 or 听歌2\n"
    return text


def create_logFile(path:str,content):
    """创建根文件/文件夹

    Retrun value
    - False: path exist but keyerr / create false
    - True: path exist / path not exist, create success
    """
    try:
        # 如果文件路径存在
        if os.path.exists(path):
            tmp = open_file(path) # 打开文件
            for key in content: # 遍历默认的键值
                if key not in tmp: # 判断是否存在
                    print(f"[create_logFile] ERR! files exists, but key '{key}' not in {path} files!")
                    return False
            return True
        # 文件路径不存在，通过content写入path
        write_file(path,content)
        return True
    except Exception as result:
        print(f"[create_logFile] ERR!\n{traceback.format_exc()}")
        return False

###############################################################################################

# 所有文件如下
Botconf = open_file('config/config.json') 
"""机器人配置文件"""
TKconf = open_file('config/TicketConf.json')
"""工单配置文件/表情角色配置文件"""

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

try:
    # 如果log路径不存在，创建log文件夹
    if(not os.path.exists(LogPath)):
        os.makedirs(LogPath) # 文件夹不存在，创建
    # 自动创建TicketLog和TicketMsgLog日志文件
    if(not create_logFile(TKlogPath,{"TKnum": 0,"data": {},"msg_pair": {},"TKchannel": {}})):
        os._exit(-1) # err,退出进程    
    if(not create_logFile(TKMsgLogPath,{"TKMsgChannel": {},"data": {}})):
        os._exit(-1) # err,退出进程
    # 创建 ./log/ticket 文件夹，用于存放ticket的日志记录
    if(not os.path.exists(TKLogFilePath)):
        os.makedirs(TKLogFilePath) # 文件夹不存在，创建

    # 创建日志文件成功，打开
    TKlog = open_file(TKlogPath) # ticket 历史记录
    TKMsgLog = open_file(TKMsgLogPath)# ticket 消息记录

    # 配置文件中，EMOJI键值存在才会加载
    if 'emoji' in TKconf:
        # 自动创建ColorID日志文件
        if(not create_logFile(ColorIdPath,{"data":{}})): 
            os._exit(-1)# err,退出进程
        # 没有错误，打开文件
        ColorIdDict = open_file(ColorIdPath)  # 记录用户在某个消息下获取的角色
    
    print(f"[BOT.START] open log files success!")
except:
    print(f"[BOT.START] open files\n{traceback.format_exc()}")
    os._exit(-1)