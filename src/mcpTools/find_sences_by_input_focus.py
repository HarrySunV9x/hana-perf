from common.mcp import mcp
from common.log import logger

@mcp.tool()
async def find_sences_by_input_focus(log_path: str, timestamp: str, time_window: float = 20.0) -> str:
    """
    【场景分析工作流编排工具】
    
    该工具提供完整的用户场景分析工作流程指导，AI agent 需要按照步骤依次调用其他 MCP 工具完成分析。
    
    工作流程：
    1. 调用 search_events_files - 搜索包含 'events' 的日志文件
    2. 对每个文件调用 find_keyword_logs - 过滤 input_focus 关键字的日志
    3. 调用 generate_scene_report - 生成 HTML 报告框架
    4. AI 分析日志并更新 HTML 报告（使用 search_replace 工具）
    
    Args:
        log_path: 日志目录或文件的路径（字符串格式）
        timestamp: 目标时间戳，格式为 "MM-DD HH:MM:SS.ffffff"，例如 "10-28 09:27:29.665281"
        time_window: 时间窗口大小（秒），默认为 20.0 秒。会在目标时间戳前后各 time_window/2 秒范围内搜索
    
    Returns:
        返回详细的工作流程指导和具体的工具调用说明

    ** 重要： 禁止使用命令行工具
    """
    logger.info(f"Initiating scene analysis workflow for {log_path} at {timestamp}")
    
    workflow_guide = f"""
🎯 **场景分析工作流启动**

## 📋 任务参数
- **日志路径**: {log_path}
- **分析时间点**: {timestamp}
- **时间窗口**: ±{time_window/2}秒（总计 {time_window}秒）

---

## 🔄 工作流程（请按步骤执行）

### ✅ 步骤 1/4: 搜索 Events 文件

**调用工具**: `search_events_files`

**参数**:
```
log_path: "{log_path}"
```

**说明**: 该工具会递归搜索目录中所有包含 'events' 的日志文件，并返回文件列表（JSON格式）。

---

### ✅ 步骤 2/4: 提取 input_focus 日志

收到步骤1的文件列表后，**对每个文件**通过 `find_keyword_logs` 工具搜索input_focus关键字的日志行。

---

### ✅ 步骤 3/4: 生成 HTML 报告框架

收集完所有日志后，调用 `generate_scene_report` 工具生成初步报告。

**调用工具**: `generate_scene_report`

**参数**:
```
timestamp: "{timestamp}"
time_window: {time_window}
log_data: "[步骤2收集的JSON格式日志数据]"
log_path: "{log_path}"
```

**说明**: 该工具会生成带有统计信息和原始日志的 HTML 报告框架，但场景分析部分需要在步骤4中补充。

---

### ✅ 步骤 4/4: AI 场景分析并更新报告

**任务**: 
1. 仔细阅读步骤3返回的日志内容
2. 根据 input_focus 日志分析用户操作场景
3. 使用 `search_replace` 工具更新 HTML 报告
4. 注意事项：严格按照模板生成报告

**分析维度**:
- 📱 **用户操作**: 识别用户的主要操作（打开应用、点击按钮、页面跳转等）
- 🔄 **Activity 切换**: 分析应用和页面的切换顺序
- ⏱️ **activity切换时间线**: 按时间顺序梳理关键事件，要包含对应的包名与Activity，使用纵向时间线展示
- ⏱️ **app时间线**: 按时间顺序梳理关键事件，要包含对应的包名，使用一条横向进度条填充各个app的启动时间，鼠标在对应位置可以显示对应的浮窗
- 🔧 **场景分析**: 根据时间线分析用户进行操作的场景
- 📊 **性能指标**: 如果有启动耗时等性能数据，请标注

**更新 HTML 的工具**: `search_replace`

**参数**:
```
file_path: "[从步骤3获取的HTML文件路径]"
old_string: "<!-- SCENE_ANALYSIS_PLACEHOLDER -->"
new_string: "[你生成的完整分析HTML内容]"
```

**HTML 内容模板** (请根据实际分析填充):
```html
<div class="section analysis-section">  
    <h3>⏱️ 操作时间线</h3>
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-time">09:27:29.123</div>
            <div class="timeline-event">用户点击应用图标 - <span class="highlight">com.example.app</span></div>
        </div>
        <div class="timeline-item">
            <div class="timeline-time">09:27:29.456</div>
            <div class="timeline-event">系统启动微信(com.tencent.mm)的MainActivity</div>
        </div>
        <!-- 根据实际日志添加更多时间线项 -->
    </div>
    
    <h3>🔧 场景分析</h3>
    <div class="conclusion-box">
        <h3>📱 用户操作场景</h3>
        <p><strong>[主要操作描述]</strong></p>
        <p>[详细说明用户在做什么，例如：用户在时间点 XX:XX 打开了相机应用，从主屏幕点击相机图标启动]</p>
    </div>
    
    <h3>✅ 分析结论</h3>
    <div class="conclusion-box">
        <p>[总结用户的完整操作流程和场景]</p>
        <p>例如：用户在 09:27:29 时刻启动了相机应用，整个启动过程涉及从 Launcher 到 Camera 的焦点切换，
        系统响应及时，未发现明显的性能问题。</p>
    </div>
</div>
```

---

## 🚀 开始执行

请现在开始执行**步骤 1**，调用 `search_events_files` 工具。

完成每个步骤后，请继续下一步，直到完成完整的场景分析报告。
"""
    
    return workflow_guide