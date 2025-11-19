from common.filter_logs import filter_logs
from common.mcp import mcp
from common.log import logger
from pathlib import Path

@mcp.tool()
async def analyze_memory_killer(log_file:str, timestamp: str, time_window: float = 1.0) -> list[str]:
    if not Path(log_file).exists():
        return "Log file not found"

    logs = filter_logs(log_file, "am_kill", timestamp, time_window)
    logger.info(f"Found {len(logs)} memory killer log lines")
    return logs