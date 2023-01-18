# encoding: utf-8:
import json
import requests
import aiohttp
import time
import traceback
import os

from khl import Bot, Message, EventTypes, Event,Client,PublicMessage
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from khl.command import Rule

# 新建机器人，token 就是机器人的身份凭证
with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 用读取来的 config 初始化 bot，字段对应即可
bot = Bot(token=config['token'])

# kook api的头链接，请不要修改
kook_base="https://www.kookapp.cn"
Botoken = config['token']
headers={f'Authorization': f"Bot {Botoken}"}
debug_ch = None #bug 修复频道
log_ch = None #tikcet log频道

#将获取当前时间封装成函数方便使用
def GetTime():  
    return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

#记录开机时间
start_time = GetTime()

# 在控制台打印msg内容，用作日志
def logging(msg: Message):
    now_time = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{now_time}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} - content:{msg.content}")

def loggingE(e: Event,func=""):
    now_time = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{now_time}] {func} Event:{e.body}")

# `/hello`指令，一般用于测试bot是否成功上线
@bot.command(name='hello')
async def world(msg: Message):
    logging(msg)
    await msg.reply('world!')

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

@bot.command(name='TKhelp')
async def help(msg: Message):
    logging(msg)
    text = help_text()
    await msg.reply(text)

#有人at机器人的时候也发送帮助命令
@bot.command(regex=r'(.+)', rules=[Rule.is_bot_mentioned(bot)])
async def atBOT(msg: Message, mention_str: str):
    logging(msg)
    text = help_text()
    await msg.reply(text)
    
#####################################机器人动态#########################################
 
from endpoints import status_active_game,status_active_music,status_delete,upd_card

# 开始打游戏
@bot.command()
async def gaming(msg: Message,game:int):
    logging(msg)
    #await bot.client.update_playing_game(3,1)# 英雄联盟
    if game == 1:    
        ret = await status_active_game(464053) # 人间地狱
        await msg.reply(f"{ret['message']}，Bot上号人间地狱啦！")
    elif game == 2:
        ret = await status_active_game(3)      # 英雄联盟
        await msg.reply(f"{ret['message']}，Bot上号LOL啦！")
    elif game == 3:
        ret = await status_active_game(23)     # CSGO
        await msg.reply(f"{ret['message']}，Bot上号CSGO啦！")

# 开始听歌
@bot.command()
async def singing(msg: Message,music:str,singer:str):
    logging(msg)
    ret = await status_active_music(music,singer)
    await msg.reply(f"{ret['message']}，Bot开始听歌啦！")
    
# 停止打游戏1/听歌2
@bot.command(name='sleep')
async def sleeping(msg: Message,d:int):
    logging(msg)
    ret = await status_delete(d)
    if d ==1:
        await msg.reply(f"{ret['message']}，Bot下号休息啦!")
    elif d==2:
        await msg.reply(f"{ret['message']}，Bot摘下了耳机~")

################################以下是给ticket功能的内容########################################

# 从文件中读取频道和分组id
with open('./config/TicketConf.json', 'r', encoding='utf-8') as f1:
    TKconf = json.load(f1)

# 从文件中读取历史ticket记录
with open('./log/TicketLog.json', 'r', encoding='utf-8') as f2:
    TKlog = json.load(f2)

# 从文件中读取历史ticket msg记录
with open('./log/TicketMsgLog.json', 'r', encoding='utf-8') as f2:
    TKMsgLog = json.load(f2)

# 判断用户是否在管理员身份组里面
async def user_in_admin_role(guild_id:str,user_id:str):
    if guild_id != TKconf['guild_id']: 
        return False # 如果不是预先设置好的服务器直接返回错误，避免bot被邀请到其他服务器去
    # 通过服务器id和用户id获取用户在服务器中的身份组
    guild = await bot.client.fetch_guild(guild_id)
    user_roles = (await guild.fetch_user(user_id)).roles
    for ar in user_roles:# 遍历用户的身份组，看看有没有管理员身份组id
        if str(ar) in TKconf["admin_role"]:
            return True

    return False

