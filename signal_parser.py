"""
信号解析器 - 提取信号中的关键信息
确保 CA、币名、涨幅、市值 等核心数据不被篡改
"""

import re
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class SignalData:
    """信号数据结构"""
    token_name: Optional[str] = None      # 币名 $XXX
    ca: Optional[str] = None              # 合约地址
    chain: str = "SOL"                    # 链 (SOL/BSC)
    gain: Optional[str] = None            # 涨幅 (12.83倍)
    market_cap: Optional[str] = None      # 市值
    raw_text: str = ""                    # 原始文本


class SignalParser:
    """信号解析器"""

    # Solana CA 正则 (32-44 位 base58)
    SOL_CA_PATTERN = r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b'

    # BSC CA 正则 (0x 开头 40 位 hex)
    BSC_CA_PATTERN = r'\b(0x[a-fA-F0-9]{40})\b'

    # 币名正则 ($XXX)
    TOKEN_PATTERN = r'\$([A-Za-z][A-Za-z0-9]*)'

    # 涨幅正则 (12.83倍 或 12.83x)
    GAIN_PATTERN = r'(\d+\.?\d*)\s*(倍|x|X)'

    # 市值正则 ($21.80K 或 $279.64K)
    MC_PATTERN = r'\$(\d+\.?\d*)\s*(K|M|B)?'

    # 市值变化正则 ($21.80K —> $279.64K)
    MC_CHANGE_PATTERN = r'\$[\d.]+\s*[KMB]?\s*[—\-\→>]+\s*\$[\d.]+\s*[KMB]?'

    def parse(self, text: str) -> SignalData:
        """解析信号文本"""
        signal = SignalData(raw_text=text)

        # 1. 提取币名 ($XXX)
        token_match = re.search(self.TOKEN_PATTERN, text)
        if token_match:
            signal.token_name = f"${token_match.group(1)}"

        # 2. 提取 CA
        # 先尝试 Solana
        sol_match = re.search(self.SOL_CA_PATTERN, text)
        if sol_match:
            ca = sol_match.group(1)
            # 过滤掉太短或无效的
            if len(ca) >= 32 and self._is_valid_ca(ca):
                signal.ca = ca
                signal.chain = "SOL"

        # 再尝试 BSC
        if not signal.ca:
            bsc_match = re.search(self.BSC_CA_PATTERN, text)
            if bsc_match:
                signal.ca = bsc_match.group(1)
                signal.chain = "BSC"

        # 3. 提取涨幅
        gain_match = re.search(self.GAIN_PATTERN, text)
        if gain_match:
            number = gain_match.group(1)
            unit = gain_match.group(2)
            signal.gain = f"{number}{unit}"

        # 4. 提取市值变化
        mc_change_match = re.search(self.MC_CHANGE_PATTERN, text)
        if mc_change_match:
            signal.market_cap = mc_change_match.group(0)
        else:
            # 单独的市值
            mc_matches = re.findall(self.MC_PATTERN, text)
            if mc_matches:
                # 取最后一个作为当前市值
                last_mc = mc_matches[-1]
                signal.market_cap = f"${last_mc[0]}{last_mc[1]}"

        return signal

    def _is_valid_ca(self, ca: str) -> bool:
        """验证 CA 是否有效"""
        # 不是全相同字符
        if len(set(ca)) < 5:
            return False
        # 长度合理
        if len(ca) < 32 or len(ca) > 44:
            return False
        return True

    def validate_output(self, signal: SignalData, output_text: str) -> tuple:
        """验证改写输出是否保留了关键信息"""
        errors = []

        # CA 必须存在
        if signal.ca and signal.ca not in output_text:
            errors.append(f"CA 丢失: {signal.ca}")

        # 币名必须存在
        if signal.token_name and signal.token_name not in output_text:
            errors.append(f"币名丢失: {signal.token_name}")

        # 涨幅必须存在（数字部分）
        if signal.gain:
            gain_number = re.search(r'(\d+\.?\d*)', signal.gain)
            if gain_number and gain_number.group(1) not in output_text:
                errors.append(f"涨幅丢失: {signal.gain}")

        if errors:
            return False, errors

        return True, []


# 测试
if __name__ == '__main__':
    parser = SignalParser()

    test_signal = """
    🎉 $KERNEL 最新涨幅为 12.83倍 🎉
    AL9ECCZrSbSdmL8hngxjxTwZvYPpoBtHqGW51pZVBAGS
    💰 市值 $21.80K —> $279.64K
    💵💵💵💵💵
    """

    signal = parser.parse(test_signal)

    print("解析结果：")
    print(f"  币名: {signal.token_name}")
    print(f"  CA: {signal.ca}")
    print(f"  链: {signal.chain}")
    print(f"  涨幅: {signal.gain}")
    print(f"  市值: {signal.market_cap}")
