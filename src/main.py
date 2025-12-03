from typing import Any
import httpx
from common.mcp import mcp
from mcpTools.find_keyword_logs import find_keyword_logs
from mcpTools.find_sences_by_input_focus import find_sences_by_input_focus
from mcpTools.search_events_files import search_events_files
from mcpTools.generate_scene_report import generate_scene_report

USER_AGENT = "hana-perf/0.1"

if __name__ == "__main__":
    # 初始化并运行 server
    mcp.run(transport='stdio')

    