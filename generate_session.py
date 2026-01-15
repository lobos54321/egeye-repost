from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import time

# 这是一个辅助脚本，用于在本地运行一次，获取 Session String
# 获取到的字符串需要填入 Zeabur 的环境变量 TG_SESSION_STRING 中

print("=== Telegram Session String 生成器 ===")
print("请先去 https://my.telegram.org 申请 API ID 和 Hash")

api_id = input("请输入 API ID: ")
api_hash = input("请输入 API Hash: ")

print("\n正在连接 Telegram... (如果需要代理请自行配置环境)")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\n✅ 登录成功！")
    print("\n请复制下面这行长字符串 (这就是你的 Session String):")
    print("-" * 20)
    print(client.session.save())
    print("-" * 20)
    print("\n⚠️  警告: 请保管好这个字符串，拥有它等于拥有你的账号控制权！")
    print("👉 下一步: 去 Zeabur 填入环境变量 TG_SESSION_STRING")
