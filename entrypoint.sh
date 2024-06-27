#!/bin/sh

# 如果日志目录不存在，则创建它
if [ ! -d /app/config/log ]; then
  mkdir -p /app/config/log
  touch /app/config/log/bot.log
fi

# 执行主程序
exec "$@"