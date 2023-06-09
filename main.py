# encoding: utf-8:
import json
import asyncio
import copy
import time
import traceback
import os

from khl import Bot, Cert, Message, EventTypes, Event, Channel
from khl.card import CardMessage, Card, Module, Element, Types
from utils import help
from utils.myLog import _log
from utils.gtime import get_time,get_time_stamp_from_str,get_time_str_from_stamp,get_time_stamp
from utils.file import *
from utils.kookApi import *
from utils.cmd import botStatus

# config是在utils.py中读取的，直接import就能使用
bot = Bot(token=Botconf["token"])  # websocket
"""main bot"""
if not Botconf["ws"]:  # webhook
    bot = Bot(
        cert=Cert(
            token=Botconf["token"],
            verify_token=Botconf["verify_token"],
            encrypt_key=Botconf["encrypt"],
        ),
        port=40000,
    )  # webhook

debug_ch: Channel
"""debug 日志频道"""
log_ch: Channel
"""tikcet 日志频道"""
GUILD_ID = TKconf["guild_id"]
"""服务器id"""
# 如下是针对工单按钮event的几个变量
OUTDATE_HOURS = TKconf["ticket"]['outdate']
"""工单频道过期时间（单位：小时）"""
class TicketBtn:
    """工单按钮event.value['type']"""
    OPEN = 'tk_open'
    """工单开启"""
    CLOSE = 'tk_close'
    """工单关闭"""
    REOPEN = 'tk_reopen'
    """工单重新激活"""
    LOCK  = 'tk_lock'
    """工单锁定"""

####################################################################################


# `/hello`指令，一般用于测试bot是否成功上线
@bot.command(name="hello", case_sensitive=False)
async def world(msg: Message):
    logging(msg)
    await msg.reply("world!")


# TKhelp帮助命令
@bot.command(name="TKhelp", case_sensitive=False)
async def help_cmd(msg: Message):
    logging(msg)
    cm = CardMessage(
        Card(
            Module.Header("ticket机器人命令面板"),
            Module.Context(f"开机于：{start_time}"),
            Module.Divider(),
            Module.Section(Element.Text(help.help_text(), Types.Text.KMD)),
        )
    )
    await msg.reply(cm)


################################以下是给ticket功能的内容########################################


# 判断用户是否在管理员身份组里面
async def user_in_admin_role(guild_id: str, user_id: str, channel_id=""):
    """channel_id 必须为 ticket命令所在频道的id，并非每个工单频道的id"""
    if guild_id != GUILD_ID:
        return False  # 如果不是预先设置好的服务器直接返回错误，避免bot被邀请到其他服务器去
    # 是master管理员
    if user_id == TKconf["ticket"]["master_id"]:
        return True
    # 通过服务器id和用户id获取用户在服务器中的身份组
    guild = await bot.client.fetch_guild(guild_id)
    user_roles = (await guild.fetch_user(user_id)).roles
    # 遍历用户的身份组，看看有没有管理员身份组id
    for ar in user_roles:
        # 判断是否在全局管理员中
        if str(ar) in TKconf["ticket"]["admin_role"]:
            return True
        # channel_id不为空，判断是否为ticket局部管理员
        if (
            channel_id
            and str(ar) in TKconf["ticket"]["channel_id"][channel_id]["admin_role"]
        ):
            return True
    # 都不是
    return False


# ticket系统,发送卡片消息
@bot.command(name="ticket", case_sensitive=False)
async def ticket(msg: Message):
    if not logging(msg):
        return
    global TKconf
    try:
        if await user_in_admin_role(msg.ctx.guild.id, msg.author_id):
            ch_id = msg.ctx.channel.id  # 当前所处的频道id
            values = json.dumps(
                {"type": TicketBtn.OPEN, "channel_id": ch_id, "user_id": msg.author_id}
            )
            # 发送消息
            send_msg = await msg.ctx.channel.send(
                CardMessage(
                    Card(
                        Module.Section(
                            "请点击右侧按钮发起ticket",
                            Element.Button(
                                "ticket", value=values, click=Types.Click.RETURN_VAL
                            )
                        )
                    )
                )
            )
            if ch_id not in TKconf["ticket"]["channel_id"]:  # 如果不在
                # 发送完毕消息，并将该频道插入此目录
                TKconf["ticket"]["channel_id"][ch_id] = {
                    "msg_id": send_msg["msg_id"],
                    "admin_role": [],
                }
                _log.info(
                    f"[Add TKch] Au:{msg.author_id} ChID:{ch_id} MsgID:{send_msg['msg_id']}"
                )
            else:
                old_msg = TKconf["ticket"]["channel_id"][ch_id]  # 记录旧消息的id输出到日志
                TKconf["ticket"]["channel_id"][ch_id]["msg_id"] = send_msg["msg_id"]  # 更新消息id
                _log.info(
                    f"[Add TKch] Au:{msg.author_id} ChID:{ch_id} New_MsgID:{send_msg['msg_id']} Old:{old_msg}"
                )

            # 保存到文件
            write_file(TKConfPath, TKconf)
        else:
            await msg.reply(f"您没有权限执行本命令！")
    except:
        _log.exception(f"Au:{msg.author_id} | ERR")
        await msg.reply(f"ERR! [{get_time()}] tkcm\n```\n{traceback.format_exc()}\n```")


