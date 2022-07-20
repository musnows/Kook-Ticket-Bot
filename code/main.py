# encoding: utf-8:
import json
from unicodedata import category
import requests
import aiohttp

from khl import Bot, Message, EventTypes, Event,Client,PublicMessage
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from khl.command import Rule

# 新建机器人，token 就是机器人的身份凭证
with open('./config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 用读取来的 config 初始化 bot，字段对应即可
bot = Bot(token=config['token'])

# kook api的头链接，请不要修改
dad="https://www.kookapp.cn"
Botoken = config['token']
headers={f'Authorization': f"Bot {Botoken}"}


# `/hello`指令，一般用于测试bot是否成功上线
@bot.command(name='hello')
async def world(msg: Message):
    await msg.reply('world!')

################################以下是给ticket功能的内容########################################

Txt_ID = '5792016130690641' # ticket申请按钮的文字频道id
Category_ID = '5707984316635077' #被隐藏的分组id 

# ticket系统,发送卡片消息
@bot.command()
async def ticket(msg: Message):
    await msg.ctx.channel.send(
        CardMessage(
            Card(Module.Section(
                    '请点击右侧按钮发起ticket',
                    Element.Button('发起ticket',Types.Click.RETURN_VAL)))))

# 监看工单系统
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def print_btn(b: Bot, e: Event):
    # 判断是否为ticket申请频道的id（文字频道id）
    if e.body['target_id'] != Txt_ID:
        return 
    print(e.body)
    global dad,headers
    url1=dad+"/api/v3/channel/create"#创建频道
    params1 = {"guild_id": e.body['guild_id'] ,"parent_id":"5707984316635077","name":e.body['user_info']['username']}
    async with aiohttp.ClientSession() as session:
        async with session.post(url1, data=params1,headers=headers) as response:
                ret1=json.loads(await response.text())
                #print(ret1["data"]["id"])

    url2=dad+"/api/v3/channel-role/create"#创建角色权限
    params2 = {"channel_id": ret1["data"]["id"] ,"type":"user_id","value":e.body['user_id']}
    async with aiohttp.ClientSession() as session:
        async with session.post(url2, data=params2,headers=headers) as response:
                ret2=json.loads(await response.text())
                #print(f"ret2: {ret2}")
    
    url3=dad+"/api/v3/channel-role/update"#设置角色权限
    params3 = {"channel_id": ret1["data"]["id"] ,"type":"user_id","value":e.body['user_id'],"allow":2048}
    async with aiohttp.ClientSession() as session:
        async with session.post(url3, data=params3,headers=headers) as response:
                ret3=json.loads(await response.text())
                #print(f"ret3: {ret3}")
    
    cm = CardMessage()
    c1 = Card(Module.Section(Element.Text(f"(met){e.body['user_id']}(met) 发起了帮助，请等待管理猿的回复\n(rol)4693884(rol)\n",Types.Text.KMD)))
    c1.append(Module.Section('帮助结束后，请点击下方“关闭”按钮关闭该ticket频道\n'))
    c1.append(Module.ActionGroup(Element.Button('关闭', Types.Click.RETURN_VAL,theme=Types.Theme.DANGER)))
    cm.append(c1)
    channel = await b.fetch_public_channel(ret1["data"]["id"]) 
    sent = await bot.send(channel,cm)
    return sent

# 监看关闭情况
@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def btn_close(b: Bot, e: Event):
    # 避免与tiket申请按钮冲突（文字频道id）
    if e.body['target_id'] == Txt_ID:
        return 
    
    global dad,headers
    url1=dad+"/api/v3/channel/view"#获取频道的信息
    params1 = {"target_id": e.body['target_id']}
    async with aiohttp.ClientSession() as session:
        async with session.post(url1, data=params1,headers=headers) as response:
                ret1=json.loads(await response.text())
    #判断发生点击事件的频道是否在预定分组下，如果不是就不进行操作
    if ret1['data']['parent_id'] != Category_ID:
        return 

    url2=dad+'/api/v3/channel/delete'#删除频道
    params2 = {"channel_id": e.body['target_id']}
    async with aiohttp.ClientSession() as session:
        async with session.post(url2, data=params2,headers=headers) as response:
                ret2=json.loads(await response.text())
                #print(ret2)
    
################################以下是给用户上色功能的内容########################################

# 设置自动上色event的服务器id和消息id
Guild_ID = '3280131482359624'
Msg_ID_1 = 'd244b380-0451-46fd-b7d2-263640813974'
Msg_ID_2 = 'd244b380-0451-46fd-b7d2-263640813974'

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
     

# # 在不修改代码的前提下设置上色功能的服务器和监听消息
@bot.command()
async def Set_GM(msg: Message,d:int,Card_Msg_id:str):
    global Guild_ID,Msg_ID_1,Msg_ID_2 #需要声明全局变量
    Guild_ID = msg.ctx.guild.id
    if d == 1:
        Msg_ID_1 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息1更新为 {Msg_ID_1}\n')
    elif d == 2:
        Msg_ID_2 = Card_Msg_id
        await msg.reply(f'监听服务器更新为 {Guild_ID}\n监听消息2更新为 {Msg_ID_2}\n')



# 判断消息的emoji回应，并给予不同角色
@bot.on_event(EventTypes.ADDED_REACTION)
async def update_reminder(b: Bot, event: Event):
    g = await b.fetch_guild(Guild_ID)# 填入服务器id
    #print(event.body)# 这里的打印eventbody的完整内容，包含emoji_id

    #将msg_id和event.body msg_id进行对比，确认是我们要的那一条消息的表情回应
    #第一个设置
    if event.body['msg_id'] == Msg_ID_1:
        channel = await b.fetch_public_channel(event.body['channel_id']) #获取事件频道
        s = await b.fetch_user(event.body['user_id'])#通过event获取用户id(对象)
        # 判断用户回复的emoji是否合法
        emoji=event.body["emoji"]['id']
        flag=0
        with open("./config/emoji1.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 1, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        #await g.grant_role(s,role)
                        await b.send(channel, f'bot已经给你上了 {emoji} 对应的角色',temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])
    
    # 第二个设置
    elif event.body['msg_id'] == Msg_ID_2:
        channel = await b.fetch_public_channel(event.body['channel_id']) #获取事件频道
        s = await b.fetch_user(event.body['user_id'])#通过event获取用户id(对象)
        # 判断用户回复的emoji是否合法
        emoji=event.body["emoji"]['id']
        flag=0
        with open("./config/emoji2.txt", 'r',encoding='utf-8') as fr1:
            lines=fr1.readlines()
            for line in lines:
                v = line.strip().split(':')
                if emoji == v[0]:
                    flag=1 #确认用户回复的emoji合法 
                    ret = save_userid_color(event.body['user_id'], 2, event.body["emoji"]['id'])# 判断用户之前是否已经获取过角色
                    if ret ==1: #已经获取过角色
                        await b.send(channel,f'你已经设置过你的角色，修改请联系管理。',temp_target_id=event.body['user_id'])
                        fr1.close()
                        return
                    else:
                        role=int(v[1])
                        #await g.grant_role(s,role)
                        await b.send(channel, f'bot已经给你上了 {emoji} 对应的角色',temp_target_id=event.body['user_id'])
        fr1.close()
        if flag == 0: #回复的表情不合法
            await b.send(channel,f'你回应的表情不在列表中哦~再试一次吧！',temp_target_id=event.body['user_id'])




# 给用户上色（在发出消息后，机器人自动添加回应）
@bot.command()
async def Color_Set(msg: Message):
    cm = CardMessage()
    c1 = Card(Module.Header('在下面添加回应，来设置你的角色吧！'), Module.Context('更多角色等待上线...'))
    c1.append(Module.Divider())
    c1.append(Module.Section('「:pig:」粉色  「:heart:」红色\n「:black_heart:」黑色  「:yellow_heart:」黄色\n'))
    c1.append(Module.Section('「:blue_heart:」蓝色  「:purple_heart:」紫色\n「:green_heart:」绿色  「:+1:」默认\n'))
    cm.append(c1)
    sent = await msg.ctx.channel.send(cm) #接受send的返回值
    # 自己new一个msg对象    
    setMSG=PublicMessage(
        msg_id= sent['msg_id'],
        _gate_ = msg.gate,
        extra={'guild_id': msg.ctx.guild.id,'channel_name': msg.ctx.channel,'author':{'id': bot.me.id}}) 
        # extra部分留空也行
    # 让bot给卡片消息添加对应emoji回应
    with open("./config/color_emoji.txt", 'r',encoding='utf-8') as fr1:
        lines = fr1.readlines()   
        for line in lines:
            v = line.strip().split(':')
            await setMSG.add_reaction(v[0])
    fr1.close()


# 凭证传好了、机器人新建好了、指令也注册完了
# 接下来就是运行我们的机器人了，bot.run() 就是机器人的起跑线
bot.run()