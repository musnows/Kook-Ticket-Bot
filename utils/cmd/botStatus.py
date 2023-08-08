# 机器人在玩状态相关功能
import traceback
from khl import Bot,Message
from ..file import logging,_log
from ..kookApi import status_active_game,status_active_music,status_delete
from ..gtime import get_time

def init(bot:Bot):
    # 开始打游戏
    @bot.command(name="game", aliases=["gaming"], case_sensitive=False)
    async def gaming(msg: Message, game: int = 0, *arg):
        logging(msg)
        try:
            if game == 0:
                await msg.reply(f"[gaming] 参数错误，用法「/gaming 数字」\n1-人间地狱，2-英雄联盟，3-CSGO")
                return
            elif game == 1:
                ret = await status_active_game(464053)  # 人间地狱
                await msg.reply(f"{ret['message']}，Bot上号人间地狱啦！")
            elif game == 2:
                ret = await status_active_game(3)  # 英雄联盟
                await msg.reply(f"{ret['message']}，Bot上号LOL啦！")
            elif game == 3:
                ret = await status_active_game(23)  # CSGO
                await msg.reply(f"{ret['message']}，Bot上号CSGO啦！")

        except Exception as result:
            _log.exception(f"Au:{msg.author_id} | ERR")
            await msg.reply(f"ERR! [{get_time()}] game\n```\n{traceback.format_exc()}\n```")


    # 开始听歌
    @bot.command(name="sing", aliases=["singing"], case_sensitive=False)
    async def singing(msg: Message, music: str = "e", singer: str = "e", *arg):
        logging(msg)
        try:
            if music == "e" or singer == "e":
                await msg.reply(f"[singing] 参数错误，用法「/singing 歌名 歌手」")
                return
            # 参数正确，开始操作
            ret = await status_active_music(music, singer)
            await msg.reply(f"{ret['message']}，Bot开始听歌啦！")
        except Exception as result:
            _log.exception(f"Au:{msg.author_id} | ERR")
            await msg.reply(f"ERR! [{get_time()}] sing\n```\n{traceback.format_exc()}\n```")


    # 停止打游戏1/听歌2
    @bot.command(name="sleep", case_sensitive=False)
    async def sleeping(msg: Message, d: int = 0, *arg):
        logging(msg)
        try:
            if d == 0:
                await msg.reply(f"[sleep] 参数错误，用法「/sleep 数字」\n1-停止游戏，2-停止听歌")
            ret = await status_delete(d)
            if d == 1:
                await msg.reply(f"{ret['message']}，Bot下号休息啦!")
            elif d == 2:
                await msg.reply(f"{ret['message']}，Bot摘下了耳机~")
        except Exception as result:
            _log.exception(f"Au:{msg.author_id} | ERR")
            await msg.reply(f"ERR! [{get_time()}] sleep\n```\n{traceback.format_exc()}\n```")

    _log.info(f"load botStatus.py")