# ticket系统,对已完成ticket进行备注
@bot.command(name="tkcm", case_sensitive=False)
async def ticket_commit(msg: Message, tkno: str, *args):
    if not logging(msg):
        return
    if tkno == "":
        await msg.reply(f"请提供ticket的八位数编号，如 000000123")
        return
    elif args == ():
        await msg.reply(f"ticket 备注不得为空！")
        return
    try:
        global TKconf, TKlog
        if not (await user_in_admin_role(msg.ctx.guild.id, msg.author_id)):
            return await msg.reply(f"您没有权限执行本命令！")
        if tkno not in TKlog["data"]:
            return await msg.reply("您输入的ticket编号未在数据库中！")
        if "log_ch_msg_id" not in TKlog["data"][tkno]:  # 工单还没有结束
            return await msg.reply("需要工单结束后，才能对其评论。")

        cmt = " ".join(args)  # 备注信息
        TKlog["data"][tkno]["cmt"] = cmt
        TKlog["data"][tkno]["cmt_usr"] = msg.author_id
        cm = CardMessage()
        c = Card(
            Module.Header(f"工单 ticket.{tkno} 已备注"),
            Module.Context(f"信息更新于 {get_time()}"),
            Module.Divider(),
        )
        text = f"开启时间: {TKlog['data'][tkno]['start_time']}\n"
        text += f"发起用户: (met){TKlog['data'][tkno]['usr_id']}(met)\n"
        text += f"结束时间: {TKlog['data'][tkno]['end_time']}\n"
        text += f"关闭用户: (met){TKlog['data'][tkno]['end_usr']}(met)\n"
        text += "\n"
        text += f"来自 (met){msg.author_id}(met) 的备注:\n> {cmt}"
        c.append(Module.Section(Element.Text(text, Types.Text.KMD)))
        cm.append(c)
        await upd_card(
            bot, TKlog["data"][tkno]["log_ch_msg_id"], cm, channel_type=msg.channel_type
        )
        # 保存到文件
        write_file(TKlogPath, TKlog)
        await msg.reply(f"工单「{tkno}」备注成功！")
        _log.info(f"[Cmt.TK] Au:{msg.author_id} - TkID:{tkno} = {cmt}")
    except:
        _log.exception(f"Au:{msg.author_id} | ERR")
        err_str = f"ERR! [{get_time()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")


@bot.command(name="add_admin_role", aliases=["aar"], case_sensitive=False)
async def ticket_admin_role_add(msg: Message, role="", *arg):
    if not logging(msg):
        return
    if role == "" or "(rol)" not in role:
        return await msg.reply("请提供需要添加的角色：`/aar @角色`")

    global TKconf
    try:
        is_global = "-g" in arg or "-G" in arg  # 判断是否要添加到全局管理员中
        role_id = role.replace("(rol)", "")
        ch_id = msg.ctx.channel.id  # 当前频道id
        if not (await user_in_admin_role(msg.ctx.guild.id, msg.author_id)):
            return await msg.reply(f"您没有权限执行本命令！")
        # 判断是否已经为全局管理员
        if role_id in TKconf["ticket"]["admin_role"]:
            return await msg.reply(
                "这个id已经在配置文件 `TKconf['ticket']['admin_role']`（全局管理员） 中啦！"
            )
        # 判断是否添加为当前频道的管理员（当前频道是否已有ticket
        if not is_global and ch_id not in TKconf["ticket"]["channel_id"]:
            return await msg.reply(
                f"当前频道暂无ticket触发按钮，无法设置当前频道ticket的管理员\n若想设置全局管理员，请在命令末尾添加`-g`参数"
            )

        # 获取这个服务器的已有角色
        guild_roles = await (
            await bot.client.fetch_guild(msg.ctx.guild.id)
        ).fetch_roles()
        _log.info(f"guild roles: {guild_roles}")  # 打印出来做debug
        # 遍历角色id，找有没有和这个角色相同的
        for r in guild_roles:
            # 找到了
            if int(role_id) == r.id:
                if is_global:  # 添加到全局
                    TKconf["ticket"]["admin_role"].append(role_id)
                    await msg.reply(f"成功添加「{role_id}」为全局管理员")
                else:
                    TKconf["ticket"]["channel_id"][ch_id]["admin_role"].append(role_id)
                    await msg.reply(f"成功添加「{role_id}」为当前频道ticket的管理员")
                # 保存到文件
                write_file(TKConfPath, TKconf)
                _log.info(
                    f"[ADD.ADMIN.ROLE] rid:{role_id} | add to TKconf [{is_global}]"
                )
                return
        # 遍历没有找到，提示用户
        await msg.reply(f"添加错误，请确认您提交的是本服务器的角色id")
    except:
        _log.exception(f"Au:{msg.author_id} | ERR")
        err_str = f"ERR! [{get_time()}] tkcm\n```\n{traceback.format_exc()}\n```"
        await msg.reply(f"{err_str}")


