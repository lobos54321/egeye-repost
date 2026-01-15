import re
import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================= 配置区域 (从环境变量获取) =================

# 1. 基础配置
API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')
SESSION_STRING = os.getenv('TG_SESSION_STRING') # 填入通过 generate_session.py 获取的字符串

# 2. 频道配置
# 监听哪个频道？(那个2000人的免费频道 username，不带@)
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')
# 转发到哪个频道？(你自己的频道 username，不带@)
DEST_CHANNEL = os.getenv('DEST_CHANNEL')

# 3. 你的专属链接文案 (支持多行，可以用 \n)
MY_FOOTER = os.getenv('MY_FOOTER', """
--------------------
🚀 **加入VIP群，提前30分钟埋伏金狗！**
👉 5折优惠进群: https://t.me/YourBot?start=123456
""")

# ================= 逻辑区域 =================

if not all([API_ID, API_HASH, SESSION_STRING, SOURCE_CHANNEL, DEST_CHANNEL]):
    print("❌ 错误: 缺少必要的环境变量。请检查 Zeabur 变量设置。")
    print("需要: TG_API_ID, TG_API_HASH, TG_SESSION_STRING, SOURCE_CHANNEL, DEST_CHANNEL")
    # 为了防止容器不断重启报错，这里可以做一个 sleep 或者优雅退出，但直接退出让用户看日志也行
    exit(1)

print("🤖 机器人正在启动...")
# 使用 StringSession，这样就不需要本地文件了，适合 Zeabur 部署
client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    try:
        # 获取原始文本
        original_text = event.message.text or ""
        print(f"📩 收到新消息: {original_text[:20]}...")

        # --- 清洗逻辑 (关键) ---

        # 1. 去掉原始链接 (正则匹配 t.me 链接和 @username)
        # 这是一个简单的过滤，把别人的引流链接删掉
        clean_text = re.sub(r'(https?://t\.me/[a-zA-Z0-9_]+)', '', original_text)
        clean_text = re.sub(r'(@[a-zA-Z0-9_]+)', '', clean_text)

        # 2. 加上我们自己的“小尾巴”
        new_text = clean_text.strip() + "\n" + MY_FOOTER

        # 3. 转发 (带图片/视频一起发)
        # 如果消息有媒体文件(图片等)，会一起发送
        await client.send_message(
            DEST_CHANNEL,
            new_text,
            file=event.message.media
        )
        print("✅ 转发并修改成功！")

    except Exception as e:
        print(f"❌ 转发出错: {e}")

# 启动客户端
print("🔗 正在连接 Telegram 服务器...")
try:
    client.start()
    print(f"🎧 正在监听: {SOURCE_CHANNEL} -> 转发到: {DEST_CHANNEL}")
    client.run_until_disconnected()
except Exception as e:
    print(f"❌ 启动失败: {e}")