# ticket系统,发送卡片消息
@bot.command()
async def ticket(msg: Message):
    logging(msg)
    global TKconf
    try:
        if (await user_in_admin_role(msg.ctx.guild.id,msg.author_id)):
            ch_id = msg.ctx.channel.id #当前所处的频道id
            # 发送消息
            send_msg = await msg.ctx.channel.send(
                            CardMessage(
                                Card(Module.Section(
                                        '请点击右侧按钮发起ticket',
                                        Element.Button('发起ticket',Types.Click.RETURN_VAL)))))
            if ch_id not in TKconf["channel_id"]: #如果不在    
                # 发送完毕消息，并将该频道插入此目录
                TKconf["channel_id"][ch_id] = send_msg["msg_id"] # 上面发送的消息的id
                print(f"[Add TKch] Au:{msg.author_id} ChID:{ch_id} MsgID:{send_msg['msg_id']}")
            else:
                old_msg = TKconf["channel_id"][ch_id] #记录旧消息的id输出到日志
                TKconf["channel_id"][ch_id] = send_msg["msg_id"] # 上面发送的消息的id
                print(f"[Add TKch] Au:{msg.author_id} ChID:{ch_id} New_MsgID:{send_msg['msg_id']} Old:{old_msg}")

            # 保存到文件
            with open("./config/TicketConf.json", 'w', encoding='utf-8') as fw2:
                json.dump(TKconf, fw2, indent=2, sort_keys=True, ensure_ascii=False)
        else:
            await msg.reply(f"您没有权限执行本命令！")
    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)

# ticket系统,对已完成ticket进行备注
@bot.command(name='tkcm')
async def ticket_commit(msg: Message,tkno:str,*args):
    logging(msg)
    if tkno == "":
        await msg.reply(f"请提供ticket的八位数编号，如 000000123")
        return
    elif args == ():
        await msg.reply(f"ticket 备注不得为空！")
        return
    try:
        global TKconf,TKlog
        if (await user_in_admin_role(msg.ctx.guild.id,msg.author_id)):
            if tkno not in TKlog['data']:
                await msg.reply("您输入的ticket编号未在数据库中！")
                return
            
            cmt = ' '.join(args) #备注信息
            TKlog['data'][tkno]['cmt'] = cmt
            TKlog['data'][tkno]['cmt_usr'] = msg.author_id
            cm = CardMessage()
            c = Card(Module.Header(f"工单 ticket.{tkno} 已备注"),Module.Context(f"信息更新于 {GetTime()}"),Module.Divider())
            text = f"开启时间: {TKlog['data'][tkno]['start_time']}\n"
            text+= f"发起用户: (met){TKlog['data'][tkno]['usr_id']}(met)\n"
            text+= f"结束时间: {TKlog['data'][tkno]['end_time']}\n"
            text+= f"关闭用户: (met){TKlog['data'][tkno]['end_usr']}(met)\n"
            text+= "\n"
            text+= f"来自 (met){msg.author_id}(met) 的备注:\n> {cmt}"
            c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
            cm.append(c)
            await upd_card(TKlog['data'][tkno]['log_msg_id'], cm, channel_type=msg.channel_type)
            # 保存到文件
            with open("./log/TicketLog.json", 'w', encoding='utf-8') as fw2:
                json.dump(TKlog, fw2, indent=2, sort_keys=True, ensure_ascii=False)
            print(f"[Cmt TK] Au:{msg.author_id} - TkID:{tkno} = {cmt}")
        else:
            await msg.reply(f"您没有权限执行本命令！")
    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)

@bot.command(name='add_admin_role',aliases=['aar'])
async def ticket_admin_role_add(msg:Message,role_id="",*arg):
    logging(msg)
    if role_id == "":
        await msg.reply("请提供需要添加的角色id")
        return
    try:
        if not (await user_in_admin_role(msg.ctx.guild.id,msg.author_id)):
            await msg.reply(f"您没有权限执行本命令！")
            return
        
        global TKconf
        if role_id in TKconf['admin_role']:
            await msg.reply("这个id已经在配置文件 `TKconf['admin_role']` 中啦！")
            return

        guild_roles = await (await bot.client.fetch_guild(msg.ctx.guild.id)).fetch_roles()
        print(guild_roles)
        for r in guild_roles:
            if int(role_id) == r.id:
                TKconf['admin_role'].append(role_id)
                await msg.reply(f"{role_id} 添加成功！")
                # 保存到文件
                with open("./config/TicketConf.json", 'w', encoding='utf-8') as fw2:
                    json.dump(TKconf, fw2, indent=2, sort_keys=True, ensure_ascii=False)
                print(f"[ADD.ADMIN.ROLE] role_id:{role_id} add to TKconf")
                break
        else:
            await msg.reply(f"添加错误，请确认您提交的是本服务器的角色id")

    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)


