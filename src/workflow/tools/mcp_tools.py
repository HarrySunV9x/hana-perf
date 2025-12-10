"""
MCP 工具注册

将工作流步骤注册为 MCP 工具，供 AI agent 调用
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_workflow_tools(mcp: "FastMCP"):
    """
    注册所有工作流相关的 MCP 工具
    
    Args:
        mcp: FastMCP 实例
    """
    
    # ==================== 步骤 1: 初始化工作流 ====================
    
    @mcp.tool()
    async def init_scene_workflow(
        log_path: str,
        timestamp: str,
        time_window: float = 20.0
    ) -> str:
        """
        【步骤 1/6】初始化场景分析工作流
        
        这是场景分析的入口，会创建工作流状态并生成报告头部。
        
        执行完成后会返回 workflow_id，后续步骤需要使用此 ID。
        
        Args:
            log_path: 日志目录或文件路径
            timestamp: 分析时间点，格式 "MM-DD HH:MM:SS.ffffff"
            time_window: 时间窗口大小（秒），默认 20.0
            
        Returns:
            执行结果和下一步指引（包含 workflow_id）
        """
        from ..steps.init_workflow import init_scene_workflow as _init
        return await _init(log_path, timestamp, time_window)
    
    # ==================== 步骤 2: 搜索文件 ====================
    
    @mcp.tool()
    async def search_events(workflow_id: str) -> str:
        """
        【步骤 2/6】搜索 Events 日志文件
        
        在日志目录中搜索包含 'events' 的日志文件。
        
        参数会从工作流状态中自动获取，只需提供 workflow_id。
        
        Args:
            workflow_id: 工作流 ID（从步骤1获取）
            
        Returns:
            执行结果和下一步指引
        """
        from ..steps.search_files import search_events as _search
        return await _search(workflow_id)
    
    # ==================== 步骤 3: 提取日志 ====================
    
    @mcp.tool()
    async def extract_logs(workflow_id: str) -> str:
        """
        【步骤 3/6】提取日志
        
        从步骤2找到的文件中提取 input_focus 关键字的日志。
        
        会根据时间窗口过滤日志。
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            执行结果和下一步指引
        """
        from ..steps.extract_logs import extract_logs as _extract
        return await _extract(workflow_id)
    
    # ==================== 步骤 4: 分析时间线 ====================
    
    @mcp.tool()
    async def analyze_timeline(workflow_id: str) -> str:
        """
        【步骤 4/6】分析时间线
        
        解析日志数据，生成时间线和 Activity 流程。
        
        会自动解析 input_focus 日志中的包名和 Activity 信息。
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            执行结果和下一步指引
        """
        from ..steps.analyze_timeline import analyze_timeline as _analyze
        return await _analyze(workflow_id)
    
    # ==================== 步骤 5: 生成分析（AI 分析） ====================
    
    @mcp.tool()
    async def generate_analysis(
        workflow_id: str,
        analysis_content: str
    ) -> str:
        """
        【步骤 5/6】生成场景分析
        
        此步骤需要 AI 分析日志数据并提供分析内容。
        
        分析内容应包含：
        - 用户操作场景描述
        - 关键发现
        - 性能指标（如果有）
        
        Args:
            workflow_id: 工作流 ID
            analysis_content: AI 生成的分析内容（HTML 格式）
            
        Returns:
            执行结果和下一步指引
        """
        from ..core.state import WorkflowState
        from ..core.components import HTMLComponents
        
        state = WorkflowState(workflow_id)
        
        if not state.exists():
            return f"❌ 工作流 {workflow_id} 不存在"
        
        try:
            state.start_step("generate_analysis")
            
            # 包装分析内容
            html_fragment = HTMLComponents.section(
                title="场景分析",
                content=analysis_content,
                icon="🎯",
                section_id="analysis"
            )
            
            state.complete_step(
                "generate_analysis",
                output_data={"analysis_generated": True},
                html_fragment=html_fragment
            )
            
            next_info = state.get_next_step_info()
            
            return f"""
✅ **场景分析** 完成

分析内容已保存到 HTML 片段。

---

## 📍 下一步 ({next_info.get('progress', '')})

**生成报告**

调用工具: `finalize_report`

参数:
```
workflow_id: "{workflow_id}"
```
"""
            
        except Exception as e:
            state.fail_step("generate_analysis", str(e))
            return f"❌ 分析生成失败: {e}"
    
    # ==================== 步骤 6: 生成报告 ====================
    
    @mcp.tool()
    async def finalize_report(workflow_id: str) -> str:
        """
        【步骤 6/6】生成最终报告
        
        合并所有 HTML 片段，生成最终的场景分析报告。
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            报告文件路径
        """
        from ..steps.finalize_report import finalize_report as _finalize
        return await _finalize(workflow_id)
    
    # ==================== 辅助工具 ====================
    
    @mcp.tool()
    async def get_workflow_status(workflow_id: str) -> str:
        """
        获取工作流状态
        
        查看当前工作流的执行状态和下一步操作。
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            工作流状态信息
        """
        from ..core.state import WorkflowState
        
        state = WorkflowState(workflow_id)
        
        if not state.exists():
            return f"❌ 工作流 {workflow_id} 不存在"
        
        context = state.load()
        if not context:
            return f"❌ 无法加载工作流状态"
        
        next_info = state.get_next_step_info()
        
        # 构建步骤状态列表
        steps_status = []
        for step_name in context.steps:
            result = context.step_results.get(step_name, {})
            status = result.get("status", "pending")
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(status, "❓")
            steps_status.append(f"{status_icon} {step_name}")
        
        return f"""
## 工作流状态

- **ID**: `{workflow_id}`
- **类型**: {context.workflow_type}
- **状态**: {context.status.value}
- **创建时间**: {context.created_at}

### 参数
- 日志路径: `{context.params.get('log_path', '')}`
- 时间点: {context.params.get('timestamp', '')}
- 时间窗口: {context.params.get('time_window', '')}秒

### 步骤进度
{chr(10).join(steps_status)}

### 下一步
{next_info.get('message', '') if next_info.get('completed') or next_info.get('failed') else f"调用 `{next_info.get('current_step', '')}` 工具"}
"""
    
    @mcp.tool()
    async def list_workflows() -> str:
        """
        列出所有工作流
        
        显示所有已创建的工作流及其状态。
        
        Returns:
            工作流列表
        """
        from ..core.state import WorkflowState
        
        workflows = WorkflowState.list_workflows()
        
        if not workflows:
            return "📭 没有找到任何工作流"
        
        lines = ["## 工作流列表", ""]
        for wf in workflows:
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(wf["status"], "❓")
            
            lines.append(f"- {status_icon} `{wf['workflow_id']}` ({wf['type']}) - {wf['created_at']}")
        
        return "\n".join(lines)

