# encoding: utf-8:
import json
import asyncio
import aiohttp
import time
import traceback
import os

from khl import Bot,Cert, Message, EventTypes, Event,Client,PublicChannel
from khl.card import CardMessage, Card, Module, Element, Types
from kookApi import *
from utils import *

# config是在utils.py中读取的，直接import就能使用
# bot = Bot(token=Botconf['token']) # websocket
bot = Bot(cert=Cert(token=Botconf['token'], verify_token=Botconf['verify_token'],encrypt_key=Botconf['encrypt']),port=5000) # webhook

debug_ch = PublicChannel # bug    日志频道
log_ch = PublicChannel   # tikcet 日志频道
Guild_ID = TKconf['guild_id'] # 服务器id

#记录开机时间
start_time = GetTime()

####################################################################################

# `/hello`指令，一般用于测试bot是否成功上线
@bot.command(name='hello',case_sensitive=False)
async def world(msg: Message):
    logging(msg)
    await msg.reply('world!')

# TKhelp帮助命令
@bot.command(name='TKhelp',case_sensitive=False)
async def help(msg: Message):
    logging(msg)
    text = help_text()
    await msg.reply(text)

    
#####################################机器人动态#########################################

# 开始打游戏
@bot.command(name='game',aliases=['gaming'],case_sensitive=False)
async def gaming(msg: Message,game:int=0,*arg):
    logging(msg)
    try:
        if game == 0:
            await msg.reply(f"[gaming] 参数错误，用法「/gaming 数字」\n1-人间地狱，2-英雄联盟，3-CSGO")
            return
        elif game == 1:    
            ret = await status_active_game(464053) # 人间地狱
            await msg.reply(f"{ret['message']}，Bot上号人间地狱啦！")
        elif game == 2:
            ret = await status_active_game(3)      # 英雄联盟
            await msg.reply(f"{ret['message']}，Bot上号LOL啦！")
        elif game == 3:
            ret = await status_active_game(23)     # CSGO
            await msg.reply(f"{ret['message']}，Bot上号CSGO啦！")
    
    except Exception as result:
        err_str = f"ERR! [{GetTime()}] sleep\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)

# 开始听歌
@bot.command(name='sing',aliases=['singing'],case_sensitive=False)
async def singing(msg: Message,music:str='e',singer:str='e',*arg):
    logging(msg)
    try:
        if music == 'e' or singer == 'e':
            await msg.reply(f"[singing] 参数错误，用法「/singing 歌名 歌手」")
            return
        # 参数正确，开始操作
        ret = await status_active_music(music,singer)
        await msg.reply(f"{ret['message']}，Bot开始听歌啦！")
    except Exception as result:
        err_str = f"ERR! [{GetTime()}] sleep\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)
    
# 停止打游戏1/听歌2
@bot.command(name='sleep',case_sensitive=False)
async def sleeping(msg: Message,d:int=0,*arg):
    logging(msg)
    try:
        if d == 0:
            await msg.reply(f"[sleep] 参数错误，用法「/sleep 数字」\n1-停止游戏，2-停止听歌")
        ret = await status_delete(d)
        if d ==1:
            await msg.reply(f"{ret['message']}，Bot下号休息啦!")
        elif d==2:
            await msg.reply(f"{ret['message']}，Bot摘下了耳机~")
    except Exception as result:
        err_str = f"ERR! [{GetTime()}] sleep\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)

################################以下是给ticket功能的内容########################################

# 判断用户是否在管理员身份组里面
async def user_in_admin_role(guild_id:str,user_id:str):
    if guild_id != Guild_ID: 
        return False # 如果不是预先设置好的服务器直接返回错误，避免bot被邀请到其他服务器去
    # 通过服务器id和用户id获取用户在服务器中的身份组
    guild = await bot.client.fetch_guild(guild_id)
    user_roles = (await guild.fetch_user(user_id)).roles
    for ar in user_roles:# 遍历用户的身份组，看看有没有管理员身份组id
        if str(ar) in TKconf["ticket"]["admin_role"]:
            return True

    return False

# ticket系统,发送卡片消息
@bot.command(name='ticket',case_sensitive=False)
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
            if ch_id not in TKconf["ticket"]["channel_id"]: #如果不在    
                # 发送完毕消息，并将该频道插入此目录
                TKconf["ticket"]["channel_id"][ch_id] = send_msg["msg_id"] # 上面发送的消息的id
                print(f"[{GetTime()}] [Add TKch] Au:{msg.author_id} ChID:{ch_id} MsgID:{send_msg['msg_id']}")
            else:
                old_msg = TKconf["ticket"]["channel_id"][ch_id] #记录旧消息的id输出到日志
                TKconf["ticket"]["channel_id"][ch_id] = send_msg["msg_id"] # 上面发送的消息的id
                print(f"[{GetTime()}] [Add TKch] Au:{msg.author_id} ChID:{ch_id} New_MsgID:{send_msg['msg_id']} Old:{old_msg}")

            # 保存到文件
            write_file("./config/TicketConf.json",TKconf)
        else:
            await msg.reply(f"您没有权限执行本命令！")
    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)

