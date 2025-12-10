"""
初始化工作流步骤

这是工作流的第一步，负责：
1. 创建工作流状态
2. 生成报告头部 HTML
"""

from datetime import datetime
from pathlib import Path
from ..core.state import WorkflowState
from ..core.components import HTMLComponents, StatCard
from ..core.registry import registry
from .base import BaseStep


class InitWorkflowStep(BaseStep):
    """初始化工作流步骤"""
    
    step_name = "init_workflow"
    
    def __init__(
        self,
        log_path: str,
        timestamp: str,
        time_window: float = 20.0
    ):
        """
        初始化
        
        Args:
            log_path: 日志路径
            timestamp: 分析时间点
            time_window: 时间窗口
        """
        # 生成工作流 ID
        safe_timestamp = timestamp.replace(":", "").replace(" ", "_").replace(".", "")
        workflow_id = f"scene_{safe_timestamp}_{datetime.now().strftime('%H%M%S')}"
        
        super().__init__(workflow_id)
        
        self.log_path = log_path
        self.timestamp = timestamp
        self.time_window = time_window
    
    async def execute(self) -> dict:
        """执行初始化"""
        # 获取工作流定义
        workflow_def = registry.get_workflow("scene_analysis")
        if not workflow_def:
            raise ValueError("场景分析工作流定义不存在")
        
        # 创建工作流状态
        self.state.create(
            workflow_type="scene_analysis",
            params={
                "log_path": self.log_path,
                "timestamp": self.timestamp,
                "time_window": self.time_window
            },
            steps=workflow_def.steps
        )
        
        return {
            "workflow_id": self.workflow_id,
            "log_path": self.log_path,
            "timestamp": self.timestamp,
            "time_window": self.time_window
        }
    
    def generate_html(self, output_data: dict) -> str:
        """生成报告头部 HTML"""
        return HTMLComponents.header(
            title="📊 场景分析报告",
            subtitle=f"日志路径: {output_data['log_path']}",
            timestamp=output_data['timestamp'],
            extra_info={
                "时间窗口": f"±{output_data['time_window']/2}秒"
            }
        )
    
    async def run(self) -> str:
        """
        重写 run 方法，因为初始化步骤不需要验证工作流存在
        """
        try:
            # 执行步骤
            output_data = await self.execute()
            
            # 生成 HTML
            html_fragment = self.generate_html(output_data)
            
            # 保存 HTML 片段（手动调用，因为状态刚创建）
            self.state.start_step(self.step_name)
            self.state.complete_step(
                self.step_name,
                output_data=output_data,
                html_fragment=html_fragment
            )
            
            # 返回结果
            return self._format_result(output_data)
            
        except Exception as e:
            return f"❌ 初始化失败: {e}"


async def init_scene_workflow(
    log_path: str,
    timestamp: str,
    time_window: float = 20.0
) -> str:
    """
    初始化场景分析工作流
    
    这是场景分析的入口函数，供 MCP 工具调用
    
    Args:
        log_path: 日志目录或文件路径
        timestamp: 分析时间点，格式 "MM-DD HH:MM:SS.ffffff"
        time_window: 时间窗口大小（秒），默认 20.0
        
    Returns:
        执行结果和下一步指引
    """
    # 验证路径存在
    if not Path(log_path).exists():
        return f"❌ 路径不存在: {log_path}"
    
    step = InitWorkflowStep(log_path, timestamp, time_window)
    return await step.run()

