import traceback
from khl import Event,Bot,Channel

from .file import ColorIdDict,ColorIdPath,write_file,_log,TKconf

async def save_userid_color(userid: str, emoji: str, uid: str):
    """用于记录使用表情回应获取ID颜色的用户
    
    Args:
    - userid: kook-user-id
    - emoji: emoji id
    - uid: str in TKconf['emoji']

    Return:
    - True:  old user
    - False: new user
    """
    global ColorIdDict
    flag = True
    # 如果键值不在，创建键值，代表之前没有获取过角色
    if uid not in ColorIdDict["data"]:
        ColorIdDict["data"][uid] = {}
        flag = False
    # 更新键值
    ColorIdDict["data"][uid][userid] = emoji
    # 如果用户是第一次添加表情回应，那就写入文件
    if flag:
        write_file(ColorIdPath, ColorIdDict)
    return flag


# 给用户上角色
async def grant_role_event(bot: Bot, event: Event,debug_ch:Channel,guild_id:str):
    """判断消息的emoji回应，并给予不同角色"""
    ch = debug_ch
    try:
        # 将event.body的msg_id和配置文件中msg_id进行对比，确认是那一条消息的表情回应
        for euid, econf in TKconf["emoji"].items():
            if event.body["msg_id"] != econf["msg_id"]:
                continue
            # 1.这里的打印eventbody的完整内容，包含emoji_id
            _log.info(f"React:{event.body}")
            # 2.获取对象
            g = await bot.client.fetch_guild(guild_id)  # 获取服务器（msg_id合法才获取，避免多次无效调用api）
            ch = await bot.client.fetch_public_channel(
                event.body["channel_id"]
            )  # 获取事件频道
            user = await g.fetch_user(event.body["user_id"])  # 通过event获取用户id(对象)
            # 3.判断用户回复的emoji是否合法
            emoji = event.body["emoji"]["id"]
            if emoji not in econf["data"]:  # 不在配置文件中，忽略
                return await ch.send(
                    f"你回应的表情不在列表中哦~再试一次吧！", temp_target_id=event.body["user_id"]
                )

            # 4.判断用户之前是否已经获取过角色
            ret = await save_userid_color(
                event.body["user_id"], event.body["emoji"]["id"], euid
            )
            text = f"「{user.nickname}#{user.identify_num}」Bot已经给你上了 「{emoji}」 对应的角色啦~"
            if ret:  # 已经获取过角色
                text += "\n上次获取的角色已删除"
            # 5.给予角色
            role = int(econf["data"][emoji])  # 角色id
            await g.grant_role(user, role)  # 上角色
            # 6.发送提示信息给用户
            await ch.send(text, temp_target_id=event.body["user_id"])
            _log.info(f"Au:{user.id} | grant rid:{role}")
    except Exception as result:
        _log.exception(f"ERR | E:{event.body}")
        err_text = (
            f"上角色时出现了错误！Au:{event.body['user_id']}\n```\n{traceback.format_exc()}\n```"
        )
        if ch != debug_ch:
            await ch.send(err_text, temp_target_id=event.body["user_id"])
        else:
            await ch.send(err_text)