# ticket系统,对已完成ticket进行备注
@bot.command(name='tkcm',case_sensitive=False)
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
        if not (await user_in_admin_role(msg.ctx.guild.id,msg.author_id)):
            return await msg.reply(f"您没有权限执行本命令！")
        if tkno not in TKlog['data']:
            return await msg.reply("您输入的ticket编号未在数据库中！")
        if 'log_ch_msg_id' not in TKlog['data'][tkno]:# 工单还没有结束
            return await msg.reply("需要工单结束后，才能对其评论。")
            
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
        await upd_card(bot,TKlog['data'][tkno]['log_ch_msg_id'], cm, channel_type=msg.channel_type)
        # 保存到文件
        write_file("./log/TicketLog.json",TKlog)
        await msg.reply(f"工单「{tkno}」备注成功！")
        print(f"[{GetTime()}] [Cmt.TK] Au:{msg.author_id} - TkID:{tkno} = {cmt}")  
    except:
        err_str = f"ERR! [{GetTime()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")
        print(err_str)

@bot.command(name='add_admin_role',aliases=['aar'],case_sensitive=False)
async def ticket_admin_role_add(msg:Message,role="",*arg):
    logging(msg)
    if role == "" or '(rol)' not in role:
        return await msg.reply("请提供需要添加的角色：`/aar @角色`")

    global TKconf
    try:
        role_id = role.replace("(rol)","")
        if not (await user_in_admin_role(msg.ctx.guild.id,msg.author_id)):
            return await msg.reply(f"您没有权限执行本命令！")
        
        if role_id in TKconf["ticket"]['admin_role']:
            return await msg.reply("这个id已经在配置文件 `TKconf['ticket']['admin_role']` 中啦！")
        
        # 获取这个服务器的已有角色
        guild_roles = await (await bot.client.fetch_guild(msg.ctx.guild.id)).fetch_roles()
        print(guild_roles) # 打印出来做debug
        for r in guild_roles:
            if int(role_id) == r.id:
                TKconf["ticket"]['admin_role'].append(role_id)
                await msg.reply(f"{role_id} 添加成功！")
                # 保存到文件
                write_file("./config/TicketConf.json",TKconf)
                print(f"[{GetTime()}] [ADD.ADMIN.ROLE] role_id:{role_id} add to TKconf")
                return
        # 遍历没有找到，提示用户
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
        if e.body['target_id'] in TKconf["ticket"]["channel_id"]:
            loggingE(e,"TK.OPEN")
            # 1.创建一个以开启ticket用户昵称为名字的文字频道
            ret1 = await channel_create(e.body['guild_id'],TKconf["ticket"]["category_id"],e.body['user_info']['username'])
            # 2.先设置管理员角色的权限
            for rol in TKconf["ticket"]['admin_role']:
                # 在该频道创建一个角色权限
                await crole_create(ret1["data"]["id"],"role_id",rol)
                # 设置该频道的角色权限为可见
                await crole_update(ret1["data"]["id"],"role_id",rol,2048)
                await asyncio.sleep(0.2)# 休息一会 避免超速
                

            # 3.设置该频道的用户权限（开启tk的用户）
            # 在该频道创建一个用户权限
            await crole_create(ret1["data"]["id"],"user_id",e.body['user_id'])
            # 设置该频道的用户权限为可见
            await crole_update(ret1["data"]["id"],"user_id",e.body['user_id'],2048)

            # 管理员角色id，修改配置文件中的admin_role部分
            text = f"(met){e.body['user_id']}(met) 发起了帮助，请等待管理猿的回复\n"
            for roles_id in TKconf["ticket"]["admin_role"]:
                text+=f"(rol){roles_id}(rol) "
            text+="\n"
            # 4.在创建出来的频道发送消息
            cm = CardMessage()
            c1 = Card(Module.Section(Element.Text(text,Types.Text.KMD)))
            c1.append(Module.Section('帮助结束后，请点击下方“关闭”按钮关闭该ticket频道\n'))
            c1.append(Module.ActionGroup(Element.Button('关闭', Types.Click.RETURN_VAL,theme=Types.Theme.DANGER)))
            cm.append(c1)
            channel = await bot.client.fetch_public_channel(ret1["data"]["id"]) 
            sent = await bot.client.send(channel,cm)

            # 5.发送消息完毕，记录消息信息
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

            # 6.保存到文件
            write_file("./log/TicketLog.json",TKlog)
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
        if e.body['target_id'] in TKconf["ticket"]["channel_id"]:
            print(f"[{GetTime()}] [TK.CLOSE] BTN.CLICK channel_id in TKconf:{e.body['msg_id']}")
            return

        # 判断关闭按钮的卡片消息id是否在以开启的tk日志中，如果不在，则return
        if e.body['msg_id'] not in TKlog["msg_pair"]:
            print(f"[{GetTime()}] [TK.CLOSE] BTN.CLICK msg_id not in TKlog:{e.body['msg_id']}")
            return
        
        # 基本有效则打印event的json内容
        loggingE(e,"TK.CLOSE")

        # 判断是否为管理员，只有管理可以关闭tk
        if not (await user_in_admin_role(e.body['guild_id'],e.body['user_id'])):
            temp_ch = await bot.client.fetch_public_channel(e.body['target_id'])
            await temp_ch.send(f"```\n抱歉，只有管理员用户可以关闭ticket\n```")
            print(f"[{GetTime()}] [TK.CLOSE] BTN.CLICK by none admin usr:{e.body['user_id']} - C:{e.body['target_id']}")
            return

        # 保存ticket的聊天记录(不在TKMsgLog里面代表一句话都没发)
        if e.body['target_id'] in TKMsgLog['TKMsgChannel']:
            filename = f"./log/ticket/{TKlog['msg_pair'][e.body['msg_id']]}.json"
            # 保存日志到文件
            write_file(filename,TKMsgLog['data'][e.body['target_id']])
            del TKMsgLog["data"][e.body['target_id']]         # 删除日志文件中的该频道 
            del TKMsgLog["TKMsgChannel"][e.body['target_id']] 
            print(f"[{GetTime()}] [TK.CLOSE] save log msg of {TKlog['msg_pair'][e.body['msg_id']]}")

        # 保存完毕记录后，删除频道
        url2=kook_base+'/api/v3/channel/delete'
        params2 = {"channel_id": e.body['target_id']}
        async with aiohttp.ClientSession() as session:
            async with session.post(url2, data=params2,headers=kook_headers) as response:
                ret2=json.loads(await response.text())
        print(f"[{GetTime()}] [TK.CLOSE] delete channel {e.body['target_id']}")

        # 记录信息
        no = TKlog['msg_pair'][e.body['msg_id']] #通过消息id获取到ticket的编号
        TKlog['data'][no]['end_time'] = GetTime() #结束时间
        TKlog['data'][no]['end_usr'] = e.body['user_id'] #是谁关闭的
        TKlog['data'][no]['end_usr_info'] = f"{e.body['user_info']['username']}#{e.body['user_info']['identify_num']}" # 用户名字
        del TKlog['msg_pair'][e.body['msg_id']] #删除键值对
        print(f"[{GetTime()}] [TK.CLOSE] TKlog handling finished NO:{no}")

        # 发送消息给开启该tk的用户和log频道
        cm = CardMessage()
        c = Card(Module.Header(f"工单 ticket.{no} 已关闭"),Module.Divider())
        text = f"开启时间: {TKlog['data'][no]['start_time']}\n"
        text+= f"发起用户: (met){TKlog['data'][no]['usr_id']}(met)\n"
        text+= f"结束时间: {TKlog['data'][no]['end_time']}\n"
        text+= f"关闭用户: (met){TKlog['data'][no]['end_usr']}(met)\n"
        c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
        cm.append(c)
        # 预先定义，避免出现私信错误
        log_ch_sent = {'msg_id':'none'}
        log_usr_sent = {'msg_id':'none'}
        try:
            open_usr = await bot.client.fetch_user(TKlog['data'][no]['usr_id'])
            log_usr_sent = await open_usr.send(cm) #发送给用户
        except Exception as result:
            if '无法' in str(traceback.format_exc()):
                print(f"ERR! [{GetTime()}] tk close Au:{TKlog['data'][no]['usr_id']}\n无法向用户发起私信")
            else:
                raise result

        log_ch_sent = await log_ch.send(cm) #发送到频道
        TKlog['data'][no]['log_ch_msg_id'] = log_ch_sent['msg_id']
        TKlog['data'][no]['log_usr_msg_id'] = log_usr_sent['msg_id']
        print(f"[{GetTime()}] [TK.CLOSE] TKlog msg send finished - ChMsgID:{log_ch_sent['msg_id']} - UMsgID:{log_usr_sent['msg_id']}")

        # 保存到文件
        write_file("./log/TicketLog.json",TKlog)
        print(f"[{GetTime()}] [TK.CLOSE] Au:{e.body['user_id']} - TkID:{no} at {TKlog['data'][no]['end_time']}")
    except:
        err_str = f"ERR! [{GetTime()}] tk close\n```\n{traceback.format_exc()}\n```"
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

    
################################以下是给用户上色功能的内容########################################

