"""
日志脱敏工具
对日志消息中的敏感信息进行过滤或截断。
"""

import re

# 正则表达式编译（模块级缓存以提高性能）
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
CPF_PATTERN_WITH_FORMAT = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
CPF_PATTERN_RAW = re.compile(r"\b\d{11}\b")
PHONE_PATTERN = re.compile(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}")

# 默认截断长度
DEFAULT_MAX_POST_LENGTH = 200
TRUNCATION_SUFFIX = "[...truncated]"


def sanitize_log_message(msg: str, max_post_length: int = DEFAULT_MAX_POST_LENGTH) -> str:
    """
    对日志消息进行脱敏处理。

    处理规则：
    1. 移除邮箱地址
    2. 移除 CPF（带格式或纯数字）
    3. 移除电话号码
    4. 截断过长的内容（超过 max_post_length 时附加 [...truncated]）

    Args:
        msg: 原始日志消息
        max_post_length: 内容最大长度（默认 200）

    Returns:
        脱敏后的日志消息
    """
    if not isinstance(msg, str):
        # 非字符串输入尝试转换，失败则返回占位符
        try:
            msg = str(msg)
        except Exception:
            return "<non-string log message>"

    # 1. 邮箱
    msg = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", msg)

    # 2. CPF（先处理带格式的）
    msg = CPF_PATTERN_WITH_FORMAT.sub("[CPF_REDACTED]", msg)

    # 3. 电话（在原始 CPF 之前处理，避免 11 位数字与电话号码重叠时的标签歧义）
    msg = PHONE_PATTERN.sub("[PHONE_REDACTED]", msg)

    # 4. 原始 CPF（纯 11 位数字，放在电话之后，优先保证电话号码识别）
    msg = CPF_PATTERN_RAW.sub("[CPF_REDACTED]", msg)

    # 4. 截断过长内容
    if len(msg) > max_post_length:
        msg = msg[:max_post_length] + TRUNCATION_SUFFIX

    return msg
