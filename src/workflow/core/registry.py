"""
步骤注册表 - 管理工作流步骤定义

借鉴 n8n 的 Node Registry 设计：
- 每个步骤有唯一标识
- 步骤可以被动态注册
- 支持不同类型的工作流
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any
from enum import Enum


class StepType(str, Enum):
    """步骤类型"""
    INIT = "init"           # 初始化步骤
    SEARCH = "search"       # 搜索步骤
    EXTRACT = "extract"     # 提取步骤
    TRANSFORM = "transform" # 转换步骤
    ANALYZE = "analyze"     # 分析步骤
    GENERATE = "generate"   # 生成步骤
    FINALIZE = "finalize"   # 最终化步骤


@dataclass
class StepDefinition:
    """
    步骤定义
    
    类似 n8n 的 Node 定义
    """
    name: str                           # 步骤唯一标识
    display_name: str                   # 显示名称
    description: str                    # 步骤描述
    step_type: StepType                 # 步骤类型
    
    # MCP 工具名称
    mcp_tool_name: str = ""
    
    # 输入输出定义
    inputs: list[str] = field(default_factory=list)   # 需要的输入数据 keys
    outputs: list[str] = field(default_factory=list)  # 产出的输出数据 keys
    
    # 是否生成 HTML 片段
    generates_html: bool = True
    
    # 执行顺序（用于排序）
    order: int = 0
    
    # 额外配置
    config: dict = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """
    工作流定义
    
    定义一个完整的工作流包含哪些步骤
    """
    name: str                           # 工作流唯一标识
    display_name: str                   # 显示名称
    description: str                    # 工作流描述
    steps: list[str] = field(default_factory=list)  # 步骤名称列表（按顺序）
    
    # 工作流参数定义
    params: dict[str, dict] = field(default_factory=dict)
    # 格式: {"param_name": {"type": "str", "required": True, "default": None, "description": ""}}


class StepRegistry:
    """
    步骤注册表
    
    单例模式，管理所有步骤和工作流定义
    """
    
    _instance: Optional["StepRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._steps: dict[str, StepDefinition] = {}
            cls._instance._workflows: dict[str, WorkflowDefinition] = {}
            cls._instance._init_default_definitions()
        return cls._instance
    
    def _init_default_definitions(self):
        """初始化默认的步骤和工作流定义"""
        
        # ==================== 场景分析工作流步骤 ====================
        
        self.register_step(StepDefinition(
            name="init_workflow",
            display_name="初始化工作流",
            description="创建工作流状态，生成报告头部",
            step_type=StepType.INIT,
            mcp_tool_name="init_scene_workflow",
            inputs=[],
            outputs=["workflow_id", "log_path", "timestamp", "time_window"],
            order=1
        ))
        
        self.register_step(StepDefinition(
            name="search_files",
            display_name="搜索日志文件",
            description="搜索目录中的 events 日志文件",
            step_type=StepType.SEARCH,
            mcp_tool_name="search_events",
            inputs=["log_path"],
            outputs=["events_files"],
            order=2
        ))
        
        self.register_step(StepDefinition(
            name="extract_logs",
            display_name="提取日志",
            description="从各个文件中提取 input_focus 关键字的日志",
            step_type=StepType.EXTRACT,
            mcp_tool_name="extract_logs",
            inputs=["events_files", "timestamp", "time_window"],
            outputs=["file_logs_map", "total_logs", "files_with_logs"],
            order=3
        ))
        
        self.register_step(StepDefinition(
            name="analyze_timeline",
            display_name="分析时间线",
            description="解析日志生成时间线数据",
            step_type=StepType.ANALYZE,
            mcp_tool_name="analyze_timeline",
            inputs=["file_logs_map"],
            outputs=["timeline_events", "activity_flow"],
            order=4
        ))
        
        self.register_step(StepDefinition(
            name="generate_analysis",
            display_name="生成分析",
            description="AI 分析日志并生成场景分析",
            step_type=StepType.ANALYZE,
            mcp_tool_name="generate_analysis",
            inputs=["file_logs_map", "timeline_events"],
            outputs=["analysis_html"],
            order=5
        ))
        
        self.register_step(StepDefinition(
            name="finalize_report",
            display_name="生成报告",
            description="合并所有 HTML 片段，生成最终报告",
            step_type=StepType.FINALIZE,
            mcp_tool_name="finalize_report",
            inputs=["workflow_id"],
            outputs=["report_path"],
            order=6
        ))
        
        # ==================== 场景分析工作流定义 ====================
        
        self.register_workflow(WorkflowDefinition(
            name="scene_analysis",
            display_name="场景分析",
            description="基于 input_focus 日志分析用户操作场景",
            steps=[
                "init_workflow",
                "search_files",
                "extract_logs",
                "analyze_timeline",
                "generate_analysis",
                "finalize_report"
            ],
            params={
                "log_path": {
                    "type": "str",
                    "required": True,
                    "description": "日志目录或文件路径"
                },
                "timestamp": {
                    "type": "str",
                    "required": True,
                    "description": "分析时间点，格式 MM-DD HH:MM:SS.ffffff"
                },
                "time_window": {
                    "type": "float",
                    "required": False,
                    "default": 20.0,
                    "description": "时间窗口大小（秒）"
                }
            }
        ))
    
    def register_step(self, step: StepDefinition):
        """注册步骤"""
        self._steps[step.name] = step
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """注册工作流"""
        self._workflows[workflow.name] = workflow
    
    def get_step(self, name: str) -> Optional[StepDefinition]:
        """获取步骤定义"""
        return self._steps.get(name)
    
    def get_workflow(self, name: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self._workflows.get(name)
    
    def get_workflow_steps(self, workflow_name: str) -> list[StepDefinition]:
        """获取工作流的所有步骤定义（按顺序）"""
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return []
        
        steps = []
        for step_name in workflow.steps:
            step = self.get_step(step_name)
            if step:
                steps.append(step)
        
        return steps
    
    def list_steps(self) -> list[StepDefinition]:
        """列出所有步骤"""
        return sorted(self._steps.values(), key=lambda s: s.order)
    
    def list_workflows(self) -> list[WorkflowDefinition]:
        """列出所有工作流"""
        return list(self._workflows.values())
    
    def get_step_help(self, step_name: str) -> str:
        """获取步骤帮助信息"""
        step = self.get_step(step_name)
        if not step:
            return f"步骤 {step_name} 不存在"
        
        return f"""
