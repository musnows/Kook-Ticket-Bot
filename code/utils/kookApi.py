import json
import aiohttp
from typing import Union
from khl import  Bot,ChannelPrivacyTypes
from .file import Botconf
from .myLog import _log

# kook api的头链接，请不要修改
kook_base="https://www.kookapp.cn"
"""kook api base url"""
kook_headers={f'Authorization': f"Bot {Botconf['token']}"}
"""kook api base headers"""


# 让机器人开始打游戏
async def status_active_game(game:int):
    url="https://www.kookapp.cn/api/v3/game/activity"
    params = {"id": game ,"data_type":1}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=kook_headers) as response:
                return json.loads(await response.text())

# 让机器人开始听歌
async def status_active_music(name:str,singer:str):
    url="https://www.kookapp.cn/api/v3/game/activity"
    params = {"data_type":2,"software":"qqmusic","singer":singer,"music_name":name}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=kook_headers) as response:
                return json.loads(await response.text())


# 删除机器人的当前动态
async def status_delete(d:int):
    url="https://www.kookapp.cn/api/v3/game/delete-activity"
    params = {"data_type":d}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=kook_headers) as response:
                return json.loads(await response.text())
                #_log.debug(ret)

#更新卡片消息
async def upd_card(bot:Bot,msg_id: str,
                   content,
                   target_id='',
                   channel_type: Union[ChannelPrivacyTypes, str] = 'public'):
    content = json.dumps(content)
    data = {'msg_id': msg_id, 'content': content}
    if target_id != '':
        data['temp_target_id'] = target_id
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
        result = await bot.client.gate.request('POST', 'message/update', data=data)
    else:
        result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
    return result

# 判断用户是否拥有管理员权限
async def has_admin(bot:Bot,user_id:str, guild_id:str):
    guild = await bot.client.fetch_guild(guild_id)
    user_roles = (await guild.fetch_user(user_id)).roles
    guild_roles = await (await bot.client.fetch_guild(guild_id)).fetch_roles()
    for i in guild_roles:  # 遍历服务器身分组
        if i.id in user_roles and i.has_permission(0):  # 查看当前遍历到的身分组是否在用户身分组内且是否有管理员权限
            return True
    if user_id == guild.master_id: # 由于腐竹可能没给自己上身分组，但是依旧拥有管理员权限
        return True
    return False


# 创建文字频道
async def channel_create(guild_id:str,parent_id:str,name:str):
    url1=kook_base+"/api/v3/channel/create"# 创建频道
    params1 = {"guild_id": guild_id ,"parent_id":parent_id,"name":name}
    async with aiohttp.ClientSession() as session:
        async with session.post(url1, data=params1,headers=kook_headers) as response:
                ret1=json.loads(await response.text())
                #_log.debug(ret1["data"]["id"])
    return ret1

# 创建角色权限
async def crole_create(channel_id:str,_type:str,_value:str):
    """
        type: user_id / role_id
        value: base on type
    """
    url2=kook_base+"/api/v3/channel-role/create"#创建角色权限
    params2 = {"channel_id": channel_id ,"type":_type,"value":_value}
    async with aiohttp.ClientSession() as session:
        async with session.post(url2, data=params2,headers=kook_headers) as response:
                ret2=json.loads(await response.text())
                #_log.debug(f"ret2: {ret2}")
    return ret2


# 设置角色权限
async def crole_update(channel_id:str,_type:str,_value:str,_allow:int):
    """服务器角色权限值见 https://developer.kaiheila.cn/doc/http/guild-role
    - type: user_id / role_id
    - value: base on type
    """
    url3=kook_base+"/api/v3/channel-role/update"#设置角色权限
    params3 = {"channel_id": channel_id ,"type":_type,"value":_value,"allow":_allow}
    async with aiohttp.ClientSession() as session:
        async with session.post(url3, data=params3,headers=kook_headers) as response:
                ret3=json.loads(await response.text())
                _log.debug(ret3)
    return ret3

# 下线机器人
async def bot_offline():
    url = kook_base + "/api/v3/user/offline"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=kook_headers) as response:
            res = json.loads(await response.text())
    return res
