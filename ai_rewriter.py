"""
AI Content Rewriter - 使用 Gemini 改写 TG 信号为 Twitter 风格
- 保留关键信息（CA、币名、涨幅、市值）
- 添加 VIP 推广话术
- 随机化内容避免重复
"""

import os
import random
import google.generativeai as genai
from signal_parser import SignalParser, SignalData


# VIP 推广话术（随机选择）
VIP_PROMOS = [
    "👀 We called it early! Next 100x? 👉 t.me/egeyeaimeme",
    "🎯 EgeEye AI spotted this first! Join 👉 t.me/egeyeaimeme",
    "🔥 Another banger from EgeEye! Free signals 👉 t.me/egeyeaimeme",
    "🤖 AI-powered alpha! Don't miss the next one 👉 t.me/egeyeaimeme",
    "💎 Early calls, big gains! Join us 👉 t.me/egeyeaimeme",
    "🚀 Want early access to gems? 👉 t.me/egeyeaimeme",
    "📡 EgeEye AI never sleeps! Follow for alpha 👉 t.me/egeyeaimeme",
    "⚡ Caught another runner! More signals 👉 t.me/egeyeaimeme",
    "🎰 We find gems, you take profits! 👉 t.me/egeyeaimeme",
    "🔮 AI sees what others miss! Join 👉 t.me/egeyeaimeme",
]

# 开头话术（随机选择）
OPENERS = [
    "🚀",
    "💥",
    "🔥",
    "⚡",
    "💎",
    "🎯",
    "📈",
    "🌙",
]

# Hashtags 池
HASHTAGS = [
    "#Solana",
    "#SOL",
    "#Memecoin",
    "#Crypto",
    "#100x",
    "#GEM",
    "#Alpha",
    "#DeFi",
]


class AIRewriter:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️ 未设置 GEMINI_API_KEY，将使用模板模式")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')

        self.parser = SignalParser()
        self.channel_link = os.getenv('VIP_CHANNEL', 't.me/egeyeaimeme')

    def _get_prompt(self, signal: SignalData) -> str:
        """生成 AI 改写 prompt"""
        return f"""你是一个加密货币推特博主。将以下信号改写成简短有力的英文推文。

【绝对禁止修改的信息】：
- 币名: {signal.token_name}
- CA: {signal.ca}
- 涨幅: {signal.gain}
- 市值: {signal.market_cap}

【要求】：
1. 用英文写
2. 简短有力，像真人发的推文
3. 可以用 emoji
4. 必须包含币名、CA、涨幅
5. 不要加 hashtag（我会单独加）
6. 不要加推广链接（我会单独加）
7. 不超过 150 字符

【原始信号】：
{signal.raw_text}

直接输出推文内容，不要任何解释："""

    async def rewrite(self, original_text: str) -> str:
        """改写信号为 Twitter 推文"""
        # 1. 解析信号
        signal = self.parser.parse(original_text)

        if not signal.ca:
            print("⚠️ 未找到 CA，跳过")
            return None

        # 2. 生成推文
        if self.model:
            tweet_body = await self._ai_rewrite(signal)
        else:
            tweet_body = self._template_rewrite(signal)

        # 3. 验证关键信息
        valid, errors = self.parser.validate_output(signal, tweet_body)
        if not valid:
            print(f"⚠️ AI 输出验证失败: {errors}")
            # 使用模板兜底
            tweet_body = self._template_rewrite(signal)

        # 4. 组装完整推文
        full_tweet = self._assemble_tweet(tweet_body, signal)

        # 5. 最终长度检查
        if len(full_tweet) > 280:
            # 缩短版本
            full_tweet = self._short_version(signal)

        return full_tweet

    async def _ai_rewrite(self, signal: SignalData) -> str:
        """使用 AI 改写"""
        try:
            prompt = self._get_prompt(signal)
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ AI 改写失败: {e}")
            return self._template_rewrite(signal)

    def _template_rewrite(self, signal: SignalData) -> str:
        """模板改写（无 AI 时使用）"""
        opener = random.choice(OPENERS)

        templates = [
            f"{opener} {signal.token_name} pumped {signal.gain}!\n\nCA: {signal.ca}",
            f"{opener} {signal.token_name} just did {signal.gain}!\n\nCA: {signal.ca}",
            f"{opener} {signal.token_name} {signal.gain} and counting!\n\nCA: {signal.ca}",
            f"{opener} Another {signal.gain} on {signal.token_name}!\n\nCA: {signal.ca}",
            f"{opener} {signal.token_name} went {signal.gain}! 🔥\n\nCA: {signal.ca}",
        ]

        body = random.choice(templates)

        # 添加市值（如果有）
        if signal.market_cap:
            body += f"\n\nMC: {signal.market_cap}"

        return body

    def _assemble_tweet(self, body: str, signal: SignalData) -> str:
        """组装完整推文"""
        # 随机 VIP 推广
        promo = random.choice(VIP_PROMOS)

        # 随机 2-3 个 hashtags
        tags = random.sample(HASHTAGS, random.randint(2, 3))

        # 如果有币名，加入 hashtag
        if signal.token_name:
            token_tag = f"#{signal.token_name.replace('$', '')}"
            tags.insert(0, token_tag)

        hashtag_str = " ".join(tags)

        # 组装
        full_tweet = f"{body}\n\n{promo}\n\n{hashtag_str}"

        return full_tweet

    def _short_version(self, signal: SignalData) -> str:
        """超长时的缩短版本"""
        opener = random.choice(OPENERS)
        promo = random.choice(VIP_PROMOS)

        # 极简版
        short = f"{opener} {signal.token_name} {signal.gain}!\n\n{signal.ca}\n\n{promo}"

        return short[:280]


# 测试
if __name__ == '__main__':
    import asyncio

    os.environ['GEMINI_API_KEY'] = 'AIzaSyAm6ndM0zlOG0Ec-rgVj71taMtdgECvnXI'

    rewriter = AIRewriter()

    test_signal = """
    🎉 $KERNEL 最新涨幅为 12.83倍 🎉
    AL9ECCZrSbSdmL8hngxjxTwZvYPpoBtHqGW51pZVBAGS
    💰 市值 $21.80K —> $279.64K
    💵💵💵💵💵
    """

    result = asyncio.run(rewriter.rewrite(test_signal))
    print("\n" + "="*50)
    print("最终推文：")
    print("="*50)
    print(result)
    print(f"\n字符数: {len(result)}")