######################################### ticket 监看 ###############################################################

# 监看工单系统(开启)
# 相关api文档 https://developer.kaiheila.cn/doc/http/channel#%E5%88%9B%E5%BB%BA%E9%A2%91%E9%81%93
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def ticket_open(b: Bot, e: Event):
    # 判断是否为ticket申请频道的id（文字频道id）
    global TKconf,TKlog
    try:
        if e.body['target_id'] in TKconf["channel_id"]:
            loggingE(e,"TK.OPEN")
            global kook_base,headers
            url1=kook_base+"/api/v3/channel/create"# 创建频道
            params1 = {"guild_id": e.body['guild_id'] ,"parent_id":TKconf["category_id"],"name":e.body['user_info']['username']}
            async with aiohttp.ClientSession() as session:
                async with session.post(url1, data=params1,headers=headers) as response:
                        ret1=json.loads(await response.text())
                        #print(ret1["data"]["id"])

            url2=kook_base+"/api/v3/channel-role/create"#创建角色权限
            params2 = {"channel_id": ret1["data"]["id"] ,"type":"user_id","value":e.body['user_id']}
            async with aiohttp.ClientSession() as session:
                async with session.post(url2, data=params2,headers=headers) as response:
                        ret2=json.loads(await response.text())
                        #print(f"ret2: {ret2}")
            
            # 服务器角色权限值见 https://developer.kaiheila.cn/doc/http/guild-role
            url3=kook_base+"/api/v3/channel-role/update"#设置角色权限
            params3 = {"channel_id": ret1["data"]["id"] ,"type":"user_id","value":e.body['user_id'],"allow":2048}
            async with aiohttp.ClientSession() as session:
                async with session.post(url3, data=params3,headers=headers) as response:
                        ret3=json.loads(await response.text())
                        #print(f"ret3: {ret3}")
            
            # 管理员角色id，修改配置文件中的对应部分
            text = f"(met){e.body['user_id']}(met) 发起了帮助，请等待管理猿的回复\n"
            for roles_id in TKconf["admin_role"]:
                text+=f"(rol){roles_id}(rol) "
            text+="\n"
            
            cm = CardMessage()
            c1 = Card(Module.Section(Element.Text(text,Types.Text.KMD)))
            c1.append(Module.Section('帮助结束后，请点击下方“关闭”按钮关闭该ticket频道\n'))
            c1.append(Module.ActionGroup(Element.Button('关闭', Types.Click.RETURN_VAL,theme=Types.Theme.DANGER)))
            cm.append(c1)
            channel = await bot.client.fetch_public_channel(ret1["data"]["id"]) 
            sent = await bot.client.send(channel,cm)

            #发送消息完毕，记录消息信息
            no = str(TKlog["TKnum"])#消息的编号，改成str处理
            no = no.rjust(8, '0')
            TKlog['data'][no] = {}
            TKlog['data'][no]['usr_id'] = e.body['user_id'] # 发起ticket的用户id
            TKlog['data'][no]['usr_info'] = f"{e.body['user_info']['username']}#{e.body['user_info']['identify_num']}" # 用户名字
            TKlog['data'][no]['msg_id'] = sent['msg_id'] # bot发送消息的id
            TKlog['data'][no]['channel_id'] = ret1["data"]["id"] # bot创建的频道id
            TKlog['data'][no]['start_time'] = GetTime() # 开启时间
            TKlog['msg_pair'][sent['msg_id']] = no # 键值对，msgid映射ticket编号
            TKlog['TKchannel'][ret1["data"]["id"]] = no #记录bot创建的频道id，用于消息日志
            TKlog['TKnum']+=1

            # 保存到文件
            with open("./log/TicketLog.json", 'w', encoding='utf-8') as fw2:
                json.dump(TKlog, fw2, indent=2, sort_keys=True, ensure_ascii=False)
            print(f"[TK.OPEN] Au:{e.body['user_id']} - TkID:{no} at {TKlog['data'][no]['start_time']}")
    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await debug_ch.send(err_str)
        print(err_str)