**{step.display_name}** (`{step.name}`)

{step.description}

- **类型**: {step.step_type.value}
- **MCP 工具**: `{step.mcp_tool_name}`
- **输入**: {', '.join(step.inputs) or '无'}
- **输出**: {', '.join(step.outputs) or '无'}
- **生成 HTML**: {'是' if step.generates_html else '否'}
"""
    
    def get_workflow_help(self, workflow_name: str) -> str:
        """获取工作流帮助信息"""
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return f"工作流 {workflow_name} 不存在"
        
        steps_info = []
        for i, step_name in enumerate(workflow.steps, 1):
            step = self.get_step(step_name)
            if step:
                steps_info.append(f"{i}. **{step.display_name}** - `{step.mcp_tool_name}`")
        
        params_info = []
        for param_name, param_def in workflow.params.items():
            required = "必填" if param_def.get("required") else "可选"
            default = f"，默认: {param_def.get('default')}" if param_def.get("default") is not None else ""
            params_info.append(f"- `{param_name}` ({required}{default}): {param_def.get('description', '')}")
        
        return f"""
## {workflow.display_name}

{workflow.description}

### 参数
{chr(10).join(params_info)}

### 步骤
{chr(10).join(steps_info)}
"""


# 全局单例
registry = StepRegistry()

