# encoding: utf-8:
import json
import aiohttp
import time
# import requests

from khl import Bot, Message, EventTypes, Event
from khl.card import CardMessage, Card, Module, Element, Types, Struct

# 本bot是另外一个仓库↓的bm-bot的特殊版本，和tiket系统无关
# https://github.com/Aewait/Kook-BattleMetrics-Bot
# 放入这里是为了方便部署+版本管理
# this bot has nothing to do with the tiket-bot,just put here for deploying


# kook api的头链接，请不要修改
dad="https://www.kookapp.cn"


# 检查指定服务器并更新
async def ServerCheck():
    url = f"https://api.battlemetrics.com/servers?filter[search]=特雷森学园&filter[game]=hll"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret1 = json.loads(await response.text())
            #print(ret1)
    for server in ret1['data']:
        if server['id'] == "15701757":  #指定服务器id
            print(f"\nGET: {server}\n")
            # 确认状态情况（依据玩家数量进行判断）
            emoji = ":green_circle:"
            if server['attributes']['players'] == 0:
                emoji = ":red_circle:"

            cm = CardMessage()
            c = Card(
                Module.Section(
                    Element.Text(f"{server['attributes']['name']}",
                                 Types.Text.KMD),
                    Element.Image(
                        src="https://s1.ax1x.com/2022/07/24/jXqRL8.png",
                        circle=True,
                        size='sm')))
            c.append(Module.Divider())
            c.append(
                Module.Section(
                    Struct.Paragraph(
                        3,
                        Element.Text(
                            f"**状态 **\n" + f"{emoji}" + "   \n" + "**地图 **\n" +
                            f"{server['attributes']['details']['map']}",
                            Types.Text.KMD),
                        Element.Text(
                            f"**服务器ip \n**" + f"{server['attributes']['ip']}" +
                            "     \n" + "**rank **\n" +
                            f"#{server['attributes']['rank']}",
                            Types.Text.KMD),
                        Element.Text(
                            f"**当前地区 \n**" +
                            f"{server['attributes']['country']}" + "    \n" +
                            "**Players **\n"
                            f"{server['attributes']['players']}/{server['attributes']['maxPlayers']}",
                            Types.Text.KMD))))
            cm.append(c)
            #await msg.reply(cm)
            return cm


# 查询服务器信息
async def Search(msg: Message, name: str, game: str, max:int):
    url = f'https://api.battlemetrics.com/servers?filter[search]={name}&filter[game]={game}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret = json.loads(await response.text())

    count = 1
    cm = CardMessage()
    for server in ret['data']:
        if count > max:
            break  #默认只显示前3个结果

        emoji = ":green_circle:"
        if server['attributes']['status'] != "online":
            emoji = ":red_circle:"
        c = Card(Module.Header(f"{server['attributes']['name']}"))
        c.append(Module.Divider())
        c.append(
            Module.Section(
                Struct.Paragraph(
                    3,
                    Element.Text(
                        f"**状态 **\n" + f"{emoji}" + "   \n" + "**地图 **\n" +
                        f"{server['attributes']['details']['map']}",
                        Types.Text.KMD),
                    Element.Text(
                        f"**服务器ip \n**" + f"{server['attributes']['ip']}" +
                        "     \n" + "**rank **\n" +
                        f"#{server['attributes']['rank']}", Types.Text.KMD),
                    Element.Text(
                        f"**当前地区 \n**" + f"{server['attributes']['country']}" +
                        "    \n" + "**Players **\n"
                        f"{server['attributes']['players']}/{server['attributes']['maxPlayers']}",
                        Types.Text.KMD))))
        cm.append(c)
        count += 1

    await msg.reply(cm)

