"""
状态管理器 - 工作流状态持久化

借鉴 n8n 的 Execution 对象设计：
- 每个工作流实例有唯一 ID
- 状态持久化到 JSON 文件
- 支持断点续跑
- 步骤间数据传递
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class StepResult:
    """步骤执行结果"""
    step_name: str
    status: StepStatus
    started_at: str
    completed_at: Optional[str] = None
    output_data: dict = field(default_factory=dict)
    html_fragment_path: Optional[str] = None
    error: Optional[str] = None


@dataclass 
class WorkflowContext:
    """工作流上下文 - 类似 n8n 的 Execution 对象"""
    workflow_id: str
    workflow_type: str
    status: WorkflowStatus
    created_at: str
    updated_at: str
    
    # 输入参数
    params: dict = field(default_factory=dict)
    
    # 步骤定义
    steps: list[str] = field(default_factory=list)
    current_step_index: int = 0
    
    # 步骤执行结果
    step_results: dict[str, dict] = field(default_factory=dict)
    
    # 全局数据存储 - 步骤间共享数据
    global_data: dict = field(default_factory=dict)
    
    # HTML 片段路径列表
    html_fragments: list[str] = field(default_factory=list)
    
    # 最终输出
    output_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["status"] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowContext":
        """从字典创建"""
        data["status"] = WorkflowStatus(data["status"])
        return cls(**data)


class WorkflowState:
    """
    工作流状态管理器
    
    职责：
    1. 创建和加载工作流状态
    2. 更新步骤执行结果
    3. 管理步骤间数据传递
    4. 管理 HTML 片段存储
    
    目录结构：
    logs/workflows/
    └── {workflow_id}/
        ├── state.json          # 工作流状态
        ├── fragments/          # HTML 片段
        │   ├── 01_header.html
        │   ├── 02_stats.html
        │   └── ...
        └── report.html         # 最终报告
    """
    
    # 工作流根目录
    WORKFLOW_ROOT = Path("logs/workflows")
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.workflow_dir = self.WORKFLOW_ROOT / workflow_id
        self.state_file = self.workflow_dir / "state.json"
        self.fragments_dir = self.workflow_dir / "fragments"
        
    def exists(self) -> bool:
        """检查工作流是否存在"""
        return self.state_file.exists()
    
    def create(
        self,
        workflow_type: str,
        params: dict,
        steps: list[str]
    ) -> WorkflowContext:
        """
        创建新的工作流
        
        Args:
            workflow_type: 工作流类型，如 "scene_analysis"
            params: 输入参数
            steps: 步骤名称列表，按执行顺序
            
        Returns:
            创建的工作流上下文
        """
        # 创建目录结构
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.fragments_dir.mkdir(exist_ok=True)
        
        now = datetime.now().isoformat()
        
        context = WorkflowContext(
            workflow_id=self.workflow_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.RUNNING,
            created_at=now,
            updated_at=now,
            params=params,
            steps=steps,
            current_step_index=0
        )
        
        self._save(context)
        return context
    
    def load(self) -> Optional[WorkflowContext]:
        """加载现有工作流状态"""
        if not self.state_file.exists():
            return None
        
        data = json.loads(self.state_file.read_text(encoding="utf-8"))
        return WorkflowContext.from_dict(data)
    
    def get_current_step(self) -> Optional[str]:
        """获取当前待执行的步骤"""
        context = self.load()
        if not context:
            return None
        
        if context.current_step_index >= len(context.steps):
            return None
            
        return context.steps[context.current_step_index]
    
    def get_step_data(self, step_name: str) -> Optional[dict]:
        """获取指定步骤的输出数据"""
        context = self.load()
        if not context:
            return None
            
        result = context.step_results.get(step_name)
        if result:
            return result.get("output_data", {})
        return None
    
    def set_global_data(self, key: str, value: Any):
        """设置全局数据（步骤间共享）"""
        context = self.load()
        if context:
            context.global_data[key] = value
            context.updated_at = datetime.now().isoformat()
            self._save(context)
    
    def get_global_data(self, key: str, default: Any = None) -> Any:
        """获取全局数据"""
        context = self.load()
        if context:
            return context.global_data.get(key, default)
        return default
    
    def start_step(self, step_name: str) -> WorkflowContext:
        """
        标记步骤开始执行
        
        Args:
            step_name: 步骤名称
            
        Returns:
            更新后的工作流上下文
        """
        context = self.load()
        if not context:
            raise ValueError(f"Workflow {self.workflow_id} not found")
        
        result = StepResult(
            step_name=step_name,
            status=StepStatus.RUNNING,
            started_at=datetime.now().isoformat()
        )
        
        context.step_results[step_name] = asdict(result)
        context.step_results[step_name]["status"] = result.status.value
        context.updated_at = datetime.now().isoformat()
        
        self._save(context)
        return context
    
    def complete_step(
        self,
        step_name: str,
        output_data: dict = None,
        html_fragment: str = None
    ) -> WorkflowContext:
        """
        完成一个步骤
        
        Args:
            step_name: 步骤名称
            output_data: 步骤输出数据，会存入 global_data
            html_fragment: 生成的 HTML 片段内容
            
        Returns:
            更新后的工作流上下文
        """
        context = self.load()
        if not context:
            raise ValueError(f"Workflow {self.workflow_id} not found")
        
        now = datetime.now().isoformat()
        
        # 更新步骤结果
        step_result = context.step_results.get(step_name, {
            "step_name": step_name,
            "status": StepStatus.RUNNING.value,
            "started_at": now
        })
        
        step_result["status"] = StepStatus.COMPLETED.value
        step_result["completed_at"] = now
        step_result["output_data"] = output_data or {}
        
        # 保存 HTML 片段
        if html_fragment:
            fragment_index = len(context.html_fragments) + 1
            fragment_filename = f"{fragment_index:02d}_{step_name}.html"
            fragment_path = self.fragments_dir / fragment_filename
            fragment_path.write_text(html_fragment, encoding="utf-8")
            
            step_result["html_fragment_path"] = str(fragment_path)
            context.html_fragments.append(str(fragment_path))
        
        context.step_results[step_name] = step_result
        
        # 合并输出数据到全局数据
        if output_data:
            context.global_data.update(output_data)
        
        # 推进到下一步
        context.current_step_index += 1
        context.updated_at = now
        
        # 检查是否完成所有步骤
        if context.current_step_index >= len(context.steps):
            context.status = WorkflowStatus.COMPLETED
        
        self._save(context)
        return context
    
    def fail_step(self, step_name: str, error: str) -> WorkflowContext:
        """标记步骤失败"""
        context = self.load()
        if not context:
            raise ValueError(f"Workflow {self.workflow_id} not found")
        
        now = datetime.now().isoformat()
        
        step_result = context.step_results.get(step_name, {
            "step_name": step_name,
            "started_at": now
        })
        
        step_result["status"] = StepStatus.FAILED.value
        step_result["completed_at"] = now
        step_result["error"] = error
        
        context.step_results[step_name] = step_result
        context.status = WorkflowStatus.FAILED
        context.updated_at = now
        
        self._save(context)
        return context
    
    def get_next_step_info(self) -> dict:
        """
        获取下一步信息 - 用于引导 AI 执行
        
        Returns:
            包含下一步信息的字典
        """
        context = self.load()
        if not context:
            return {"error": "Workflow not found"}
        
        if context.status == WorkflowStatus.COMPLETED:
            return {
                "completed": True,
                "message": "✅ 工作流已完成",
                "output_path": context.output_path
            }
        
        if context.status == WorkflowStatus.FAILED:
            return {
                "failed": True,
                "message": "❌ 工作流已失败",
                "step_results": context.step_results
            }
        
        current_step = self.get_current_step()
        progress = f"{context.current_step_index + 1}/{len(context.steps)}"
        
        return {
            "completed": False,
            "current_step": current_step,
            "progress": progress,
            "remaining_steps": context.steps[context.current_step_index:],
            "global_data": context.global_data
        }
    
    def get_all_fragments(self) -> list[str]:
        """获取所有 HTML 片段路径（按顺序）"""
        context = self.load()
        if not context:
            return []
        return context.html_fragments
    
    def set_output_path(self, path: str):
        """设置最终输出路径"""
        context = self.load()
        if context:
            context.output_path = path
            context.updated_at = datetime.now().isoformat()
            self._save(context)
    
    def _save(self, context: WorkflowContext):
        """保存状态到文件"""
        self.state_file.write_text(
            json.dumps(context.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    @classmethod
    def list_workflows(cls) -> list[dict]:
        """列出所有工作流"""
        workflows = []
        if cls.WORKFLOW_ROOT.exists():
            for workflow_dir in cls.WORKFLOW_ROOT.iterdir():
                if workflow_dir.is_dir():
                    state_file = workflow_dir / "state.json"
                    if state_file.exists():
                        data = json.loads(state_file.read_text(encoding="utf-8"))
                        workflows.append({
                            "workflow_id": data["workflow_id"],
                            "type": data["workflow_type"],
                            "status": data["status"],
                            "created_at": data["created_at"]
                        })
        return workflows

