#!/bin/sh
echo "[entrypoint] begin to run entrypoint.sh"

# 如果日志目录不存在，则创建它
if [ ! -d /app/config/log ]; then
  mkdir -p /app/config/log
  touch /app/config/log/bot.log
  echo "[entrypoint] create files and dir of /app/config/log/bot.log"
fi

echo "[entrypoint] return to run python process"
# 执行主程序
exec "$@"