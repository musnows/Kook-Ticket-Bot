# encoding: utf-8:
import json
import aiohttp
import time
# import requests

from khl import Bot, Message, EventTypes, Event, Client, PublicChannel, PublicMessage
from khl.card import CardMessage, Card, Module, Element, Types, Struct
import khl.task

# 本bot是另外一个仓库↓的bm-bot的特殊版本，和tiket系统无关
# https://github.com/Aewait/Kook-BattleMetrics-Bot
# 放入这里是为了方便部署+版本管理
# this bot has nothing to do with the tiket-bot,just put here for deploying

###########################################################################################################

with open('../config/bm_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 用读取来的 config 初始化 bot，字段对应即可
bot = Bot(token=config['token'])

# kook api的头链接，请不要修改
dad="https://www.kookapp.cn"
Botoken = config['token']
headers={f'Authorization': f"Bot {Botoken}"}

# 在控制台打印msg内容，用作日志
def logging(msg: Message):
    now_time = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{now_time}] G:{msg.ctx.guild.id} - C:{msg.ctx.channel.id} - Au:{msg.author_id}_{msg.author.username}#{msg.author.identify_num} - content:{msg.content}")

###########################################################################################################

# `/hello`指令，一般用于测试bot是否成功上线
@bot.command(name='hello')
async def world(msg: Message):
    logging(msg)
    await msg.reply('world!')
    

# 检查指定服务器并更新
async def ServerCheck():
    #logging(msg)
    url = f"https://api.battlemetrics.com/servers?filter[search]=特雷森学园&filter[game]=hll"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ret1 = json.loads(await response.text())
            #print(ret1)
    for server in ret1['data']:
        if server['id'] == "15701757":  #指定服务器id
            print(f"\nGET: {server}\n")
            # 确认状态情况
            emoji = ":green_circle:"
            if server['attributes']['status'] != "online":
                emoji = ":red_circle:"

            cm = CardMessage()
            c = Card(
                Module.Section(
                    Element.Text(f"{server['attributes']['name']}",
                                 Types.Text.KMD),
                    Element.Image(
                        src="https://s1.ax1x.com/2022/07/24/jXqRL8.png",
                        circle=True,
                        size='sm'),
                    mode='right'))
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


# 手动显示指定服务器的信息
@bot.command()
async def card(msg:Message):
    logging(msg)
    cm= await ServerCheck()
    await msg.reply(cm)

# 用来保存定时发出的卡片消息
Msg_ID = "3e51fb86-1bfc-40dc-9ce1-a8bd696fa694"

# 手动更改全局变量中的msgid
@bot.command()
async def Change_MSG(msg:Message,id:str):
    logging(msg)
    global Msg_ID
    Msg_ID = id

# 自动更新
@bot.task.add_interval(minutes=20)
async def update_Server():
    global Msg_ID
    cm = await ServerCheck()
    channel = await bot.fetch_public_channel("5792016130690641")
    sent = await bot.send(channel,cm)

    now_time = time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

    url = dad+"/api/v3/message/delete"#删除旧的服务器信息
    params = {"msg_id":Msg_ID}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=params,headers=headers) as response:
                ret=json.loads(await response.text())
                print(f"[{now_time}] Delete:{ret['message']}")#打印删除信息的返回值

    Msg_ID = sent['msg_id']# 更新msg_id
    print(f"[{now_time}] SENT_MSG_ID:{sent['msg_id']}")


# 查询服务器信息
@bot.command()
async def check(msg: Message, name: str, game: str, max: int = 3):
    logging(msg)
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



bot.run()