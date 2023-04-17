def help_text(text=""):
    """help命令的内容"""
    text+=f"`/ticket` 在本频道发送一条消息，作为ticket的开启按钮\n"
    text+=f"`/tkcm 工单id 备注` 对某一条已经关闭的工单进行备注\n"
    text+=f"`/aar @角色组` 将角色添加进入管理员角色\n"
    text+=f"```\nid获取办法：kook设置-高级设置-打开开发者模式；右键用户头像即可复制用户id，右键频道/分组即可复制id，角色id需要进入服务器管理面板的角色页面中右键复制\n```\n"
    # text+=f"以上命令都需要管理员才能操作\n"
    text+=f"`/gaming 游戏选项` 让机器人开始打游戏(代码中指定了几个游戏)\n"
    text+=f"`/singing 歌名 歌手` 让机器人开始听歌\n"
    text+=f"`/sleeping 1(2)` 让机器人停止打游戏1 or 听歌2\n"
    return text