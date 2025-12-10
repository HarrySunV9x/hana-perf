"""
提取日志步骤

从各个 events 文件中提取 input_focus 关键字的日志
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from ..core.components import HTMLComponents
from .base import BaseStep


class ExtractLogsStep(BaseStep):
    """提取日志步骤"""
    
    step_name = "extract_logs"
    
    async def execute(self) -> dict:
        """执行日志提取"""
        events_files = self.get_input("events_files", [])
        timestamp = self.get_param("timestamp")
        time_window = self.get_param("time_window", 20.0)
        
        # 解析时间
        target_time = self._parse_timestamp(timestamp)
        start_time = target_time - timedelta(seconds=time_window / 2)
        end_time = target_time + timedelta(seconds=time_window / 2)
        
        file_logs_map = {}
        total_logs = 0
        
        for file_info in events_files:
            file_path = file_info["path"]
            logs = self._filter_logs(file_path, "input_focus", start_time, end_time)
            
            if logs:
                file_logs_map[file_path] = logs
                total_logs += len(logs)
        
        return {
            "file_logs_map": file_logs_map,
            "total_logs": total_logs,
            "files_with_logs": len(file_logs_map)
        }
    
    def _parse_timestamp(self, timestamp: str) -> datetime:
        """解析时间戳"""
        # 如果没有微秒部分，补上
        if '.' not in timestamp:
            timestamp = timestamp + '.000000'
        
        target_time = datetime.strptime(timestamp, '%m-%d %H:%M:%S.%f')
        target_time = target_time.replace(year=datetime.now().year)
        return target_time
    
    def _filter_logs(
        self,
        file_path: str,
        keyword: str,
        start_time: datetime,
        end_time: datetime
    ) -> list[str]:
        """过滤日志"""
        filtered_logs = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 关键字过滤
                    if keyword not in line:
                        continue
                    
                    # 时间过滤
                    time_match = re.search(r'(\d{2}-\d{2}\s+)(\d{2}:\d{2}:\d{2}\.\d+)', line)
                    if time_match:
                        try:
                            time_str = time_match.group(0)
                            log_time = datetime.strptime(time_str, '%m-%d %H:%M:%S.%f')
                            log_time = log_time.replace(year=datetime.now().year)
                            
                            if start_time <= log_time <= end_time:
                                filtered_logs.append(line)
                        except ValueError:
                            continue
                    else:
                        # 没有时间戳但包含关键字，也保留
                        filtered_logs.append(line)
        except Exception:
            pass
        
        return filtered_logs
    
    def generate_html(self, output_data: dict) -> str:
        """生成日志块 HTML"""
        file_logs_map = output_data["file_logs_map"]
        
        if not file_logs_map:
            return HTMLComponents.conclusion_box(
                title="未找到日志",
                content="在指定时间范围内未找到 input_focus 相关日志",
                box_type="warning"
            )
        
        logs_html = ""
        for file_path, logs in file_logs_map.items():
            filename = Path(file_path).name
            content = "".join(logs[:200])  # 限制显示行数
            
            logs_html += HTMLComponents.log_block(
                filename=filename,
                content=content,
                line_count=len(logs),
                max_lines=200
            )
        
        return HTMLComponents.section(
            title="原始日志",
            content=logs_html,
            icon="📝",
            section_id="logs"
        )


async def extract_logs(workflow_id: str) -> str:
    """
    提取日志
    
    供 MCP 工具调用
    
    Args:
        workflow_id: 工作流 ID
        
    Returns:
        执行结果和下一步指引
    """
    step = ExtractLogsStep(workflow_id)
    return await step.run()

