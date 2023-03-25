# Kook-Ticket-Bot

![commit](https://img.shields.io/github/last-commit/musnows/Kook-Ticket-Bot) ![release](https://img.shields.io/github/v/release/musnows/Kook-Ticket-Bot)


A ticket bot for KOOK, **自托管**表单/工单系统机器人

工作流程
* 当用户B点击卡片消息的按钮后，创建一个只有用户B可见的文字频道
* Bot会自动在该临时频道发送一条消息，并`@用户B` 和处理表单的 `@管理员`
* 当处理完毕后，点击`关闭`按钮，Bot会删除该文字频道
* 文字频道删除后，Bot会给预先`设置好的log频道`和`开启ticket的用户`发送一条记录信息，并在服务器后端保存该ticket的聊天记录；
* 管理员可以使用`/tkcm`命令，指定ticket编号对该工单发表评论

附加功能
* 通过表情回应给用户添加对应角色
* 设置Bot动态 `游戏/音乐`

本README尽量详细，争取让没有写过python代码，但了解基本编程环境搭建的用户能配置成功并正常使用bot！

> 无须服务器和环境搭建，在replit上部署本bot！[WIKI教程](https://github.com/musnows/Kook-Ticket-Bot/wiki)

如果您对本README还有完善的建议，十分欢迎您[加入KOOK帮助频道](https://kook.top/gpbTwZ)与我联系，亦或者在仓库提出issue

## help command

Bot的帮助命令为 `/tkhelp`，`@Bot`也能触发帮助命令

```python
# help命令的内容
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
```

## Requerments

使用本机器人之前，请先确认您的python版本高于`3.7`, 安装以下依赖项

```
pip install -r reqiurements.txt
```

完成下方的配置后，就可以运行bot了 (注意 工作路径是code目录)

```
python main.py
```
如果是linux系统需要bot后台运行，使用如下命令

```
nohup python -u main.py >> ./log/bot.log 2>&1 &
```


## Config

因为bot开机的时候就会打开下面的文件，若缺少字段，会影响bot的正常运行；

目前在 [code/utils.py](./code/utils.py) 的底部打开了所有的配置文件，并添加了 `create_logFile()` 函数来自动创建不存在的配置文件，以下README中对配置文件的示例仅供参考，若运行后出现了自动创建文件失败的报错，请采用REAMDE中的描述手动创建配置文件！

### 1.bot token
在 `code/config`路径中添加`config.json`，并在里面填入以下内容来初始化你的Bot

```json
{
    "token": "kook-bot websocket token"
}
```

### 2.TicketConfig

在 `code/config`路径中新增`TicketConf.json`，并填入以下内容（注意，这里的键值都不能修改）

```json
{
  "guild_id":"ticket bot 所服务的服务器id",
  "ticket": {
    "admin_role": [
      "管理员角色id 1",
      "管理员角色id 2"
    ],
    "category_id": "隐藏掉的频道分组id",
    "channel_id": {},
    "log_channel": "用于发送ticket日志的文字频道id",
    "debug_channel": "用于发送bot出错信息的文字频道id"
  }
}
```
ticket机器人需要您创建一个对全体成员不可见的隐藏分组，设置该分组权限为`@全体成员->分组不可见`来隐藏；并给管理员角色设置权限，让管理员能看到这个分组。

`admin_role`中的管理员角色，即为机器人发送的ticket消息中会`@`的角色组；且只有拥有管理员身份组的用户，才能`关闭ticket/给ticket写评论`。

<img src="./screenshots/tk2.png" wight="350px" height="220px" alt="bot发送附带关闭按钮的卡片">

#### 关于命令权限问题

> id获取办法：`kook设置-高级设置-打开开发者模式`；右键服务器头像，复制服务器id；右键用户头像即可复制用户id，右键频道/分组即可复制频道/分组id。

只有拥有`admin_role`中角色的用户才能操作bot的管理命令。

举例：服务器有个`摸鱼`角色，如果你想让**张三**可以操作bot的管理命令，那就需要给**张三**添加上`摸鱼`角色，并进入服务器的设置-角色管理-右键`摸鱼`角色，复制角色id，并把这个id添加到`"admin_role"`中

<img src="./screenshots/role_id.png" wight="300px" height="200px" alt="角色id获取">

假设`摸鱼`的角色id为114514，那么添加了之后的`TicketConf.json`配置文件应该如下

```json
{
  "guild_id":"ticket bot 所服务的服务器id",
  "ticket": {
    "admin_role": [
      "114514"
    ],
    "category_id": "隐藏掉的频道分组id",
    "channel_id": {},
    "log_channel": "用于发送ticket日志的文字频道id",
    "debug_channel": "用于发送bot出错信息的文字频道id"
  }
}
```
这样才能让**张三**操作`/ticket`命令


### 3.TicketLog

在 `code/log` 路径中新增 `TicketLog.json`，并填入以下字段

```json
{
    "TKnum": 0,
    "data": {},
    "msg_pair": {},
    "TKchannel": {}
}
```

* TKnum是ticket的编号计数，最高为8位数字，应该完全够用了
* TKchannel是用于记录bot创建的ticket频道id，和ticket编号对应
* msg_pair是一个键值对，用于记录bot在ticket频道发送的消息（关闭按钮），和ticket编号对应
* data中是每一个编号的ticket的详细信息，包括开启时间、开启用户、关闭时间、关闭用户、管理员的评论等

### 4.TicketMsgLog

在 `code/log` 路径中新增 `TicketMsgLog.json`，并填入以下字段

```json
{
  "TKMsgChannel": {},
  "data": {}
}
```
* TKMsgChannel是用于记录bot创建的ticket频道id，和ticket编号对应，用来判断ticket频道是否有过消息（避免出现没有发过消息就关闭ticket频道的情况）
* data为消息记录，作为ticket频道的消息记录

为了保存聊天记录，还需要创建 `code/log/ticket` 文件夹，bot会在ticket关闭后，按照编号，保存 `code/log/ticket/编号.json` 文件，并删除 `TicketMsgLog.json` 中 `data` 字段里面的内容。

- [ ] 后续会增加bot发送聊天记录文件到频道的功能

----

#### 下面是ticket功能的示例图

用户先点击按钮，机器人会创建一个临时频道

<img src="./screenshots/tk1.png" wight="300px" height="130px" alt="ticket发起">

并在该频道内部发送一条消息，并at用户和管理员，附带一个只有管理员才能关闭的按钮

<img src="./screenshots/tk2.png" wight="350px" height="220px" alt="bot发送附带关闭按钮的卡片">

ticket被关闭后，bot会向`TicketConf.json`中设置的log频道发送一张卡片

<img src="./screenshots/tk3.png" wight="350px" height="220px" alt="bot发送log卡片">

管理员用户可以使用`/tkcm`命令，给某个ticket添加备注信息，卡片消息会同步更新

```
/tkcm TICKET编号 备注内容
示例
/tkcm 00000000 这是一个测试
```

<img src="./screenshots/tk4.png" wight="350px" height="220px" alt="tkcm">

----

### emoji/role

这个功能的作用是根据一条消息的表情回应，给用户上对应的角色。类似于YY里的上马甲。

请确认您的bot角色拥有管理员权限，并处于其需要给予的角色之上。如图，TestBot只能给其他用户上在他下面的角色，否则Api会报错 `无权限`

<img src="./screenshots/emoji_role_rules.png" alt="emoji_role_rules">

要想使用本功能，请创建 `code/log/ColorID.json`文件，复制如下内容到其中

```json
{
    "data":{}   
}
```

并在 `code/TicketConf.json` 里面追加如下字段

```json
  "emoji": {
    "乱写一个字符串，以后不要修改": {
      "channel_id": "该消息的频道id",
      "data": {},
      "msg_id": "消息id"
    }
  }
```
随后要做的是，在`data`里面添加emoji和角色id的对照表

> 角色ID获取：设置内开启开发者模式后，进入服务器后台，右键角色复制id；
>
> 表情ID获取：
> * 在客户端内，选中表情后`ctrl+c`，即可复制出表情id
> * 在bot的代码中，打印[add_reaction的event消息](https://github.com/musnows/Kook-Ticket-Bot/blob/296f3bf477b8d5530934464fc7f8489d18c65379/code/main.py#L447-L452)获取表情id

<img src="./screenshots/emoji_id.png" wight="250px" height="160px" alt="复制表情id">

配置示例如下，左侧为表情，右侧为这个表情对应的角色id

```json
  "emoji": {
    "乱写一个字符串，以后不要修改": {
      "channel_id": "该消息的频道id",
      "data": {
        "❤": "3970687",
        "🐷": "2881825",
        "👍": "0",
        "💙": "2928540",
        "💚": "2904370",
        "💛": "2882418",
        "💜": "2907567",
        "🖤": "4196071"
      },
      "msg_id": "消息id"
    }
  }
```
如果你有多个消息（比如不同的角色逻辑），那就在后续追加字段

```json
  "emoji": {
    "乱写一个字符串A，以后不要修改": {
      "channel_id": "该消息的频道id",
      "data": {
        "❤": "3970687",
        "🐷": "2881825",
        "👍": "0",
        "💙": "2928540",
        "💚": "2904370",
        "💛": "2882418",
        "💜": "2907567",
        "🖤": "4196071"
      },
      "msg_id": "消息id"
    },
    "乱写一个字符串B，以后不要修改": {
      "channel_id": "该消息的频道id",
      "data": {},
      "msg_id": "消息id"
    }
  }
```

bot会根据`emoji_id`给用户上对应的角色

<img src="./screenshots/role2.png" wight="250px" height="160px" alt="上角色的消息">

<img src="./screenshots/role1.png" wight="350px" height="210px" alt="bot上角色">



## The end
有任何问题，请添加`issue`，或加入我的交流服务器与我联系 [kook邀请链接](https://kook.top/gpbTwZ)

如果你觉得本项目还不错，还请高抬贵手点个star✨，万般感谢！
