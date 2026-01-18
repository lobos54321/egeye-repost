# EgeEye Repost + Twitter Bot V2

TG 信号监听 → AI 改写 → 自动发 Twitter + 转发 TG 频道

## 特性

- ✅ **信号关键信息保护** - CA、币名、涨幅、市值原样保留
- ✅ **VIP 推广话术随机化** - 每条推文都不一样
- ✅ **深夜休眠** - 悉尼时间 3:00-9:00 停发
- ✅ **频率控制** - 30分钟最多5条，每条间隔10分钟
- ✅ **自动互动** - 随机点赞，模拟真人
- ✅ **新号保护模式** - 新号每天限制10条

## 文件说明

| 文件 | 功能 |
|------|------|
| `main_v2.py` | 主程序：监听 TG + 发 Twitter + 转发 |
| `twitter_poster.py` | Twitter 自动发帖模块（含反检测） |
| `twitter_login.py` | Twitter 登录脚本（本地运行一次） |
| `ai_rewriter.py` | Gemini AI 改写模块 |
| `signal_parser.py` | 信号解析器（提取 CA、币名等） |
| `generate_session.py` | TG Session 生成器 |

## 使用步骤

### 1. 安装依赖
```bash
cd /Users/boliu/web3-skyvern/egeye-repost
pip install -r requirements.txt
playwright install chromium
```

### 2. 本地登录 Twitter（只需一次）
```bash
python twitter_login.py
```
- 浏览器会打开，手动登录 Twitter
- 登录后 cookies 会保存到 `twitter_cookies.json`

### 3. 配置环境变量
```bash
# Telegram
export TG_API_ID=你的API_ID
export TG_API_HASH=你的API_HASH
export TG_SESSION_STRING=你的Session字符串
export SOURCE_CHANNEL=信号源频道username
export DEST_CHANNEL=目标频道username

# Twitter
export ENABLE_TWITTER=true
export TWITTER_MIN_INTERVAL=600      # 最小发帖间隔（秒），默认10分钟
export TWITTER_MAX_PER_30MIN=5       # 30分钟最多5条
export TWITTER_DAILY_LIMIT=50        # 每日上限
export TWITTER_NEW_ACCOUNT=false     # 新号模式
export TWITTER_NEW_ACCOUNT_LIMIT=10  # 新号每日限制

# AI
export GEMINI_API_KEY=你的Gemini_API_Key

# TG 小尾巴
export MY_FOOTER="你的引流文案"
```

### 4. 运行
```bash
python main_v2.py
```

## 发帖策略

| 规则 | 设置 |
|------|------|
| 最小间隔 | 10分钟 |
| 30分钟上限 | 5条 |
| 每日上限 | 50条（新号10条） |
| 休眠时段 | 悉尼 3:00-9:00 |
| 互动概率 | 30% 点赞 |

## 部署到 Zeabur

1. 把 `twitter_cookies.json` 一起上传
2. 设置所有环境变量
3. 设置 `HEADLESS=true`（无头模式）

## 注意事项

- Twitter cookies 有效期约 30-90 天，过期需重新登录
- 建议先用小号测试
- 保持像真人操作的节奏