######################################### ticket 监看 ###############################################################

TicketOpenLock = asyncio.Lock()
"""开启工单锁"""
TicketCloseLock = asyncio.Lock()
"""工单关闭锁"""

async def ticket_open_event(b: Bot, e: Event):
    """监看工单系统(开启)
    - 相关api文档 https://developer.kaiheila.cn/doc/http/channel#%E5%88%9B%E5%BB%BA%E9%A2%91%E9%81%93
    """
    # 判断是否为ticket申请频道的id（文字频道id）
    global TKconf, TKlog
    try:
        # e.body['target_id'] 是ticket按钮所在频道的id
        # 判断当前频道id是否在执行了ticket命令的频道中
        if e.body["target_id"] in TKconf["ticket"]["channel_id"]:
            loggingE(e, "TK.OPEN")
            # 如果用户已经在键值对里面了，提示，告知无法开启
            if e.body["user_id"] in TKlog["user_pair"]:
                ch = await bot.client.fetch_public_channel(e.body["target_id"])
                no = TKlog["user_pair"][e.body["user_id"]]
                text = f"(met){e.body['user_id']}(met)\n您当前已开启了一个ticket，请在已有ticket频道中留言\n"
                text += f"(chn){TKlog['data'][no]['channel_id']}(chn)"
                cm = CardMessage(
                    Card(Module.Section(Element.Text(text, Types.Text.KMD)))
                )
                await ch.send(cm, temp_target_id=e.body["user_id"])
                _log.info(f"C:{e.body['target_id']} | Au:{e.body['user_id']} | user in tkconf:{no}")
                return
            # 0.先尝试给这个用户发个信息，发不过去，就提示他
            try:
                open_usr = await bot.client.fetch_user(e.body["user_id"])
                send_msg = await open_usr.send(f"您点击了ticket按钮，这是一个私信测试")  # 发送给用户
                ret = await direct_msg_delete(send_msg["msg_id"])  # 删除这个消息
                _log.info(f"[TK.OPEN] pm msg send test success | {ret}")
            except Exception as result:
                if "无法" in str(result) or "屏蔽" in str(result):
                    ch = await bot.client.fetch_public_channel(e.body["target_id"])
                    await ch.send(
                        f"为了保证ticket记录的送达，使用ticket-bot前，需要您私聊一下机器人（私聊内容不限）",
                        temp_target_id=e.body["user_id"],
                    )
                    _log.error(f"ERR! [TK.OPEN] | Au:{e.body['user_id']} = {result}")
                else:
                    raise result
            # 先获取工单的编号
            no = str(TKlog["TKnum"]).rjust(8, "0")
            TKlog["TKnum"] += 1
            # 1.创建一个以开启ticket用户昵称为名字的文字频道
            ret1 = await channel_create(
                e.body["guild_id"],
                TKconf["ticket"]["category_id"],
                f"{no} | {e.body['user_info']['username']}",
            )
            # 2.先设置管理员角色的权限
            # 全局管理员
            for rol in TKconf["ticket"]["admin_role"]:
                # 在该频道创建一个角色权限
                await crole_create(ret1["data"]["id"], "role_id", rol)
                # 设置该频道的角色权限为可见
                await crole_update(ret1["data"]["id"], "role_id", rol, 2048)
                await asyncio.sleep(0.2)  # 休息一会 避免超速
            # 频道管理员
            for rol in TKconf["ticket"]["channel_id"][e.body["target_id"]]["admin_role"]:
                # 在该频道创建一个角色权限
                await crole_create(ret1["data"]["id"], "role_id", rol)
                # 设置该频道的角色权限为可见
                await crole_update(ret1["data"]["id"], "role_id", rol, 2048)
                await asyncio.sleep(0.2)  # 休息一会 避免超速

            # 3.设置该频道的用户权限（开启tk的用户）
            # 在该频道创建一个用户权限
            await crole_create(ret1["data"]["id"], "user_id", e.body["user_id"])
            # 设置该频道的用户权限为可见
            await crole_update(ret1["data"]["id"], "user_id", e.body["user_id"], 2048)

            # 4.在创建出来的频道发送消息
            text = f"(met){e.body['user_id']}(met) 发起了帮助，请等待管理猿的回复\n"
            text += f"工单编号/ID：{no}\n"
            text += f"工单开启时间：{get_time()}\n"
            # 管理员角色id，修改配置文件中的admin_role部分
            for roles_id in TKconf["ticket"]["admin_role"]:
                text += f"(rol){roles_id}(rol) "
            for roles_id in TKconf["ticket"]["channel_id"][e.body["target_id"]][
                "admin_role"
            ]:
                text += f"(rol){roles_id}(rol) "
            text += "\n"
            values_close = json.dumps({"type": TicketBtn.CLOSE,
                                       "channel_id": e.body["target_id"],"user_id": e.body["user_id"],})
            values_lock = json.dumps({"type": TicketBtn.LOCK,
                                "channel_id": e.body["target_id"],"user_id": e.body["user_id"],})
            # 构造卡片
            cm = CardMessage()
            c1 = Card(Module.Section(Element.Text(text, Types.Text.KMD)),Module.Divider())
            text = "帮助结束后，请点击下方“关闭”按钮关闭该ticket频道\n"
            text+= "或使用“锁定”功能，暂时锁定工单（可见,无法发言）"
            c1.append(Module.Section(Element.Text(text, Types.Text.KMD)))
            c1.append(Module.ActionGroup(
                Element.Button("关闭",value=values_close,click=Types.Click.RETURN_VAL,theme=Types.Theme.DANGER),
                Element.Button("锁定",value=values_lock,click=Types.Click.RETURN_VAL,theme=Types.Theme.WARNING)
            ))
            cm.append(c1)
            channel = await bot.client.fetch_public_channel(ret1["data"]["id"])
            sent = await bot.client.send(channel, cm)

            # 5.发送消息完毕，记录消息信息
            TKlog["data"][no] = {
                "usr_id":e.body["user_id"],
                "usr_info":f"{e.body['user_info']['username']}#{e.body['user_info']['identify_num']}",
                "msg_id": sent["msg_id"],
                "channel_id":ret1["data"]["id"],
                "bt_channel_id":e.body["target_id"], # 开启该ticket的按钮所在频道的id
                "start_time":time.time(),
                "lock": False
            }
            # 键值对映射
            TKlog["msg_pair"][sent["msg_id"]] = no  # 键值对，msgid映射ticket编号
            TKlog["user_pair"][e.body["user_id"]] = no  # 用户键值对，一个用户只能创建一个ticket
            TKlog["TKchannel"][ret1["data"]["id"]] = no  # 记录bot创建的频道id，用于消息日志

            # 6.保存到文件
            write_file(TKlogPath, TKlog)
            _log.info(
                f"[TK.OPEN] Au:{e.body['user_id']} - TkID:{no} at {TKlog['data'][no]['start_time']}"
            )
    except:
        _log.exception(f"ERR in TK.OPEN | E:{e.body}")
        err_str = f"ERR! [{get_time()}] TK.OPEN\n```\n{traceback.format_exc()}\n```"
        await debug_ch.send(err_str)
        # 如果出现了错误，就把用户键值对给删了，允许创建第二个
        if e.body["user_id"] in TKlog["user_pair"]:
            _log.info(
                f"Au:{e.body['user_id']} del {TKlog['user_pair'][e.body['user_id']]}"
            )
            del TKlog["user_pair"][e.body["user_id"]]