# 监看工单关闭情况
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def ticket_close(b: Bot, e: Event):
    try:
        # 避免与tiket申请按钮冲突（文字频道id）
        if e.body['target_id'] in TKconf["channel_id"]:
            print(f"[TK.CLOSE] BTN.CLICK channel_id in TKconf:{e.body['msg_id']}")
            return

        # 判断关闭按钮的卡片消息id是否在以开启的tk日志中，如果不在，则return
        if e.body['msg_id'] not in TKlog["msg_pair"]:
            print(f"[TK.CLOSE] BTN.CLICK msg_id not in TKlog:{e.body['msg_id']}")
            return
        
        # 基本有效则打印event的json内容
        loggingE(e,"TK.CLOSE")

        # 判断是否为管理员，只有管理可以关闭tk
        if not (await user_in_admin_role(e.body['guild_id'],e.body['user_id'])):
            temp_ch = await bot.client.fetch_public_channel(e.body['target_id'])
            await temp_ch.send(f"```\n抱歉，只有管理员用户可以关闭ticket\n```")
            print(f"[TK.CLOSE] BTN.CLICK by none admin usr:{e.body['user_id']} - C:{e.body['target_id']}")
            return

        # 保存ticket的聊天记录(不在TKMsgLog里面代表一句话都没发)
        if e.body['target_id'] in TKMsgLog['TKMsgChannel']:
            filename = f"./log/ticket/{TKlog['msg_pair'][e.body['msg_id']]}.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)#保存之前创建该文件（不然会报错）
            with open(filename, 'w', encoding='utf-8') as fw2:
                json.dump(TKMsgLog['data'][e.body['target_id']], fw2, indent=2, sort_keys=True, ensure_ascii=False)
            del TKMsgLog["data"][e.body['target_id']]
            del TKMsgLog["TKMsgChannel"][e.body['target_id']]
            print(f"[TK.CLOSE] save log msg of {TKlog['msg_pair'][e.body['msg_id']]}")

        # 保存完毕记录后，删除频道
        url2=kook_base+'/api/v3/channel/delete'
        params2 = {"channel_id": e.body['target_id']}
        async with aiohttp.ClientSession() as session:
            async with session.post(url2, data=params2,headers=headers) as response:
                ret2=json.loads(await response.text())
        print(f"[TK.CLOSE] delete channel {e.body['target_id']}")

        # 记录信息
        no = TKlog['msg_pair'][e.body['msg_id']] #通过消息id获取到ticket的编号
        TKlog['data'][no]['end_time'] = GetTime() #结束时间
        TKlog['data'][no]['end_usr'] = e.body['user_id'] #是谁关闭的
        TKlog['data'][no]['end_usr_info'] = f"{e.body['user_info']['username']}#{e.body['user_info']['identify_num']}" # 用户名字
        del TKlog['msg_pair'][e.body['msg_id']] #删除键值对
        print(f"[TK.CLOSE] TKlog handling finished NO:{no}")

        # 发送消息给开启该tk的用户和log频道
        cm = CardMessage()
        c = Card(Module.Header(f"工单 ticket.{no} 已关闭"),Module.Divider())
        text = f"开启时间: {TKlog['data'][no]['start_time']}\n"
        text+= f"发起用户: (met){TKlog['data'][no]['usr_id']}(met)\n"
        text+= f"结束时间: {TKlog['data'][no]['end_time']}\n"
        text+= f"关闭用户: (met){TKlog['data'][no]['end_usr']}(met)\n"
        c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
        cm.append(c)
        open_usr = await bot.client.fetch_user(TKlog['data'][no]['usr_id'])
        log_usr_sent = await open_usr.send(cm) #发送给用户
        log_ch_sent = await log_ch.send(cm) #发送到频道
        TKlog['data'][no]['log_ch_msg_id'] = log_ch_sent['msg_id']
        TKlog['data'][no]['log_usr_msg_id'] = log_usr_sent['msg_id']
        print(f"[TK.CLOSE] TKlog msg send finished - ChMsgID:{log_ch_sent['msg_id']} - UMsgID:{log_usr_sent['msg_id']}")

        # 保存到文件
        with open("./log/TicketLog.json", 'w', encoding='utf-8') as fw2:
            json.dump(TKlog, fw2, indent=2, sort_keys=True, ensure_ascii=False)
        print(f"[TK.CLOSE] Au:{e.body['user_id']} - TkID:{no} at {TKlog['data'][no]['end_time']}")
    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await debug_ch.send(err_str)
        print(err_str)

