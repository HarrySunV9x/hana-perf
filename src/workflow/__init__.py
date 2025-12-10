"""
Workflow 模块 - 基于状态机的工作流引擎

设计理念借鉴 n8n / Dify 的工作流架构：
- 节点化：每个步骤是独立的、可复用的单元
- 状态外置：状态持久化到 JSON 文件，支持断点续跑
- 数据流：上一步的输出是下一步的输入

使用方式：
1. 调用 init_scene_workflow 初始化工作流
2. 按顺序调用各个步骤的 MCP Tool
3. 每个步骤自动读取状态、执行、更新状态、生成 HTML 片段
4. 最后调用 finalize_report 合并生成完整报告
"""

from .core.state import WorkflowState
from .core.components import HTMLComponents
from .core.builder import ReportBuilder
from .core.registry import StepRegistry

__all__ = [
    "WorkflowState",
    "HTMLComponents", 
    "ReportBuilder",
    "StepRegistry"
]

