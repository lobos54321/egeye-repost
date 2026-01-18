"""
EgeEye Repost + Twitter Auto Poster V2
TG 信号 → AI 改写 → 发 Twitter + 转发 TG 频道

特性：
- 信号关键信息保护（CA、币名、涨幅、市值）
- VIP 推广话术随机化
- 深夜休眠（悉尼时区）
- 发帖频率控制（30分钟5条上限）
- 自动互动（点赞）
- 新号保护模式
"""

import re
import os
import asyncio
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from ai_rewriter import AIRewriter
from twitter_poster import TwitterPoster
from signal_parser import SignalParser

# ================= 配置区域 =================

# Telegram 配置
API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')
SESSION_STRING = os.getenv('TG_SESSION_STRING')

# 频道配置
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')  # 信号源频道
DEST_CHANNEL = os.getenv('DEST_CHANNEL')      # 转发到的 TG 频道

# Twitter 配置
ENABLE_TWITTER = os.getenv('ENABLE_TWITTER', 'true').lower() == 'true'

# AI 配置
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# TG 转发小尾巴
MY_FOOTER = os.getenv('MY_FOOTER', """
--------------------
🚀 加入 EgeEye，抓住下一个 100 倍！
👉 t.me/egeyeaimeme
""")

# 悉尼时区
TIMEZONE = ZoneInfo('Australia/Sydney')

# ================= 全局变量 =================

tg_client = None
ai_rewriter = None
twitter_poster = None
signal_parser = None
twitter_queue = asyncio.Queue()

# ================= 初始化函数 =================

def check_config():
    """检查必要配置"""
    if not all([API_ID, API_HASH, SESSION_STRING, SOURCE_CHANNEL, DEST_CHANNEL]):
        print("❌ 错误: 缺少必要的 Telegram 环境变量")
        print("需要: TG_API_ID, TG_API_HASH, TG_SESSION_STRING, SOURCE_CHANNEL, DEST_CHANNEL")
        return False
    return True


async def init_services():
    """初始化所有服务"""
    global tg_client, ai_rewriter, twitter_poster, signal_parser

    print("🤖 EgeEye Signal Bot V2 启动中...")
    print(f"⏰ 当前悉尼时间: {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}")

    # Telegram 客户端
    tg_client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)

    # 信号解析器
    signal_parser = SignalParser()
    print("✅ 信号解析器已就绪")

    # AI 改写器
    try:
        ai_rewriter = AIRewriter()
        if GEMINI_API_KEY:
            print("✅ AI 改写器已启用 (Gemini)")
        else:
            print("⚠️ 未设置 GEMINI_API_KEY，使用模板模式")
    except Exception as e:
        print(f"⚠️ AI 改写器初始化失败: {e}")
        ai_rewriter = None

    # Twitter 发帖器
    if ENABLE_TWITTER:
        try:
            twitter_poster = TwitterPoster()
            await twitter_poster.init_browser()

            is_logged_in = await twitter_poster.check_login()
            if is_logged_in:
                print("✅ Twitter 已登录")
            else:
                print("❌ Twitter 未登录，请先运行 python twitter_login.py")
                print("   Twitter 功能将被禁用")
                await twitter_poster.close()
                twitter_poster = None
        except Exception as e:
            print(f"❌ Twitter 初始化失败: {e}")
            twitter_poster = None
    else:
        print("⚠️ Twitter 发帖已禁用 (ENABLE_TWITTER=false)")