# 记录ticket频道的聊天记录
@bot.on_message()
async def ticket_msg_log(msg: Message):
    try:
        # 判断频道id是否在以开启的tk日志中，如果不在，则return
        if msg.ctx.channel.id not in TKlog["TKchannel"]:
            return
        
        # 如果不在TKMsgLog日志中，说明是初次发送消息，则创建键值
        no = TKlog["TKchannel"][msg.ctx.channel.id]
        if msg.ctx.channel.id not in TKMsgLog["TKMsgChannel"]:
            log = {'first_msg_time':GetTime(),'msg':{}}
            TKMsgLog['data'][msg.ctx.channel.id] = log
            TKMsgLog['TKMsgChannel'][msg.ctx.channel.id] = GetTime() # 添加频道，代表该频道有发送过消息
        
        # 如果在，那么直接添加消息就行
        TKMsgLog['data'][msg.ctx.channel.id]['msg'][str(time.time())] = {
            "msg_id":msg.id,
            "channel_id":msg.ctx.channel.id,
            "user_id":msg.author_id,
            "user_name":f"{msg.author.nickname}#{msg.author.identify_num}",
            "content": msg.content,
            "time":GetTime()
        }
        print(f"[{GetTime()}] NO:{no} Au:{msg.author_id} {msg.author.nickname}#{msg.author.identify_num} = {msg.content}")
    except:
        err_str = f"ERR! [{GetTime()}] log_tk_msg\n```\n{traceback.format_exc()}\n```"
        await debug_ch.send(err_str)
        print(err_str)

# 定时保存TKMsgLog
@bot.task.add_interval(minutes=5)
async def ticket_msg_log_save():
    with open("./log/TicketMsgLog.json", 'w', encoding='utf-8') as fw2:
        json.dump(TKMsgLog, fw2, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"[TK.MSG.LOG.SAVE] TKMsgLog save at {GetTime()}")
    
################################以下是给用户上色功能的内容########################################

# 22.12.12 这部分写的很烂，等待我重写！新的版本在kook-valorant-bot中有

# 设置自动上色event的服务器id和消息id
Guild_ID = '1573724356603748'
Msg_ID_1 = '0a4b9403-de0b-494e-b216-3d1dbe957d0f'
Msg_ID_2 = '5d92f952-15c1-46a4-b370-41a9cf739e50'
Msg_ID_3 = 'd4dbb164-bd80-469b-9473-8285a9c91e0d'

