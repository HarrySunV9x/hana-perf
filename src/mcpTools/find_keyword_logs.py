from common.filter_logs import filter_logs
from common.mcp import mcp
from common.log import logger
from pathlib import Path

@mcp.tool()
async def find_keyword_logs(log_file:str, keyword:str, timestamp: str, time_window: float = 1.0) -> list[str]:
    """
    该工具会在指定的时间范围内查找包含 "keyword" 关键字的日志行，
    用于分析系统由于其他原因而杀死进程的情况。
    
    Args:
        log_file: 日志文件的路径（字符串格式）
        keyword: 关键字，用于过滤日志行
        timestamp: 目标时间戳，格式为 "MM-DD HH:MM:SS.ffffff"，例如 "10-28 09:27:29.665281"
        time_window: 时间窗口大小（秒），默认为 1.0 秒。会在目标时间戳前后各 time_window/2 秒范围内搜索
    
    Returns:
        包含匹配日志行的列表。如果日志文件不存在，返回错误提示字符串。
    """
    if not Path(log_file).exists():
        return "Log file not found"

    logs = filter_logs(log_file, keyword, timestamp, time_window)
    logger.info(f"Found {len(logs)} {keyword} log lines")
    return logs