async def twitter_worker():
    """Twitter 发帖工作线程"""
    print("🐦 Twitter worker 已启动")

    while True:
        try:
            # 从队列获取待发内容
            tweet_content = await twitter_queue.get()

            if not twitter_poster:
                print("⚠️ Twitter 未就绪，跳过")
                twitter_queue.task_done()
                continue

            # 尝试发推
            success, reason = await twitter_poster.post_tweet(tweet_content)

            if not success:
                if "休眠" in reason:
                    # 休眠时段，重新放回队列，等会再试
                    print(f"😴 休眠中，1800秒后重试...")
                    await asyncio.sleep(1800)  # 等30分钟
                    await twitter_queue.put(tweet_content)
                elif "等待" in reason:
                    # 需要等待，提取等待时间
                    wait_match = re.search(r'(\d+)', reason)
                    if wait_match:
                        wait_time = int(wait_match.group(1))
                        print(f"⏳ 等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time + random.randint(10, 30))
                        await twitter_queue.put(tweet_content)
                elif "上限" in reason:
                    print(f"📊 达到每日上限，明天继续")
                    # 不重试，丢弃这条
                else:
                    print(f"⚠️ 发推失败: {reason}")

            twitter_queue.task_done()

            # 随机延迟，避免太规律
            await asyncio.sleep(random.randint(5, 15))

        except Exception as e:
            print(f"❌ Twitter worker 错误: {e}")
            await asyncio.sleep(30)


# ================= 消息处理 =================

async def handle_signal(event):
    """处理新信号"""
    global tg_client

    try:
        original_text = event.message.text or ""

        # 跳过空消息
        if not original_text.strip():
            return

        print(f"\n{'='*50}")
        print(f"📩 收到新信号")
        print(f"   {original_text[:80]}...")

        # 1. 解析信号
        signal = signal_parser.parse(original_text)

        if signal.ca:
            print(f"   币名: {signal.token_name}")
            print(f"   CA: {signal.ca[:20]}...")
            print(f"   涨幅: {signal.gain}")

        # 2. 转发到 TG 频道
        await forward_to_tg(original_text, event.message.media)

        # 3. 改写并发 Twitter（仅当有 CA 时）
        if signal.ca and ENABLE_TWITTER and twitter_poster and ai_rewriter:
            tweet_content = await ai_rewriter.rewrite(original_text)

            if tweet_content:
                await twitter_queue.put(tweet_content)
                print(f"📝 已加入 Twitter 队列 (队列长度: {twitter_queue.qsize()})")
        elif not signal.ca:
            print("⚠️ 未找到 CA，仅转发 TG")

    except Exception as e:
        print(f"❌ 处理信号出错: {e}")
        import traceback
        traceback.print_exc()


async def forward_to_tg(original_text: str, media=None):
    """转发到 TG 频道"""
    global tg_client

    try:
        # 清洗内容
        clean_text = re.sub(r'(https?://t\.me/[a-zA-Z0-9_]+)', '', original_text)
        clean_text = re.sub(r'(@[a-zA-Z0-9_]+)', '', clean_text)

        # 加小尾巴
        tg_content = clean_text.strip() + "\n" + MY_FOOTER

        # 发送
        await tg_client.send_message(
            DEST_CHANNEL,
            tg_content,
            file=media
        )
        print("✅ TG 转发成功")

    except Exception as e:
        print(f"❌ TG 转发失败: {e}")


# ================= 主函数 =================

async def main():
    """主函数"""
    global tg_client

    if not check_config():
        return

    await init_services()

    # 注册消息处理器
    @tg_client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def handler(event):
        await handle_signal(event)

    # 启动 TG 客户端
    print(f"\n🔗 正在连接 Telegram...")
    await tg_client.start()
    print(f"🎧 正在监听: {SOURCE_CHANNEL}")
    print(f"📤 TG 转发到: {DEST_CHANNEL}")

    # 启动 Twitter worker
    if ENABLE_TWITTER and twitter_poster:
        asyncio.create_task(twitter_worker())
        print(f"🐦 Twitter 发帖已启用")

    print(f"\n{'='*50}")
    print("✅ 系统已就绪，等待信号...")
    print(f"{'='*50}\n")

    # 保持运行
    await tg_client.run_until_disconnected()


# ================= 入口 =================

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 收到退出信号，正在关闭...")
    except Exception as e:
        print(f"❌ 致命错误: {e}")
        import traceback
        traceback.print_exc()
