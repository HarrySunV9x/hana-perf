from typing import Any
import httpx
from common.mcp import mcp

from analyze_memory_killer.analyze_memory_killer import analyze_memory_killer

# Constants
USER_AGENT = "hana-perf/0.1"

if __name__ == "__main__":
    # 初始化并运行 server
    mcp.run(transport='stdio')

    