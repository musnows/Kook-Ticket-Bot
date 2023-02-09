# encoding: utf-8
# 本文件仅供replit部署使用，具体请看如下文档
# https://blog.musnow.top/2023/02/09/note_python/9%E7%99%BD%E5%AB%96replist%E9%83%A8%E7%BD%B2ticket%E6%9C%BA%E5%99%A8%E4%BA%BA/
# 如果您是在云服务器/本地电脑部署本bot，请忽略此文件

from flask import Flask
from threading import Thread
# 初始化
app = Flask(' ')
# 设立根路径作为api调用
@app.route('/')
def home():
  text = "ticket bot online!"
  print(text)
  return text
# 开始运行，绑定ip和端口
def run():
  app.run(host='0.0.0.0',port = 8000)
# 通过线程运行
def keep_alive():
  t= Thread(target=run)
  t.start()