# 用于记录使用表情回应获取ID颜色的用户
async def save_userid_color(userid:str,emoji:str,uid:str):
    global ColorIdDict
    # 如果键值不在，创建键值
    if uid not in ColorIdDict['data']:
        ColorIdDict['data'][uid]={}
    
    flag = False
    # 如果用户是第一次添加表情回应，那就写入文件
    if userid in ColorIdDict['data'][uid].keys():
        write_file("./log/ColorID.json",ColorIdDict)
        flag = True
    # 不管有没有这个用户，都更新
    ColorIdDict['data'][uid][userid] = emoji
    return flag

# 给用户上角色
async def Color_GrantRole(bot: Bot, event: Event):
    g = await bot.client.fetch_guild(Guild_ID)  # 服务器id
    # 将event.body的msg_id和配置文件中msg_id进行对比，确认是那一条消息的表情回应
    for euid,econf in TKconf['emoji'].items():
        if event.body['msg_id'] != econf['msg_id']:
            continue
        try:
            # 这里的打印eventbody的完整内容，包含emoji_id
            print(f"[{GetTime()}] React:{event.body}")  
            channel = await bot.client.fetch_public_channel(event.body['channel_id'])  #获取事件频道
            user = await bot.client.fetch_user(event.body['user_id'])  #通过event获取用户id(对象)
            # 判断用户回复的emoji是否合法
            emoji = event.body["emoji"]['id']
            if emoji in econf['data']:
                # 判断用户之前是否已经获取过角色
                ret = await save_userid_color(event.body['user_id'], event.body["emoji"]['id'],euid)  
                text = f'Bot已经给你上了 {emoji} 对应的颜色啦~'
                if ret:  # 已经获取过角色
                    text+="\n上次获取的角色已删除"
                # 给予角色
                role = int(econf['data'][emoji])
                await g.grant_role(user, role)
                await bot.client.send(channel, text, temp_target_id=event.body['user_id'])
            else:  # 回复的表情不合法
                await bot.client.send(channel, f'你回应的表情不在列表中哦~再试一次吧！', temp_target_id=event.body['user_id'])
        except Exception as result:
            err_text =f"出现了错误！au:{event.body['user_id']}\n{traceback.format_exc()}"
            await bot.client.send(channel,err_text,temp_target_id=event.body['user_id'])
            print(err_text)



