"""
Twitter 登录脚本 - 本地运行，手动登录并保存 cookies
"""

import asyncio
from twitter_poster import TwitterPoster


async def main():
    print("="*50)
    print("🐦 Twitter 登录工具")
    print("="*50)
    print("\n这个脚本会打开浏览器，让你手动登录 Twitter")
    print("登录后会保存 cookies，之后自动发帖时不用再登录\n")

    poster = TwitterPoster()
    await poster.init_browser()

    # 检查是否已登录
    is_logged_in = await poster.check_login()

    if is_logged_in:
        print("✅ 已经登录了！")
        confirm = input("要重新登录吗？(y/n): ")
        if confirm.lower() != 'y':
            await poster.close()
            return

    # 手动登录
    await poster.login_manual()

    # 验证登录成功
    is_logged_in = await poster.check_login()
    if is_logged_in:
        print("\n🎉 登录成功！cookies 已保存")
        print("现在可以运行 main_v2.py 开始自动发帖了")
    else:
        print("\n❌ 登录似乎失败了，请重试")

    await poster.close()


if __name__ == '__main__':
    asyncio.run(main())
