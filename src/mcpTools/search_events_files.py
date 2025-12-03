from common.mcp import mcp
from common.log import logger
from pathlib import Path
import os
import json

@mcp.tool()
async def search_events_files(log_path: str) -> str:
    """
    【步骤1/4】搜索日志目录中包含 'events' 的文件
    
    这是场景分析的第一步，用于定位所有相关的 events 日志文件。
    找到文件后，AI agent 应该对每个文件调用 find_keyword_logs 工具。
    
    Args:
        log_path: 日志目录或文件的路径（字符串格式）
    
    Returns:
        返回找到的 events 文件列表（JSON格式），包含文件路径和基本信息
    """
    log_path_obj = Path(log_path)
    
    logger.info(f"[Step 1/4] Searching for files containing 'events' in {log_path}")
    events_files = []
    
    if log_path_obj.is_file():
        # 如果是单个文件，检查文件名是否包含 events
        if 'events' in log_path_obj.name.lower():
            events_files.append({
                "path": str(log_path_obj.absolute()),
                "name": log_path_obj.name,
                "size": log_path_obj.stat().st_size if log_path_obj.exists() else 0
            })
    elif log_path_obj.is_dir():
        # 如果是目录，递归搜索包含 events 的文件
        for root, dirs, files in os.walk(log_path):
            for file in files:
                if 'events' in file.lower():
                    file_path = Path(root) / file
                    events_files.append({
                        "path": str(file_path.absolute()),
                        "name": file,
                        "size": file_path.stat().st_size if file_path.exists() else 0
                    })
    else:
        error_msg = f"❌ 路径不存在: {log_path}"
        logger.error(error_msg)
        return error_msg
    
    if not events_files:
        return f"❌ 未找到包含 'events' 的日志文件在路径: {log_path}"
    
    logger.info(f"✅ Found {len(events_files)} events files")
    
    result = f"""
✅ 【步骤1/4完成】找到 {len(events_files)} 个 events 文件

## 文件列表
{chr(10).join([f"- {f['name']} ({f['size']:,} bytes)" for f in events_files])}

## 下一步操作
请对每个文件调用 `find_keyword_logs` 工具，参数如下：
- keyword: "input_focus"
- timestamp: [你要分析的时间点]
- time_window: [时间窗口大小，建议20秒]

## 文件路径（JSON格式）
```json
{json.dumps(events_files, ensure_ascii=False, indent=2)}
```
"""
    
    return result

