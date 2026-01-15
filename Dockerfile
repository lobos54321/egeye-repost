# 使用轻量级 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制脚本文件
COPY . .

# 设置环境变量，确保 Python 输出直接打印到日志
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "main.py"]