# 用于记录使用表情回应获取ID颜色的用户
def save_userid_color(userid:str,d:int,emoji:str):
    flag=0
    if d ==1:
        # 需要先保证原有txt里面没有保存该用户的id，才进行追加
        with open("./config/idsave_1.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()   
        #使用r+同时读写（有bug）
            for line in lines:
                v = line.strip().split(':')
                if userid == v[0]:
                    flag=1 #因为用户已经回复过表情，将flag置为1
                    fr1.close()
                    return flag
        fr1.close()
        #原有txt内没有该用户信息，进行追加操作
        if flag==0:
            fw2 = open("./config/idsave_1.txt",'a+',encoding='utf-8')
            fw2.write(userid + ':' + emoji + '\n')
            fw2.close()
        return flag

    elif d == 2:
        # 需要先保证原有txt里面没有保存该用户的id，才进行追加
        with open("./config/idsave_2.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()   
        #使用r+同时读写（有bug）
            for line in lines:
                v = line.strip().split(':')
                if userid == v[0]:
                    flag=1 #因为用户已经回复过表情，将flag置为1
                    fr1.close()
                    return flag
        fr1.close()
        #原有txt内没有该用户信息，进行追加操作
        if flag==0:
            fw2 = open("./config/idsave_2.txt",'a+',encoding='utf-8')
            fw2.write(userid + ':' + emoji + '\n')
            fw2.close()
        return flag

    elif d == 3:
        # 需要先保证原有txt里面没有保存该用户的id，才进行追加
        with open("./config/idsave_3.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()   
        #使用r+同时读写（有bug）
            for line in lines:
                v = line.strip().split(':')
                if userid == v[0]:
                    flag=1 #因为用户已经回复过表情，将flag置为1
                    fr1.close()
                    return flag
        fr1.close()
        #原有txt内没有该用户信息，进行追加操作
        if flag==0:
            fw2 = open("./config/idsave_3.txt",'a+',encoding='utf-8')
            fw2.write(userid + ':' + emoji + '\n')
            fw2.close()
        return flag
     

# 在不修改代码的前提下设置上色功能的服务器和监听消息
@bot.command()
async def Set_GM(msg: Message,d:int,Card_Msg_id:str):
    logging(msg)
    global Guild_ID,Msg_ID_1,Msg_ID_2,Msg_ID_3 #需要声明全局变量
    Guild_ID = msg.ctx.guild.id
    if d == 1:
        Msg_ID_1 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息1更新为 {Msg_ID_1}\n')
    elif d == 2:
        Msg_ID_2 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息2更新为 {Msg_ID_2}\n')
    elif d == 3:
        Msg_ID_3 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息3更新为 {Msg_ID_3}\n')


# 判断消息的emoji回应，并给予不同角色
@bot.on_event(EventTypes.ADDED_REACTION)
async def grant_roles(b: Bot, event: Event):
    g = await bot.client.fetch_guild(Guild_ID)# 填入服务器id
    loggingE(event,"EMOJI.REACT")#事件日志

    channel = await bot.client.fetch_public_channel(event.body['channel_id']) #获取事件频道
    s = await bot.client.fetch_user(event.body['user_id'])#通过event获取用户id(对象)
    # 判断用户回复的emoji是否合法
    emoji=event.body["emoji"]['id']
 
    # 第一个消息
    if event.body['msg_id'] == Msg_ID_1:  #将msg_id和event.body msg_id进行对比，确认是我们要的那一条消息的表情回应
        flag=0
        with open("./config/emoji1.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 1, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    #ret=0
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的`游戏角色`角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        await g.grant_role(s,role)
                        await b.send(channel, f"bot已经给你上了 {event.body['emoji']['name']} 对应的角色",temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])
    
    # 第二个消息
    elif event.body['msg_id'] == Msg_ID_2:
        # channel = await bot.client.fetch_public_channel(event.body['channel_id']) #获取事件频道
        # s = await bot.client.fetch_user(event.body['user_id'])#通过event获取用户id(对象)
        # # 判断用户回复的emoji是否合法
        # emoji=event.body["emoji"]['id']
        flag=0
        with open("./config/emoji2.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 2, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    #ret=0
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的`休闲游戏`角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        await g.grant_role(s,role)
                        await b.send(channel, f"bot已经给你上了 {event.body['emoji']['name']} 对应的角色",temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])
    
    # 第三个消息
    elif event.body['msg_id'] == Msg_ID_3:
        flag=0
        with open("./config/emoji3.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 3, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    #ret=0
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的`社会身份`角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        await g.grant_role(s,role)
                        await b.send(channel, f"bot已经给你上了 {event.body['emoji']['name']} 对应的角色",temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])


###################################################################################################################################

# 开机的时候打印一次时间，记录重启时间
print(f"Start at: [%s]" % start_time)

@bot.task.add_date()
async def loading_channel_cookie():
    try:
        global debug_ch, log_ch
        debug_ch = await bot.client.fetch_public_channel(TKconf['debug_channel'])
        log_ch = await bot.client.fetch_public_channel(TKconf['log_channel'])
        print("[BOT.TASK] fetch_public_channel success")
    except:
        print("[BOT.TASK] fetch_public_channel failed")
        print(traceback.format_exc())
        os._exit(-1)  #出现错误直接退出程序

# 凭证传好了、机器人新建好了、指令也注册完了
# 接下来就是运行我们的机器人了，bot.run() 就是机器人的起跑线
bot.run()