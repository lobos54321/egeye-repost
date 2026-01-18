"""
Twitter Auto Poster V2 - 高级反检测版本
- 随机化发帖时间
- 深夜休眠（悉尼时区）
- 自动互动（点赞、回复）
- 频率限制（30分钟不超过5条）
- 新号保护模式
"""

import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

class TwitterPoster:
    def __init__(self):
        self.cookies_file = os.path.join(os.path.dirname(__file__), 'twitter_cookies.json')
        self.stats_file = os.path.join(os.path.dirname(__file__), 'twitter_stats.json')
        self.browser = None
        self.context = None
        self.page = None

        # 悉尼时区
        self.timezone = ZoneInfo('Australia/Sydney')

        # 加载统计数据
        self.stats = self._load_stats()

        # 配置参数
        self.config = {
            'min_interval': int(os.getenv('TWITTER_MIN_INTERVAL', '600')),  # 最小间隔10分钟
            'max_per_30min': int(os.getenv('TWITTER_MAX_PER_30MIN', '5')),  # 30分钟最多5条
            'daily_limit': int(os.getenv('TWITTER_DAILY_LIMIT', '50')),      # 每日上限
            'new_account_mode': os.getenv('TWITTER_NEW_ACCOUNT', 'false').lower() == 'true',
            'new_account_limit': int(os.getenv('TWITTER_NEW_ACCOUNT_LIMIT', '10')),  # 新号每日限制
            'sleep_start': 3,   # 悉尼时间凌晨3点开始休眠
            'sleep_end': 9,     # 悉尼时间早上9点结束休眠
            'interaction_chance': 0.3,  # 30%概率做互动
        }

    def _load_stats(self):
        """加载统计数据"""
        if os.path.exists(self.stats_file):
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            'today': datetime.now(self.timezone).strftime('%Y-%m-%d'),
            'tweets_today': 0,
            'recent_tweets': [],  # 最近30分钟的发推时间戳
            'last_interaction': 0,
        }

    def _save_stats(self):
        """保存统计数据"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f)

    def _reset_daily_stats(self):
        """重置每日统计"""
        today = datetime.now(self.timezone).strftime('%Y-%m-%d')
        if self.stats['today'] != today:
            self.stats['today'] = today
            self.stats['tweets_today'] = 0
            self._save_stats()
            print(f"📅 新的一天，计数器已重置")

    async def init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(
            headless=os.getenv('HEADLESS', 'false').lower() == 'true'
        )

        if os.path.exists(self.cookies_file):
            self.context = await self.browser.new_context(
                storage_state=self.cookies_file,
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("✅ 已加载保存的登录状态")
        else:
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("⚠️ 未找到登录状态，需要先登录")

        self.page = await self.context.new_page()

    async def save_cookies(self):
        """保存登录状态"""
        await self.context.storage_state(path=self.cookies_file)
        print(f"✅ 登录状态已保存")

    async def check_login(self):
        """检查是否已登录"""
        await self.page.goto('https://x.com/home', wait_until='networkidle')
        await asyncio.sleep(2)
        if 'login' in self.page.url or 'i/flow' in self.page.url:
            return False
        return True

    async def login_manual(self):
        """手动登录"""
        print("\n" + "="*50)
        print("🔐 请在浏览器中手动登录 Twitter/X")
        print("   登录完成后，回到终端按 Enter 继续...")
        print("="*50 + "\n")

        await self.page.goto('https://x.com/login')
        input("按 Enter 键确认已登录完成...")
        await self.save_cookies()
        print("✅ 登录成功，状态已保存！")

    def is_sleep_time(self):
        """检查是否在休眠时段（悉尼时间凌晨3点-早上9点）"""
        now = datetime.now(self.timezone)
        hour = now.hour
        if self.config['sleep_start'] <= hour or hour < self.config['sleep_end']:
            # 凌晨3-23点 或 0-9点
            if hour >= self.config['sleep_start'] or hour < self.config['sleep_end']:
                return True
        return False

    def can_tweet(self):
        """检查是否可以发推"""
        self._reset_daily_stats()
        now = datetime.now(self.timezone).timestamp()

        # 1. 检查休眠时段
        if self.is_sleep_time():
            hour = datetime.now(self.timezone).hour
            print(f"😴 休眠时段 (悉尼时间 {hour}点)，暂停发帖")
            return False, "休眠时段"

        # 2. 检查每日限制
        daily_limit = self.config['new_account_limit'] if self.config['new_account_mode'] else self.config['daily_limit']
        if self.stats['tweets_today'] >= daily_limit:
            print(f"📊 已达今日上限 ({daily_limit}条)")
            return False, "达到每日上限"

        # 3. 清理30分钟前的记录
        thirty_min_ago = now - 1800
        self.stats['recent_tweets'] = [t for t in self.stats['recent_tweets'] if t > thirty_min_ago]

        # 4. 检查30分钟内发推数量
        if len(self.stats['recent_tweets']) >= self.config['max_per_30min']:
            wait_time = int(self.stats['recent_tweets'][0] + 1800 - now)
            print(f"⏰ 30分钟内已发 {self.config['max_per_30min']} 条，需等待 {wait_time} 秒")
            return False, f"等待 {wait_time} 秒"

        # 5. 检查最小间隔
        if self.stats['recent_tweets']:
            last_tweet = max(self.stats['recent_tweets'])
            elapsed = now - last_tweet
            if elapsed < self.config['min_interval']:
                wait = int(self.config['min_interval'] - elapsed)
                print(f"⏳ 距上次发推仅 {int(elapsed)} 秒，需再等 {wait} 秒")
                return False, f"等待 {wait} 秒"

        return True, "OK"

    async def random_scroll(self):
        """随机滚动页面，模拟真人浏览"""
        scroll_amount = random.randint(100, 500)
        await self.page.evaluate(f'window.scrollBy(0, {scroll_amount})')
        await asyncio.sleep(random.uniform(0.5, 2))

    async def do_interaction(self):
        """随机互动：点赞或浏览"""
        try:
            print("💬 执行随机互动...")

            # 先随机滚动
            for _ in range(random.randint(2, 5)):
                await self.random_scroll()

            # 尝试点赞一条推文
            like_buttons = await self.page.query_selector_all('[data-testid="like"]')
            if like_buttons and len(like_buttons) > 0:
                # 随机选一条点赞
                btn = random.choice(like_buttons[:5])  # 只在前5条中选
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await btn.click()
                print("❤️ 点赞了一条推文")
                await asyncio.sleep(random.uniform(1, 3))

            self.stats['last_interaction'] = datetime.now(self.timezone).timestamp()
            self._save_stats()

        except Exception as e:
            print(f"⚠️ 互动失败 (不影响发帖): {e}")

    async def post_tweet(self, content):
        """发送推文"""
        # 检查是否可以发推
        can_post, reason = self.can_tweet()
        if not can_post:
            return False, reason

        try:
            # 随机延迟
            await asyncio.sleep(random.uniform(2, 5))

            # 打开首页
            await self.page.goto('https://x.com/home', wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 4))

            # 随机概率先做互动
            if random.random() < self.config['interaction_chance']:
                await self.do_interaction()

            # 点击发推输入框
            tweet_box = await self.page.wait_for_selector(
                '[data-testid="tweetTextarea_0"]',
                timeout=10000
            )
            await tweet_box.click()
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # 模拟真人打字
            for char in content:
                await self.page.keyboard.type(char, delay=random.randint(30, 100))
                # 偶尔停顿
                if random.random() < 0.05:
                    await asyncio.sleep(random.uniform(0.3, 0.8))

            await asyncio.sleep(random.uniform(1, 3))

            # 点击发送
            post_button = await self.page.wait_for_selector(
                '[data-testid="tweetButtonInline"]',
                timeout=5000
            )
            await post_button.click()
            await asyncio.sleep(random.uniform(2, 4))

            # 更新统计
            now = datetime.now(self.timezone).timestamp()
            self.stats['tweets_today'] += 1
            self.stats['recent_tweets'].append(now)
            self._save_stats()

            print(f"✅ 推文发送成功 (今日第 {self.stats['tweets_today']} 条): {content[:40]}...")
            return True, "发送成功"

        except Exception as e:
            print(f"❌ 发推失败: {e}")
            return False, str(e)

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("🔒 浏览器已关闭")


async def main():
    """测试"""
    poster = TwitterPoster()
    await poster.init_browser()

    is_logged_in = await poster.check_login()
    if not is_logged_in:
        await poster.login_manual()

    # 测试发推
    test_content = "Testing... 🚀 #crypto"
    success, msg = await poster.post_tweet(test_content)
    print(f"结果: {success}, {msg}")

    await poster.close()


if __name__ == '__main__':
    asyncio.run(main())
