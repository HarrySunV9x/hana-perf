"""
分析时间线步骤

解析日志数据，生成时间线和 Activity 流程
"""

import re
from pathlib import Path
from ..core.components import HTMLComponents, TimelineEvent
from .base import BaseStep


class AnalyzeTimelineStep(BaseStep):
    """分析时间线步骤"""
    
    step_name = "analyze_timeline"
    
    async def execute(self) -> dict:
        """执行时间线分析"""
        file_logs_map = self.get_input("file_logs_map", {})
        
        # 收集所有日志行并按时间排序
        all_logs = []
        for file_path, logs in file_logs_map.items():
            for log in logs:
                time_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d+)', log)
                if time_match:
                    all_logs.append({
                        "time": time_match.group(1),
                        "content": log.strip(),
                        "file": Path(file_path).name
                    })
        
        # 按时间排序
        all_logs.sort(key=lambda x: x["time"])
        
        # 解析 input_focus 事件
        timeline_events = []
        activity_flow = []
        seen_activities = set()
        
        for log in all_logs:
            event = self._parse_input_focus(log["content"])
            if event:
                timeline_events.append({
                    "time": log["time"],
                    "title": event.get("title", "焦点切换"),
                    "description": event.get("description", ""),
                    "package": event.get("package", ""),
                    "activity": event.get("activity", "")
                })
                
                # 记录 Activity 流程（去重）
                activity_key = f"{event.get('package', '')}:{event.get('activity', '')}"
                if activity_key not in seen_activities and event.get("activity"):
                    seen_activities.add(activity_key)
                    activity_flow.append({
                        "time": log["time"],
                        "package": event.get("package", ""),
                        "activity": event.get("activity", "")
                    })
        
        return {
            "timeline_events": timeline_events,
            "activity_flow": activity_flow,
            "events_count": len(timeline_events)
        }
    
    def _parse_input_focus(self, log_line: str) -> dict:
        """解析 input_focus 日志行"""
        result = {}
        
        # 尝试提取包名和 Activity
        # 常见格式: input_focus: com.example.app/.MainActivity
        focus_match = re.search(r'input_focus[:\s]+(\S+)/(\S+)', log_line)
        if focus_match:
            result["package"] = focus_match.group(1)
            result["activity"] = focus_match.group(2)
            result["title"] = f"焦点切换到 {result['activity']}"
            result["description"] = f"包名: {result['package']}"
        else:
            # 尝试其他格式
            pkg_match = re.search(r'([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+)', log_line, re.IGNORECASE)
            if pkg_match:
                result["package"] = pkg_match.group(1)
                result["title"] = f"焦点变化"
                result["description"] = log_line[:100]
        
        # 如果找到了有效信息
        if result:
            return result
        
        # 返回基本信息
        return {
            "title": "input_focus 事件",
            "description": log_line[:100] if len(log_line) > 100 else log_line
        }
    
    def generate_html(self, output_data: dict) -> str:
        """生成时间线 HTML"""
        timeline_events = output_data["timeline_events"]
        activity_flow = output_data["activity_flow"]
        
        html_parts = []
        
        # 生成垂直时间线
        if timeline_events:
            events = [
                TimelineEvent(
                    time=e["time"],
                    title=e["title"],
                    description=e.get("description", "")
                )
                for e in timeline_events[:20]  # 限制显示数量
            ]
            
            timeline_html = HTMLComponents.timeline_vertical(
                events=events,
                title="Activity 切换时间线"
            )
            
            # 显示截断提示
            if len(timeline_events) > 20:
                timeline_html += HTMLComponents.conclusion_box(
                    title="提示",
                    content=f"共 {len(timeline_events)} 个事件，仅显示前 20 个",
                    box_type="info"
                )
            
            html_parts.append(timeline_html)
        
        # 生成 Activity 流程图
        if activity_flow:
            flow_html = HTMLComponents.activity_flow(activity_flow[:10])
            html_parts.append(HTMLComponents.divider("Activity 流程"))
            html_parts.append(flow_html)
        
        content = "\n".join(html_parts) if html_parts else "未发现有效的时间线事件"
        
        return HTMLComponents.section(
            title="时间线分析",
            content=content,
            icon="⏱️",
            section_id="timeline"
        )


async def analyze_timeline(workflow_id: str) -> str:
    """
    分析时间线
    
    供 MCP 工具调用
    
    Args:
        workflow_id: 工作流 ID
        
    Returns:
        执行结果和下一步指引
    """
    step = AnalyzeTimelineStep(workflow_id)
    return await step.run()