# 判断消息的emoji回应，并给予不同角色
@bot.on_event(EventTypes.ADDED_REACTION)
async def Grant_Roles(b: Bot, event: Event):
    # 只有emoji的键值在配置文件中存在，才启用监看
    if 'emoji' in TKconf:
        await Color_GrantRole(b, event)
    # 如果想获取emoji的样式，比如频道自定义emoji，就需要在这里print
    # print(event.body) 


##########################################################################################

# 定时保存log file
@bot.task.add_interval(minutes=5)
async def log_file_save():
    write_file("./log/TicketMsgLog.json",TKMsgLog)
    write_file("./log/ColorID.json",ColorIdDict)
    print(f"[FILE.SAVE] file save at {GetTime()}")
    logFlush() # 刷新缓冲区

# kill命令安全退出
@bot.command()
async def kill(msg:Message,*arg):
    logging(msg)
    if not (await user_in_admin_role(msg.ctx.guild.id,msg.author_id)):
        await msg.reply(f"您没有权限执行本命令！")
        return
    
    # 发送信息提示
    await msg.reply(f"bot exit")
    res = await bot_offline() # 调用接口下线bot
    print(f"[KILL] [{GetTime()}] bot-off: {res}\n") # 打印下线日志
    logFlush() # 刷新缓冲区
    os._exit(0) # 进程退出


@bot.task.add_date()
async def loading_channel_cookie():
    try:
        global debug_ch, log_ch
        debug_ch = await bot.client.fetch_public_channel(TKconf["ticket"]['debug_channel'])
        log_ch = await bot.client.fetch_public_channel(TKconf["ticket"]['log_channel'])
        print(f"[BOT.START] fetch_public_channel success {GetTime()}")
        logFlush() # 刷新缓冲区
    except:
        print(f"[BOT.START] fetch_public_channel failed {GetTime()}")
        print(traceback.format_exc())
        print("[BOT.START] 获取频道失败，请检查config文件中的debug_channel和log_channel\n")
        logFlush() # 刷新缓冲区
        os._exit(-1)  #出现错误直接退出程序


# 开机 （如果是主文件就开机）
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    print(f"[BOT] Start at {start_time}")
    # 如果使用replit部署，取消下面这行的注释
    # logDup('./log/log.txt') # 标准输出重定向至文件
    bot.run()