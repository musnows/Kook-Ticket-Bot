import json
import time
import aiohttp

from typing import Union
from khl import  Bot,Message,ChannelPrivacyTypes
from khl.card import Card, CardMessage, Element, Module, Types


with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
bot = Bot(token=config['token'])
Botoken=config['token']


# 让机器人开始打游戏
async def status_active_game(game:int):
    url="https://www.kookapp.cn/api/v3/game/activity"
    headers={f'Authorization': f"Bot {Botoken}"}
    params = {"id": game ,"data_type":1}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=headers) as response:
                return json.loads(await response.text())

# 让机器人开始听歌
async def status_active_music(name:str,singer:str):
    url="https://www.kookapp.cn/api/v3/game/activity"
    headers={f'Authorization': f"Bot {Botoken}"}
    params = {"data_type":2,"software":"qqmusic","singer":singer,"music_name":name}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=headers) as response:
                return json.loads(await response.text())


# 删除机器人的当前动态
async def status_delete(d:int):
    url="https://www.kookapp.cn/api/v3/game/delete-activity"
    headers={f'Authorization': f"Bot {Botoken}"}
    params = {"data_type":d}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=headers) as response:
                return json.loads(await response.text())
                #print(ret)

#更新卡片消息
async def upd_card(msg_id: str,
                   content,
                   target_id='',
                   channel_type: Union[ChannelPrivacyTypes, str] = 'public',
                   bot=bot):
    content = json.dumps(content)
    data = {'msg_id': msg_id, 'content': content}
    if target_id != '':
        data['temp_target_id'] = target_id
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
        result = await bot.client.gate.request('POST', 'message/update', data=data)
    else:
        result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
    return result