from common.mcp import mcp
from common.log import logger
from pathlib import Path
from datetime import datetime
import json

@mcp.tool()
async def generate_scene_report(
    timestamp: str, 
    time_window: float,
    log_data: str,
    log_path: str
) -> str:
    """
    【步骤3/4】生成场景分析 HTML 报告
    
    基于收集的日志数据生成初步的 HTML 报告框架。
    AI agent 需要在后续步骤中分析日志并填充分析结论。
    
    Args:
        timestamp: 分析的目标时间戳，格式为 "MM-DD HH:MM:SS.ffffff"
        time_window: 时间窗口大小（秒）
        log_data: 日志数据（JSON格式），包含文件路径和对应的日志内容
        log_path: 原始日志路径
    
    Returns:
        返回生成的 HTML 文件路径和下一步操作说明
    """
    logger.info(f"[Step 3/4] Generating HTML report for timestamp {timestamp}")
    
    # 解析日志数据
    try:
        file_logs_map = json.loads(log_data)
    except json.JSONDecodeError as e:
        return f"❌ 无法解析日志数据 JSON: {e}"
    
    if not file_logs_map:
        return f"❌ 日志数据为空，无法生成报告"
    
    # 统计信息
    total_files = len(file_logs_map)
    total_logs = sum(len(logs) for logs in file_logs_map.values())
    
    # 生成 HTML 文件名
    html_output_dir = Path("logs")
    html_output_dir.mkdir(exist_ok=True)
    
    safe_timestamp = timestamp.replace(":", "-").replace(" ", "_").replace(".", "-")
    html_file = html_output_dir / f"scene_analysis_{safe_timestamp}.html"
    
    # 生成 HTML 内容
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>场景分析报告 - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            margin-top: 0;
        }}
        .file-section {{
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 12px;
            line-height: 1.5;
            max-height: 400px;
            overflow-y: auto;
        }}
        .meta {{
            color: #666;
            font-size: 14px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .analysis-section {{
            background: #fff9e6;
            border-left: 4px solid #ffc107;
            padding: 20px;
        }}
        .timeline {{
            position: relative;
            padding-left: 30px;
        }}
        .timeline-item {{
            position: relative;
            padding-bottom: 20px;
            border-left: 2px solid #667eea;
            padding-left: 25px;
            margin-left: 10px;
        }}
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -7px;
            top: 0;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
        }}
        .timeline-time {{
            font-weight: bold;
            color: #667eea;
            font-size: 14px;
        }}
        .timeline-event {{
            margin-top: 5px;
            color: #333;
        }}
        .highlight {{
            background: #fff3cd;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .conclusion-box {{
            background: linear-gradient(135deg, #667eea22 0%, #764ba233 100%);
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #667eea;
            margin-top: 15px;
        }}
        .conclusion-box h3 {{
            margin-top: 0;
            color: #667eea;
        }}
        .placeholder {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 场景分析报告</h1>
        <p class="meta">时间点: {timestamp} | 时间窗口: ±{time_window/2}秒</p>
    </div>
    
    <div class="section">
        <h2>📈 统计信息</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_files}</div>
                <div class="stat-label">Events 文件</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_logs}</div>
                <div class="stat-label">日志条目</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{time_window}s</div>
                <div class="stat-label">时间窗口</div>
            </div>
        </div>
    </div>
    
    <!-- SCENE_ANALYSIS_PLACEHOLDER -->
    
    <div class="section">
        <h2>📝 原始日志</h2>
"""
    
    # 按文件添加日志内容
    for file_path, logs in file_logs_map.items():
        log_content = "".join(logs[:200])
        # HTML转义
        log_content = log_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        html_content += f"""
        <div class="file-section">
            <h3>📄 {Path(file_path).name}</h3>
            <p class="meta">共 {len(logs)} 条日志</p>
            <pre>{log_content}</pre>
"""
        if len(logs) > 200:
            html_content += f"            <p class='meta'>... (省略 {len(logs) - 200} 行) ...</p>\n"
        html_content += "        </div>\n"
    
    html_content += """
    </div>
</body>
</html>
"""
    
    # 写入 HTML 文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✅ HTML report generated: {html_file}")
    
    # 生成日志摘要用于分析
    log_summary = ""
    for file_path, logs in file_logs_map.items():
        log_summary += f"\n### 文件: {Path(file_path).name} ({len(logs)} 条)\n"
        log_summary += "```\n"
        log_summary += "".join(logs[:50])  # 只显示前50行用于prompt
        if len(logs) > 50:
            log_summary += f"\n... (省略 {len(logs) - 50} 行) ...\n"
        log_summary += "```\n"
    
    result = f"""
✅ 【步骤3/4完成】HTML 报告已生成

## 报告信息
- **文件路径**: `{html_file.absolute()}`
- **分析文件数**: {total_files}
- **日志条目数**: {total_logs}
- **时间点**: {timestamp}
- **时间窗口**: ±{time_window/2}秒

---

## 【步骤4/4】AI 场景分析任务

请根据以下日志内容，完成场景分析：

{log_summary}

### 分析要求
请详细分析并说明：
1. **主要操作**: 用户在做什么操作（如：打开应用、页面跳转、手势操作等）
2. **涉及组件**: 涉及哪些应用、Activity、系统服务
3. **操作流程**: 按时间顺序梳理关键事件
4. **性能数据**: 如果有启动时间、响应时间等性能指标，请标注

### 更新 HTML 报告
完成分析后，请使用 `search_replace` 工具更新 HTML 文件：
- 文件路径: `{html_file.absolute()}`
- 将 `<!-- SCENE_ANALYSIS_PLACEHOLDER -->` 替换为完整的场景分析 HTML 内容

### HTML 模板示例
```html
<div class="section analysis-section">
    <h2>🎯 场景分析</h2>
    
    <div class="conclusion-box">
        <h3>📱 用户操作</h3>
        <p>[描述用户的主要操作]</p>
    </div>
    
    <h3>⏱️ 操作时间线</h3>
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-time">HH:MM:SS.xxx</div>
            <div class="timeline-event">[事件描述]</div>
        </div>
    </div>
    
    <h3>🔧 涉及组件</h3>
    <table>
        <tr><th>组件类型</th><th>名称</th><th>作用</th></tr>
        <tr><td>应用</td><td>[包名]</td><td>[作用说明]</td></tr>
    </table>
    
    <h3>✅ 分析结论</h3>
    <p>[总结性描述]</p>
</div>
```

**现在请开始分析日志并更新 HTML 报告。**
"""
    
    return result

