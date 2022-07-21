# Kook-Ticket-Bot
A ticket bot for KOOK  表单系统机器人

工作流程
* 当用户B点击卡片消息的按钮后，创建一个只有用户B可见的文字频道
* Bot会自动在该临时频道发送一条消息，并`@用户B` 和处理表单的 `@管理员`
* 当处理完毕后，点击`关闭`按钮，Bot会删除该文字频道

附加功能
* 通过表情回应给用户添加对应角色

## Requerments
you need to `pip install` pakages before using this bot
```
pip install khl.py
pip install requests
```

## Config
### 1.bot token
在 `code/config`路径中添加`config.json`，并在里面填入以下内容来初始化你的Bot
```
{
    "token": " YOUR BOT TOKEN HERE ",
    "verify_token": "",
    "encrypt_key": ""
}
```
### 2.ListTK
在`code/main.py`的`L29-30`可以看到下面这两个全局变量
```python
ListTK = ['4794121363928781','7843220427378656','0'] # ticket申请按钮的文字频道id
Category_ID = '8267613700948160' #被隐藏的分组id 
```
这两个分别是申请ticket的文字频道，和bot创建临时文字频道的隐藏分组id（设置该分组权限为`@全体成员->分组不可见`来隐藏）

下面是ticket功能的示例图

<img src="./screenshots/tk1.png" wight="300px" height="130px">

<img src="./screenshots/tk2.png" wight="350px" height="220px">

----

### 3.emoji/role
如果你想使用通过表情回应来上角色的功能，则还需要添加 `code/config/emoji.txt`

举个栗子：emoji_id 🎙 对应 role_id `4779921`，则需要在`emoji.txt`中写入下面内容
```
🎙:4779921
```
bot会根据emoji_id给用户上对应的角色

<img src="./screenshots/role2.png" wight="250px" height="160px">

<img src="./screenshots/role1.png" wight="350px" height="210px">

看`L109-113`，我设置了3个不同的 Msg_ID 给 `add_reaction event`，因为需要设置不同分类的角色
```
# 设置自动上色event的服务器id和消息id
Guild_ID = '1573724356603748'
Msg_ID_1 = '0a4b9403-de0b-494e-b216-3d1dbe957d0f'
Msg_ID_2 = '5d92f952-15c1-46a4-b370-41a9cf739e50'
Msg_ID_3 = 'd4dbb164-bd80-469b-9473-8285a9c91e0d'
```
对应的，判断函数也被分为了3个不同的情况。你可以根据你的实际需要修改/弃用一部分代码。

同时，`L115-170`则是3个不同的idsave文件，用来保存已经领取过角色的用户。这样设计可以让每一个用户只能在一个Msg_ID下领取其中一个角色。避免刷角色的情况。

<img src="./screenshots/role3.png" wight="200px" height="110px">

>更多代码示例，请查看`code/main.py` 的 `L192-L270`

## The end
有任何问题，请添加`issue`，或加入我的交流服务器与我联系 [kook邀请链接](https://kook.top/gpbTwZ)

如果你觉得本项目还不错，还请高抬贵手点个star✨，万般感谢！

