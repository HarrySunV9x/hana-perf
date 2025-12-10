"""
最终化报告步骤

合并所有 HTML 片段，生成最终报告
"""

from pathlib import Path
from ..core.builder import ReportBuilder
from ..core.components import HTMLComponents
from .base import BaseStep


class FinalizeReportStep(BaseStep):
    """最终化报告步骤"""
    
    step_name = "finalize_report"
    
    async def execute(self) -> dict:
        """执行报告生成"""
        # 获取工作流信息
        context = self.context
        if not context:
            raise ValueError("工作流上下文不存在")
        
        timestamp = context.params.get("timestamp", "")
        
        # 创建报告构建器
        builder = ReportBuilder(f"场景分析报告 - {timestamp}")
        
        # 加载所有 HTML 片段
        fragments = self.state.get_all_fragments()
        for fragment_path in fragments:
            builder.add_fragment_from_file(fragment_path)
        
        # 生成输出路径
        safe_timestamp = timestamp.replace(":", "-").replace(" ", "_").replace(".", "-")
        output_path = f"logs/workflows/{self.workflow_id}/report.html"
        
        # 构建报告
        absolute_path = builder.build(output_path)
        
        # 更新状态
        self.state.set_output_path(absolute_path)
        
        return {
            "report_path": absolute_path,
            "fragments_count": len(fragments)
        }
    
    def generate_html(self, output_data: dict) -> str:
        """最终步骤不生成额外的 HTML 片段"""
        return ""
    
    async def run(self) -> str:
        """重写 run 方法，因为最终步骤有特殊的输出格式"""
        if not self.state.exists():
            return f"❌ 工作流 {self.workflow_id} 不存在"
        
        try:
            self.state.start_step(self.step_name)
            
            output_data = await self.execute()
            
            self.state.complete_step(
                self.step_name,
                output_data=output_data,
                html_fragment=None  # 最终步骤不生成片段
            )
            
            report_path = output_data["report_path"]
            
            return f"""
🎉 **工作流已完成！**

## 📄 报告信息

- **报告路径**: `{report_path}`
- **片段数量**: {output_data['fragments_count']}

## 📋 执行摘要

工作流 `{self.workflow_id}` 已成功完成所有步骤。

您可以在浏览器中打开报告文件查看完整的场景分析结果。

```bash
open "{report_path}"
```
"""
            
        except Exception as e:
            self.state.fail_step(self.step_name, str(e))
            return f"❌ 报告生成失败: {e}"


async def finalize_report(workflow_id: str) -> str:
    """
    生成最终报告
    
    供 MCP 工具调用
    
    Args:
        workflow_id: 工作流 ID
        
    Returns:
        执行结果
    """
    step = FinalizeReportStep(workflow_id)
    return await step.run()