async def ticket_close_event(b: Bot, e: Event):
    """监看工单关闭情况"""
    try:
        # 避免与tiket申请按钮冲突（文字频道id）
        if e.body["target_id"] in TKconf["ticket"]["channel_id"]:
            _log.info(f"[TK.CLOSE] BTN.CLICK channel_id in TKconf:{e.body['msg_id']}")
            return

        # 判断关闭按钮的卡片消息id是否在以开启的tk日志中，如果不在，则return
        if e.body["msg_id"] not in TKlog["msg_pair"]:
            _log.info(f"[TK.CLOSE] BTN.CLICK msg_id not in TKlog:{e.body['msg_id']}")
            return

        # 基本有效则打印event的json内容
        loggingE(e, "TK.CLOSE")

        # 判断是否为管理员，只有管理可以关闭tk
        no = TKlog["msg_pair"][e.body["msg_id"]]  # 通过消息id获取到ticket的编号
        btn_ch_id = TKlog["data"][no]["bt_channel_id"]  # 开启该ticket的按钮所在频道的id
        if not (
            await user_in_admin_role(e.body["guild_id"], e.body["user_id"], btn_ch_id)
        ):
            temp_ch = await bot.client.fetch_public_channel(e.body["target_id"])
            await temp_ch.send(
                f"```\n抱歉，只有管理员用户可以关闭ticket\n```", temp_target_id=e.body["user_id"]
            )
            _log.info(
                f"[TK.CLOSE] BTN.CLICK by none admin usr:{e.body['user_id']} | C:{e.body['target_id']}"
            )
            return

        # 保存ticket的聊天记录(不在TKMsgLog里面代表一句话都没发)
        if e.body["target_id"] in TKMsgLog["TKMsgChannel"]:
            filename = f"./log/ticket/{TKlog['msg_pair'][e.body['msg_id']]}.json"
            # 保存日志到文件
            write_file(filename, TKMsgLog["data"][e.body["target_id"]])
            del TKMsgLog["data"][e.body["target_id"]]  # 删除日志文件中的该频道
            del TKMsgLog["TKMsgChannel"][e.body["target_id"]]
            _log.info(
                f"[TK.CLOSE] save log msg of {TKlog['msg_pair'][e.body['msg_id']]}"
            )

        # 保存完毕记录后，删除频道
        ret = await delete_channel(e.body["target_id"])
        _log.info(f"[TK.CLOSE] delete channel {e.body['target_id']} | {ret}")

        # 记录信息
        TKlog["data"][no]["end_time"] = time.time()  # 结束时间
        TKlog["data"][no]["end_usr"] = e.body["user_id"]  # 是谁关闭的
        TKlog["data"][no][
            "end_usr_info"
        ] = f"{e.body['user_info']['username']}#{e.body['user_info']['identify_num']}"  # 用户名字
        del TKlog["msg_pair"][e.body["msg_id"]]  # 删除键值对
        del TKlog["user_pair"][TKlog["data"][no]['usr_id']]  # 删除用户键值对
        _log.info(f"[TK.CLOSE] TKlog handling finished | NO:{no}")

        # 发送消息给开启该tk的用户和log频道
        cm = CardMessage()
        c = Card(Module.Header(f"工单 ticket.{no} 已关闭"), Module.Divider())
        text = f"开启时间: {get_time_str_from_stamp(TKlog['data'][no]['start_time'])}\n" # 时间戳转str
        text += f"发起用户: (met){TKlog['data'][no]['usr_id']}(met)\n"
        text += f"结束时间: {get_time()}\n" # 当前时间
        text += f"关闭用户: (met){TKlog['data'][no]['end_usr']}(met)\n"
        c.append(Module.Section(Element.Text(text, Types.Text.KMD)))
        cm.append(c)
        # 预先定义，避免出现私信错误
        log_ch_sent = {"msg_id": "none"}
        log_usr_sent = {"msg_id": "none"}
        try:
            open_usr = await bot.client.fetch_user(TKlog["data"][no]["usr_id"])
            log_usr_sent = await open_usr.send(cm)  # 发送给用户
        except Exception as result:
            if "无法" in str(result) or '屏蔽' in str(result) or 'connect' in str(result):
                _log.warning(f"ERR! [TK.CLOSE] Au:{TKlog['data'][no]['usr_id']} | {result}")
            else:
                raise result

        log_ch_sent = await log_ch.send(cm)  # 发送到频道
        TKlog["data"][no]["log_ch_msg_id"] = log_ch_sent["msg_id"]
        TKlog["data"][no]["log_usr_msg_id"] = log_usr_sent["msg_id"]
        _log.info(
            f"[TK.CLOSE] TKlog msg send finished - ChMsgID:{log_ch_sent['msg_id']} - UMsgID:{log_usr_sent['msg_id']}"
        )

        # 保存到文件
        write_file(TKlogPath, TKlog)
        _log.info(
            f"[TK.CLOSE] Au:{e.body['user_id']} - TkID:{no} at {TKlog['data'][no]['end_time']}"
        )
    except:
        _log.exception(f"ERR in [TK.CLOSE] | E:{e.body}")
        err_str = f"ERR! [{get_time()}] [TK.CLOSE]\n```\n{traceback.format_exc()}\n```"
        await debug_ch.send(err_str)

