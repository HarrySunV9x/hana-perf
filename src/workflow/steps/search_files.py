"""
搜索文件步骤

负责在日志目录中搜索包含 'events' 的日志文件
"""

import os
from pathlib import Path
from ..core.components import HTMLComponents, StatCard
from .base import BaseStep


class SearchFilesStep(BaseStep):
    """搜索文件步骤"""
    
    step_name = "search_files"
    
    async def execute(self) -> dict:
        """执行搜索"""
        log_path = self.get_param("log_path")
        log_path_obj = Path(log_path)
        
        events_files = []
        
        if log_path_obj.is_file():
            # 如果是单个文件，检查文件名是否包含 events
            if 'events' in log_path_obj.name.lower():
                events_files.append({
                    "path": str(log_path_obj.absolute()),
                    "name": log_path_obj.name,
                    "size": log_path_obj.stat().st_size
                })
        elif log_path_obj.is_dir():
            # 如果是目录，递归搜索
            for root, dirs, files in os.walk(log_path):
                for file in files:
                    if 'events' in file.lower():
                        file_path = Path(root) / file
                        events_files.append({
                            "path": str(file_path.absolute()),
                            "name": file,
                            "size": file_path.stat().st_size
                        })
        
        return {
            "events_files": events_files,
            "files_count": len(events_files),
            "total_size": sum(f["size"] for f in events_files)
        }
    
    def generate_html(self, output_data: dict) -> str:
        """生成统计卡片 HTML"""
        files_count = output_data["files_count"]
        total_size = output_data["total_size"]
        time_window = self.get_param("time_window", 20.0)
        
        # 格式化文件大小
        if total_size > 1024 * 1024:
            size_str = f"{total_size / (1024*1024):.1f} MB"
        elif total_size > 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size} B"
        
        stats_html = HTMLComponents.stats_cards([
            StatCard(value=str(files_count), label="Events 文件", icon="📁"),
            StatCard(value=size_str, label="总大小", icon="💾"),
            StatCard(value=f"{time_window}s", label="时间窗口", icon="⏱️")
        ])
        
        return HTMLComponents.section(
            title="统计信息",
            content=stats_html,
            icon="📈",
            section_id="stats"
        )


async def search_events(workflow_id: str) -> str:
    """
    搜索 Events 日志文件
    
    供 MCP 工具调用
    
    Args:
        workflow_id: 工作流 ID
        
    Returns:
        执行结果和下一步指引
    """
    step = SearchFilesStep(workflow_id)
    return await step.run()

