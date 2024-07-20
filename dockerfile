FROM python:3.10.6-slim

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
# 本地测试的时候用镜像源安装pip包
# RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV LANG="C.UTF-8" \
    TZ="Asia/Shanghai"

WORKDIR /app

COPY . /app/
COPY ./config /app/config
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

VOLUME [ "/app/config" ]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]