@bot.on_message()
async def ticket_msg_log(msg: Message):
    """记录ticket频道的聊天记录"""
    try:
        # 判断频道id是否在以开启的tk日志中，如果不在，则return
        if msg.ctx.channel.id not in TKlog["TKchannel"]:
            return
        # TKlog的初始化时间晚于机器人发送关闭按钮的时间，所以机器人发送的第一条消息是不计入的
        # 如果不在TKMsgLog日志中，说明是初次发送消息，则创建键值
        no = TKlog["TKchannel"][msg.ctx.channel.id]
        if msg.ctx.channel.id not in TKMsgLog["TKMsgChannel"]:
            log = {"first_msg_time":time.time(), "msg": {},"msg_num":0}
            TKMsgLog["data"][msg.ctx.channel.id] = log
            TKMsgLog["TKMsgChannel"][msg.ctx.channel.id] = time.time()  # 添加频道，代表该频道有发送过消息

        # 如果在，那么直接添加消息就行
        no = TKMsgLog["data"][msg.ctx.channel.id]["msg_num"] # 编号
        TKMsgLog["data"][msg.ctx.channel.id]["msg"][str(no)] = {
            "msg_id": msg.id,
            "channel_id": msg.ctx.channel.id,
            "user_id": msg.author_id,
            "user_name": f"{msg.author.nickname}#{msg.author.identify_num}",
            "content": msg.content,
            "time_stamp":time.time()
        }
        TKMsgLog["data"][msg.ctx.channel.id]["msg_num"] += 1 # 编号+1
        # 打印日志
        _log.info(
            f"TNO:{no} | Au:{msg.author_id} {msg.author.nickname}#{msg.author.identify_num} = {msg.content}"
        )
    except:
        _log.exception(f"ERR occur | Au:{msg.author_id}")
        err_str = f"ERR! [{get_time()}] log_tk_msg\n```\n{traceback.format_exc()}\n```"
        await debug_ch.send(err_str)

