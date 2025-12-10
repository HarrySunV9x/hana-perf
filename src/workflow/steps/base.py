"""
步骤基类 - 所有步骤的抽象基类

借鉴 n8n 的 Node 执行模式
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from ..core.state import WorkflowState, WorkflowContext
from ..core.components import HTMLComponents
from ..core.registry import StepDefinition, registry


class BaseStep(ABC):
    """
    步骤基类
    
    所有步骤都需要继承此类并实现 execute 方法
    """
    
    # 子类需要定义步骤名称
    step_name: str = ""
    
    def __init__(self, workflow_id: str):
        """
        初始化步骤
        
        Args:
            workflow_id: 工作流 ID
        """
        self.workflow_id = workflow_id
        self.state = WorkflowState(workflow_id)
        self.components = HTMLComponents()
        
        # 获取步骤定义
        self.definition: Optional[StepDefinition] = registry.get_step(self.step_name)
    
    @property
    def context(self) -> Optional[WorkflowContext]:
        """获取工作流上下文"""
        return self.state.load()
    
    def get_input(self, key: str, default: Any = None) -> Any:
        """
        获取输入数据（从全局数据中）
        
        Args:
            key: 数据键
            default: 默认值
        """
        return self.state.get_global_data(key, default)
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """
        获取工作流参数
        
        Args:
            key: 参数键
            default: 默认值
        """
        context = self.context
        if context:
            return context.params.get(key, default)
        return default
    
    def validate_inputs(self) -> tuple[bool, str]:
        """
        验证输入数据是否完整
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.definition:
            return True, ""
        
        missing = []
        for input_key in self.definition.inputs:
            value = self.get_input(input_key) or self.get_param(input_key)
            if value is None:
                missing.append(input_key)
        
        if missing:
            return False, f"缺少输入数据: {', '.join(missing)}"
        
        return True, ""
    
    @abstractmethod
    async def execute(self) -> dict:
        """
        执行步骤
        
        子类必须实现此方法
        
        Returns:
            输出数据字典
        """
        pass
    
    @abstractmethod
    def generate_html(self, output_data: dict) -> str:
        """
        生成 HTML 片段
        
        子类必须实现此方法
        
        Args:
            output_data: execute() 的输出数据
            
        Returns:
            HTML 片段字符串
        """
        pass
    
    async def run(self) -> str:
        """
        运行步骤的完整流程
        
        1. 验证输入
        2. 标记开始
        3. 执行步骤
        4. 生成 HTML
        5. 完成步骤
        6. 返回下一步指引
        
        Returns:
            执行结果和下一步指引
        """
        # 验证工作流存在
        if not self.state.exists():
            return f"❌ 工作流 {self.workflow_id} 不存在，请先调用 init_scene_workflow"
        
        # 验证输入
        valid, error = self.validate_inputs()
        if not valid:
            return f"❌ 输入验证失败: {error}"
        
        try:
            # 标记开始
            self.state.start_step(self.step_name)
            
            # 执行步骤
            output_data = await self.execute()
            
            # 生成 HTML（如果步骤定义要求）
            html_fragment = None
            if self.definition and self.definition.generates_html:
                html_fragment = self.generate_html(output_data)
            
            # 完成步骤
            self.state.complete_step(
                self.step_name,
                output_data=output_data,
                html_fragment=html_fragment
            )
            
            # 返回结果和下一步指引
            return self._format_result(output_data)
            
        except Exception as e:
            # 标记失败
            self.state.fail_step(self.step_name, str(e))
            return f"❌ 步骤执行失败: {e}"
    
    def _format_result(self, output_data: dict) -> str:
        """格式化执行结果"""
        next_info = self.state.get_next_step_info()
        
        step_display = self.definition.display_name if self.definition else self.step_name
        
        result = f"""
✅ **{step_display}** 完成

## 输出数据
"""
        # 添加关键输出信息
        for key, value in output_data.items():
            if isinstance(value, (list, dict)):
                if isinstance(value, list):
                    result += f"- `{key}`: {len(value)} 项\n"
                else:
                    result += f"- `{key}`: {len(value)} 字段\n"
            else:
                result += f"- `{key}`: {value}\n"
        
        result += "\n---\n\n"
        
        # 添加下一步指引
        if next_info.get("completed"):
            result += "🎉 **工作流已完成！**\n"
            if next_info.get("output_path"):
                result += f"\n📄 报告已生成: `{next_info['output_path']}`"
        else:
            current_step = next_info.get("current_step", "")
            progress = next_info.get("progress", "")
            step_def = registry.get_step(current_step)
            
            if step_def:
                result += f"""
## 📍 下一步 ({progress})

**{step_def.display_name}**

调用工具: `{step_def.mcp_tool_name}`

参数:
```
workflow_id: "{self.workflow_id}"
```
"""
        
        return result

