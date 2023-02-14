import json
import time
import sys
import aiofiles
from khl import Message,Event

#将获取当前时间封装成函数方便使用
def GetTime():  
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

# 打开文件
def open_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    return tmp
# 写入文件
async def write_file(path: str, value,ifAio=False):
    if ifAio:
        async with aiofiles.open(path, 'w+', encoding='utf-8') as f:
            await f.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        with open(path, 'w+', encoding='utf-8') as fw2:
            json.dump(value, fw2, indent=2, sort_keys=True, ensure_ascii=False)


# 设置日志文件的重定向
def logDup(path:str='./log/log.txt'):
    file =  open(path, 'a')
    sys.stdout = file 
    sys.stderr = file
# 刷新缓冲区
def logFlush():
    sys.stdout.flush() # 刷新缓冲区
    sys.stderr.flush() # 刷新缓冲区

# 打印msg内容，用作日志
def logging(msg: Message):
    print(f"[{GetTime()}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} - content:{msg.content}")
    logFlush() # 刷新缓冲区 

# 打印event的日志
def loggingE(e: Event,func=""):
    print(f"[{GetTime()}] {func} Event:{e.body}")
    logFlush() # 刷新缓冲区

# help命令的内容
def help_text():
    text = "ticket-bot的命令操作\n"
    text+=f"`/ticket` 在本频道发送一条消息，作为ticket的开启按钮\n"
    text+=f"`/tkcm 工单id 备注` 对某一条已经关闭的工单进行备注\n"
    text+=f"`/aar 角色id` 将角色id添加进入管理员角色\n"
    text+=f"```\nid获取办法：kook设置-高级设置-打开开发者模式；右键用户头像即可复制用户id，右键频道/分组即可复制id，角色id需要进入服务器管理面板的角色页面中右键复制\n```\n"
    text+=f"以上命令都需要管理员才能操作\n"
    text+=f"`/gaming 游戏选项` 让机器人开始打游戏(代码中指定了几个游戏)\n"
    text+=f"`/singing 歌名 歌手` 让机器人开始听歌\n"
    text+=f"`/sleeping 1(2)` 让机器人停止打游戏1 or 听歌2\n"
    return text

###############################################################################################

Botconf = open_file('config/config.json')      # 机器人配置文件
TKconf = open_file('config/TicketConf.json')   # 工单配置文件/表情角色配置文件

TKlog = open_file('./log/TicketLog.json')      # ticket 历史记录
TKMsgLog = open_file('./log/TicketMsgLog.json')# ticket 消息记录
# EMOJI键值存在才会加载
if 'emoji' in TKconf:
    ColorIdDict = open_file('./log/ColorID.json')  # 记录用户在某个消息下获取的角色