async def get_ticket_lock_card(channel_id:str,tk_user_id:str,btn_user_id:str,header_text=""):
    """获取工单锁定的卡片
    - channel_id: 目标频道
    - tk_user_id:工单用户 
    - btn_user:操作用户
    - header_text: 标题文字
    """
    text = f"进入锁定状态，禁止用户发言\n操作时间：{get_time()}\n"
    text+= f"工单用户：(met){tk_user_id}(met)\n"
    text+= f"操作用户：(met){btn_user_id}(met)"
    values = json.dumps({"type": TicketBtn.REOPEN,
                "channel_id": channel_id,"user_id": tk_user_id})
    cm = CardMessage(Card(Module.Header(header_text),
                        Module.Section(Element.Text(text,Types.Text.KMD),
                                    Element.Button(text="重新激活",value=values))))
    return cm

@bot.task.add_interval(minutes=10)
async def ticket_channel_activate_check():
    """检查日志频道是否活跃。
    超过指定天数没有发送信息的频道，将被机器人关闭
    """
    global TKMsgLog,TKlog
    msg_id = "none"
    try:
        _log.info(f"[BOT.TASK] activate check start")
        # 机器人用户id
        bot_id = (await bot.client.fetch_me()).id
        # 在tklog msg_pair里面的是所有开启ticket的记录
        TKLogTemp = copy.deepcopy(TKlog)
        for msg_id,tkno in TKLogTemp["msg_pair"].items():
            # 如果记录里面有endtime代表工单已被关闭，跳过(保证不出错)
            if 'end_time' in TKlog['data'][tkno]:
                # 报警是因为工单如果被关闭了，应该不会出现在这个循环中
                _log.warning(f"[channel.activate] end_time in {tkno}")
                continue
            # 已经被锁定了，也跳过
            if 'lock' not in TKlog["data"][tkno]:
                TKlog["data"][tkno] = False  # 创建键值为false
            if TKlog["data"][tkno]['lock']:
                continue
            # 获取频道id
            ch_id = TKlog["data"][tkno]['channel_id']
            user_id = TKlog["data"][tkno]['usr_id'] # 开启工单的用户id
            # 获取工单开始时间的时间戳
            ticket_start_time = TKlog['data'][tkno]['start_time']
            assert(isinstance(ticket_start_time,type(time.time()))) # 不能是str
            cur_time = get_time_stamp() # 获取当前时间戳

            # 先构造卡片消息
            cm = await get_ticket_lock_card(ch_id,user_id,bot_id,f"工单超出「{OUTDATE_HOURS}」小时未活动")
            # 超时秒数 =  超时h * 每小时秒数
            outdate_sec = OUTDATE_HOURS * 3600 
            ch = await bot.client.fetch_public_channel(ch_id)
            # 1.如果频道id不在msglog里面，代表一次发言都没有过（机器人发言未计入）
            if ch_id not in TKMsgLog["TKMsgChannel"]:
                time_diff = cur_time-ticket_start_time # 时间插值
                if time_diff >= (outdate_sec):
                    # 超出了超时时间还不发送消息，关闭用户发言权限
                    await crole_update(ch_id, "user_id", user_id, 2048,4096)
                    await ch.send(cm)
                    TKlog["data"][tkno]['lock'] = True
                    _log.info(f"C:{ch_id} Au:{user_id} | empty channel, lock")
                # 两种情况都继续到下一个ticket
                continue

            # 2.走到这里代表有消息，筛选出消息时长最大的那个
            max_time = 0
            for msg_no,msg_info in TKMsgLog["data"][ch_id]['msg'].items():
                time_str = msg_info['time_stamp'] # 消息发送时间
                max_time = int(time_str) if int(time_str) > max_time else max_time
            # 获取到了list中的最大时间，max_time不能为0
            time_diff = cur_time - max_time
            if  max_time == 0 or time_diff >= (outdate_sec):# 超时时间*每小时秒数
                # 超出了超时时间还不发送消息，关闭用户发言权限
                await crole_update(ch_id, "user_id", user_id, 2048,4096)
                await ch.send(cm)
                TKlog["data"][tkno]['lock'] = True
                _log.info(f"C:{ch_id} Au:{user_id} | no msg in {OUTDATE_HOURS}h, lock")
            # 继续执行下一个ticket
            continue
        _log.info(f"[BOT.TASK] activate check end")
    except:
        _log.exception(f"err in task | msg:{msg_id}")


async def ticket_reopen_event(b:Bot,e:Event):
    """重新激活工单"""
    try:
        value = json.loads(e.body['value']) # 导入value
        user_id = value['user_id'] # 开启该工单的用户
        ch_id = value['channel_id'] # 该工单频道
        # 判断开启用户是否在键值对中，不在代表有问题
        if user_id not in TKlog["user_pair"]:
            return _log.warning(f"[TK.REOPEN] Au:{user_id} | C:{ch_id} | user not in pair")
        # 获取工单id
        no = TKlog["user_pair"][user_id] # 用户键值对:id
        # 重新允许用户发言
        await crole_update(ch_id, "user_id", user_id, 4096)
        # 发送信息到该频道
        ch = await bot.client.fetch_public_channel(ch_id)
        c = Card(Module.Header(f"工单「{no}」重新激活"),Module.Divider())
        text = f"重启时间：{get_time()}\n"
        text+= f"重启用户：(met){user_id}(met)\n"
        text+= f"用户ID：  {user_id}\n"
        c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
        await ch.send(CardMessage(c))
        # 修改文件
        TKlog["data"][no]['lock'] = False
        _log.info(f"[TK.REOPEN] Au:{user_id} | C:{ch_id} | success")
    except:
        _log.exception(f"ERR in [TK.REOPEN] | E:{e.body}")

async def ticket_lock_evnet(b:Bot,e:Event):
    """锁定工单（效果和机器人自己扫的效果相同）"""
    try:
        value = json.loads(e.body['value']) # 导入value
        user_id = value['user_id'] # 开启该工单的用户
        ch_id = e.body["target_id"] # 该工单频道
        # 判断开启用户是否在键值对中，不在代表有问题
        if user_id not in TKlog["user_pair"]:
            return _log.warning(f"[TK.LOCK] Au:{user_id} | C:{ch_id} | user not in pair")
        # 获取频道obj
        ch = await bot.client.fetch_public_channel(ch_id)
        # 获取工单id
        no = TKlog["user_pair"][user_id] # 用户键值对:id 
        if TKlog["data"][no]['lock']:# 已经被锁定了
            _log.info(f"[TK.LOCK] Au:{user_id} | C:{ch_id} | already lock")
            return await ch.send(f"(met){user_id}(met) 该工单已锁定，请勿二次操作")
        # 设置用户权限并发送信息
        await crole_update(ch_id, "user_id", user_id, 2048,4096)
        cm = await get_ticket_lock_card(ch_id,user_id,e.body['user_id'],f"工单「{no}」手动锁定")
        await ch.send(cm)
        TKlog["data"][no]['lock'] = True
        _log.info(f"[TK.LOCK] Au:{user_id} | C:{ch_id}")
    except:
        _log.exception(f"ERR in [TK.LOCK] | E:{e.body}")

@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn_click_event_watch(b:Bot,e:Event):
    """通过按钮的value，分选给各个函数"""
    try:
        value = json.loads(e.body['value']) # 导入value
        btn_type = value['type'] # 按钮类型
        
        if btn_type == TicketBtn.OPEN:
            global TicketOpenLock  # 同一时间只允许创建一个tk
            async with TicketOpenLock:
                _log.info(f"[TK.OPEN] Au:{e.body['user_id']} C:{e.body['target_id']}")
                await ticket_open_event(b,e)
        elif btn_type == TicketBtn.CLOSE:
            global TicketCloseLock # 同一时间只允许一个tk关闭
            async with TicketCloseLock:
                _log.info(f"[TK.CLOSE] Au:{e.body['user_id']} C:{e.body['target_id']}")
                await ticket_close_event(b,e)
        elif btn_type == TicketBtn.REOPEN:
            _log.info(f"[TK.REOPEN] Au:{e.body['user_id']} C:{e.body['target_id']}")
            await ticket_reopen_event(b,e)
        elif btn_type == TicketBtn.LOCK:
            _log.info(f"[TK.LOCK] Au:{e.body['user_id']} C:{e.body['target_id']}")
            await ticket_lock_evnet(b,e)
        else:
            _log.warning(f"invalied value.type | {e.body}")
    except:
        _log.exception(f"err in event watch | {e.body}")


################################以下是给用户上色功能的内容########################################

# 只有emoji的键值在配置文件中存在，才启用监看
# 否则不加载这个event，节省性能
if EMOJI_ROLES_ON:
    from utils.cmd.grantRoles import grant_role_event
    _log.info(f"[BOT.ON_EVENT] loading ADDED_REACTION")
    # 添加event监看
    @bot.on_event(EventTypes.ADDED_REACTION)
    async def grant_role(b: Bot, event: Event):
        await grant_role_event(b, event)
        # 如果想获取emoji的样式，比如频道自定义emoji，就需要在这里print
        # print(event.body)

##########################################################################################


# 定时保存log file
@bot.task.add_interval(minutes=5)
async def log_file_save_task():
    try:
        await write_all_files()
        _log.info(f"[FILE.SAVE.TASK] file saved")
        logFlush()  # 刷新缓冲区
    except:
        _log.exception(f"[FILE.SAVE] err")


# kill命令安全退出
@bot.command(name="kill", case_sensitive=False)
async def kill(msg: Message, atbot="", *arg):
    try:
        logging(msg)
        if not (await user_in_admin_role(msg.ctx.guild.id, msg.author_id)):
            return
        cur_bot = await bot.client.fetch_me()
        if f"(met){cur_bot.id}(met)" not in atbot:
            return await msg.reply(f"为了保证命令唯一性，执行本命令必须at机器人！`/kill @机器人`")

        await write_all_files()
        # 发送信息提示
        await msg.reply(f"[KILL] bot exit")
        # 如果是webscoket才调用下线接口
        res = "webhook"
        if Botconf["ws"]:
            res = await bot_offline()  # 调用接口下线bot
        _log.info(
            f"[KILL] [{get_time()}] Au:{msg.author_id} | bot-off: {res}\n"
        )  # 打印下线日志
        logFlush()  # 刷新缓冲区
        os._exit(0)  # 进程退出
    except:
        _log.exception(f"kill err")
        await msg.reply(f"kill err\n```\n{traceback.format_exc()}\n```")

# 开机任务
@bot.on_startup
async def loading_channel(b:Bot):
    try:
        global debug_ch, log_ch
        debug_ch = await bot.client.fetch_public_channel(
            TKconf["ticket"]["debug_channel"]
        )
        log_ch = await bot.client.fetch_public_channel(TKconf["ticket"]["log_channel"])
        _log.info(f"[BOT.START] fetch_public_channel success")
        botStatus.init(bot)  # 机器人动态相关命令
        logFlush()  # 刷新缓冲区
    except:
        _log.exception(f"[BOT.START] fetch_public_channel failed")
        _log.critical("[BOT.START] 获取频道失败，请检查TicketConf文件中的debug_channel和log_channel\n")
        logFlush()  # 刷新缓冲区
        os.abort()  # 出现错误直接退出程序


# 如果是主文件就开机
if __name__ == "__main__":
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start at {start_time}")
    # 开机
    bot.run()
