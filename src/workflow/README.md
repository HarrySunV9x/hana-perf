# Workflow 工作流引擎

> 基于状态机模式的 MCP 工作流引擎，解决 AI Agent 多步骤任务中的上下文丢失问题

---

## 📋 目录

- [问题背景](#问题背景)
- [设计理念](#设计理念)
- [架构概览](#架构概览)
- [核心组件](#核心组件)
- [工作流程](#工作流程)
- [使用指南](#使用指南)
- [扩展开发](#扩展开发)
- [与 n8n/Dify 的对比](#与-n8ndify-的对比)

---

## 问题背景

### 传统 MCP 工具的困境

在使用 MCP（Model Context Protocol）工具时，当任务涉及多个步骤时，AI Agent 面临以下挑战：

```
┌─────────────────────────────────────────────────────────────────┐
│                        传统模式的问题                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   用户: "分析 /logs 目录下 09:27:29 时刻的日志"                    │
│                                                                  │
│   AI 需要记住:                                                    │
│   ├── 步骤1: 搜索 events 文件 ──────────────────────┐            │
│   ├── 步骤2: 对每个文件提取日志 ────────────────────┤ 上下文越来越长 │
│   ├── 步骤3: 解析时间线 ────────────────────────────┤            │
│   ├── 步骤4: 生成分析 ──────────────────────────────┤            │
│   └── 步骤5: 合并报告 ──────────────────────────────┘            │
│                                                                  │
│   问题:                                                          │
│   ❌ AI 可能忘记后续步骤                                          │
│   ❌ 上下文过长导致遗漏细节                                        │
│   ❌ 中途失败需要从头开始                                          │
│   ❌ 无法查看执行进度                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 解决方案

本工作流引擎通过**状态外置**和**步骤拆分**解决这些问题：

```
┌─────────────────────────────────────────────────────────────────┐
│                        工作流模式                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   状态文件 (JSON) ─────────────────────────────────────────────  │
│   ├── workflow_id: "scene_20241210_123456"                       │
│   ├── current_step: 2                                            │
│   ├── params: { log_path, timestamp, time_window }               │
│   ├── global_data: { events_files: [...], log_data: {...} }     │
│   └── html_fragments: [ "01_header.html", "02_stats.html" ]     │
│                                                                  │
│   每个 MCP 工具:                                                  │
│   ├── 读取状态 → 获取所需数据                                     │
│   ├── 执行任务 → 产生输出                                         │
│   ├── 更新状态 → 保存结果                                         │
│   └── 返回指引 → 告诉 AI 下一步                                   │
│                                                                  │
│   优势:                                                          │
│   ✅ AI 不需要记住所有步骤                                        │
│   ✅ 每个工具返回下一步调用说明                                    │
│   ✅ 状态持久化，支持断点续传                                      │
│   ✅ 可随时查看执行进度                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 设计理念

### 核心原则

| 原则 | 说明 |
|------|------|
| **状态外置** | 工作流状态存储在 JSON 文件中，而非依赖 AI 的上下文记忆 |
| **步骤原子化** | 每个步骤是独立的、可复用的单元，有明确的输入输出 |
| **渐进式生成** | 每个步骤生成 HTML 片段，最后合并成完整报告 |
| **自引导执行** | 每个工具执行完毕后，返回下一步的调用指引 |

### 借鉴来源

本设计借鉴了多个成熟的工作流系统：

```
┌─────────────┬────────────────────────────────────────────────────┐
│   系统       │   借鉴的概念                                        │
├─────────────┼────────────────────────────────────────────────────┤
│   n8n       │   - Node（节点）概念：每个操作是独立单元              │
│             │   - Execution（执行）：工作流实例有独立状态            │
│             │   - Node Registry：节点注册和发现机制                 │
├─────────────┼────────────────────────────────────────────────────┤
│   Dify      │   - Workflow 模式：可视化编排                        │
│             │   - 变量传递：节点间通过变量共享数据                   │
│             │   - Block 概念：功能区块                              │
├─────────────┼────────────────────────────────────────────────────┤
│   Airflow   │   - DAG 状态管理                                     │
│             │   - Task 依赖关系                                    │
│             │   - 断点续传机制                                      │
├─────────────┼────────────────────────────────────────────────────┤
│   Jenkins   │   - Pipeline Stage 概念                              │
│             │   - 步骤进度可视化                                    │
└─────────────┴────────────────────────────────────────────────────┘
```

---

## 架构概览

### 目录结构

```
src/workflow/
├── __init__.py              # 模块入口，导出公共 API
│
├── core/                    # 🔧 核心组件
│   ├── state.py            # 状态管理器 - 工作流状态持久化
│   ├── components.py       # HTML 组件库 - 可复用的 UI 组件
│   ├── builder.py          # 报告构建器 - 合并 HTML 片段
│   └── registry.py         # 步骤注册表 - 步骤和工作流定义
│
├── steps/                   # 📋 步骤实现
│   ├── base.py             # 步骤抽象基类
│   ├── init_workflow.py    # 步骤1: 初始化工作流
│   ├── search_files.py     # 步骤2: 搜索日志文件
│   ├── extract_logs.py     # 步骤3: 提取日志
│   ├── analyze_timeline.py # 步骤4: 分析时间线
│   └── finalize_report.py  # 步骤6: 生成最终报告
│
├── templates/               # 🎨 HTML 模板资源
│   └── base.html           # 基础 HTML 模板
│
└── tools/                   # 🔌 MCP 工具
    └── mcp_tools.py        # MCP 工具注册
```

### 组件关系图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              MCP Server                                   │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        tools/mcp_tools.py                          │  │
│  │   register_workflow_tools(mcp)                                      │  │
│  │   ├── init_scene_workflow()                                         │  │
│  │   ├── search_events()                                               │  │
│  │   ├── extract_logs()                                                │  │
│  │   ├── analyze_timeline()                                            │  │
│  │   ├── generate_analysis()                                           │  │
│  │   └── finalize_report()                                             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                          steps/*.py                                 │  │
│  │   BaseStep (抽象基类)                                                │  │
│  │   ├── execute() ──────────→ 执行业务逻辑                             │  │
│  │   ├── generate_html() ────→ 生成 HTML 片段                           │  │
│  │   └── run() ──────────────→ 完整执行流程                             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                    ┌───────────────┼───────────────┐                      │
│                    ▼               ▼               ▼                      │
│  ┌──────────────────────┐ ┌──────────────┐ ┌──────────────────────┐      │
│  │   core/state.py      │ │ core/        │ │   core/builder.py   │      │
│  │   WorkflowState      │ │ components.py│ │   ReportBuilder     │      │
│  │   ├── create()       │ │ HTMLComponents│ │   ├── add_fragment()│      │
│  │   ├── load()         │ │ ├── header() │ │   └── build()       │      │
│  │   ├── complete_step()│ │ ├── timeline()│ │                     │      │
│  │   └── get_next_step()│ │ └── table()  │ │                     │      │
│  └──────────────────────┘ └──────────────┘ └──────────────────────┘      │
│             │                                          │                  │
│             ▼                                          ▼                  │
│  ┌──────────────────────────────────────────────────────────────────────┐│
│  │                        文件系统                                       ││
│  │   logs/workflows/{workflow_id}/                                       ││
│  │   ├── state.json           # 工作流状态                               ││
│  │   ├── fragments/           # HTML 片段                                ││
│  │   │   ├── 01_init_workflow.html                                      ││
│  │   │   ├── 02_search_files.html                                       ││
│  │   │   └── ...                                                         ││
│  │   └── report.html          # 最终报告                                 ││
│  └──────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. WorkflowState - 状态管理器

**文件**: `core/state.py`

**职责**: 管理工作流的生命周期和状态持久化

```python
# 核心数据结构
@dataclass 
class WorkflowContext:
    workflow_id: str           # 工作流唯一标识
    workflow_type: str         # 工作流类型，如 "scene_analysis"
    status: WorkflowStatus     # running / completed / failed
    
    params: dict               # 输入参数
    steps: list[str]           # 步骤列表
    current_step_index: int    # 当前步骤索引
    
    global_data: dict          # 步骤间共享数据（核心！）
    html_fragments: list[str]  # HTML 片段路径列表
```

**关键方法**:

| 方法 | 说明 |
|------|------|
| `create()` | 创建新工作流，初始化状态文件和目录结构 |
| `load()` | 加载现有工作流状态 |
| `complete_step()` | 完成步骤，更新状态，保存 HTML 片段 |
| `get_global_data()` | 获取全局数据（步骤间共享） |
| `get_next_step_info()` | 获取下一步执行信息 |

**状态文件示例** (`state.json`):

```json
{
  "workflow_id": "scene_1028_092729_143052",
  "workflow_type": "scene_analysis",
  "status": "running",
  "created_at": "2024-12-10T14:30:52.123456",
  "updated_at": "2024-12-10T14:31:15.789012",
  
  "params": {
    "log_path": "/path/to/logs",
    "timestamp": "10-28 09:27:29.665281",
    "time_window": 20.0
  },
  
  "steps": ["init_workflow", "search_files", "extract_logs", "analyze_timeline", "generate_analysis", "finalize_report"],
  "current_step_index": 2,
  
  "step_results": {
    "init_workflow": {
      "status": "completed",
      "completed_at": "2024-12-10T14:30:55.000000",
      "output_data": { "workflow_id": "scene_..." }
    },
    "search_files": {
      "status": "completed",
      "completed_at": "2024-12-10T14:31:05.000000",
      "output_data": { "events_files": [...], "files_count": 3 }
    }
  },
  
  "global_data": {
    "events_files": [
      {"path": "/logs/events_1.log", "name": "events_1.log", "size": 102400}
    ],
    "files_count": 3
  },
  
  "html_fragments": [
    "logs/workflows/scene_.../fragments/01_init_workflow.html",
    "logs/workflows/scene_.../fragments/02_search_files.html"
  ]
}
```

---

### 2. HTMLComponents - HTML 组件库

**文件**: `core/components.py`

**职责**: 提供可复用的 HTML UI 组件

**可用组件**:

| 组件 | 方法 | 用途 |
|------|------|------|
| 报告头部 | `header()` | 标题、副标题、元信息 |
| 统计卡片 | `stats_cards()` | 数字统计展示 |
| 垂直时间线 | `timeline_vertical()` | 事件时间轴 |
| 横向时间线 | `timeline_horizontal()` | 进度条/耗时分布 |
| 数据表格 | `table()` | 结构化数据展示 |
| 结论框 | `conclusion_box()` | 高亮提示信息 |
| 日志块 | `log_block()` | 代码/日志展示 |
| Activity 流程 | `activity_flow()` | Activity 切换流程图 |
| 区块容器 | `section()` | 通用内容区块 |

**使用示例**:

```python
from workflow.core.components import HTMLComponents, StatCard, TimelineEvent

# 统计卡片
html = HTMLComponents.stats_cards([
    StatCard(value="5", label="Events 文件", icon="📁"),
    StatCard(value="1.2 MB", label="总大小", icon="💾"),
    StatCard(value="20s", label="时间窗口", icon="⏱️")
])

# 垂直时间线
html = HTMLComponents.timeline_vertical([
    TimelineEvent(time="09:27:29.100", title="焦点切换", description="Launcher → Camera"),
    TimelineEvent(time="09:27:29.500", title="Activity 启动", description="CameraActivity")
])

# 包装成区块
html = HTMLComponents.section(
    title="统计信息",
    content=stats_html,
    icon="📈"
)
```

---

### 3. ReportBuilder - 报告构建器

**文件**: `core/builder.py`

**职责**: 合并所有 HTML 片段，生成最终报告

**工作流程**:

```
┌─────────────────────────────────────────────────────────────────┐
│   ReportBuilder                                                  │
│                                                                  │
│   fragments = []                                                 │
│                                                                  │
│   add_fragment_from_file("01_header.html")     →  fragments[0]  │
│   add_fragment_from_file("02_stats.html")      →  fragments[1]  │
│   add_fragment_from_file("03_logs.html")       →  fragments[2]  │
│   add_fragment_from_file("04_timeline.html")   →  fragments[3]  │
│   add_fragment_from_file("05_analysis.html")   →  fragments[4]  │
│                                                                  │
│   build("report.html")                                           │
│   ├── 注入基础样式 (CSS)                                         │
│   ├── 合并所有片段                                               │
│   ├── 注入脚本 (JavaScript)                                      │
│   └── 输出完整 HTML 文件                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**内置样式**: Cyberpunk 风格的深色主题，包含：
- CSS 变量系统
- 响应式布局
- 动画效果
- 完整的组件样式

---

### 4. StepRegistry - 步骤注册表

**文件**: `core/registry.py`

**职责**: 管理步骤和工作流的定义，类似 n8n 的 Node Registry

**核心概念**:

```python
@dataclass
class StepDefinition:
    name: str              # 步骤唯一标识
    display_name: str      # 显示名称
    description: str       # 描述
    step_type: StepType    # 类型: INIT/SEARCH/EXTRACT/ANALYZE/FINALIZE
    mcp_tool_name: str     # 对应的 MCP 工具名
    inputs: list[str]      # 需要的输入数据
    outputs: list[str]     # 产出的输出数据
    generates_html: bool   # 是否生成 HTML

@dataclass
class WorkflowDefinition:
    name: str              # 工作流标识
    display_name: str      # 显示名称
    steps: list[str]       # 步骤列表（按顺序）
    params: dict           # 参数定义
```

**已注册的步骤**:

```
scene_analysis 工作流
├── init_workflow     [INIT]      → 初始化工作流
├── search_files      [SEARCH]    → 搜索 Events 文件
├── extract_logs      [EXTRACT]   → 提取日志
├── analyze_timeline  [ANALYZE]   → 分析时间线
├── generate_analysis [ANALYZE]   → AI 生成分析
└── finalize_report   [FINALIZE]  → 生成最终报告
```

---

### 5. BaseStep - 步骤抽象基类

**文件**: `steps/base.py`

**职责**: 定义步骤的标准接口和执行流程

**执行流程** (`run()` 方法):

```
┌─────────────────────────────────────────────────────────────────┐
│   BaseStep.run()                                                 │
│                                                                  │
│   1. 验证工作流存在                                              │
│      └── if not exists: return "❌ 工作流不存在"                  │
│                                                                  │
│   2. 验证输入数据完整                                            │
│      └── 检查 definition.inputs 中的数据是否都存在               │
│                                                                  │
│   3. 标记步骤开始                                                │
│      └── state.start_step(step_name)                            │
│                                                                  │
│   4. 执行业务逻辑                                                │
│      └── output_data = await self.execute()  ← 子类实现          │
│                                                                  │
│   5. 生成 HTML 片段                                              │
│      └── html = self.generate_html(output_data)  ← 子类实现      │
│                                                                  │
│   6. 完成步骤                                                    │
│      └── state.complete_step(step_name, output_data, html)      │
│                                                                  │
│   7. 返回结果和下一步指引                                        │
│      └── return self._format_result(output_data)                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**子类需要实现的方法**:

```python
class MyStep(BaseStep):
    step_name = "my_step"
    
    async def execute(self) -> dict:
        """执行业务逻辑，返回输出数据"""
        input_data = self.get_input("some_key")
        # ... 处理逻辑
        return {"result": "..."}
    
    def generate_html(self, output_data: dict) -> str:
        """根据输出数据生成 HTML 片段"""
        return HTMLComponents.section(
            title="结果",
            content=f"<p>{output_data['result']}</p>"
        )
```

---

## 工作流程

### 完整执行流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           场景分析工作流                                      │
└─────────────────────────────────────────────────────────────────────────────┘

用户: "分析 /logs 目录下 10-28 09:27:29 的日志"

                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  步骤 1: init_scene_workflow                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  输入: log_path="/logs", timestamp="10-28 09:27:29", time_window=20 │    │
│  │  处理: 创建工作流目录和状态文件                                        │    │
│  │  输出: workflow_id="scene_1028_092729_143052"                        │    │
│  │  HTML: 01_init_workflow.html (报告头部)                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  返回: "✅ 工作流已初始化\n📍 下一步: 调用 search_events"                    │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  步骤 2: search_events                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  输入: workflow_id (自动从状态读取 log_path)                          │    │
│  │  处理: 遍历目录，搜索包含 "events" 的文件                             │    │
│  │  输出: events_files=[...], files_count=5                             │    │
│  │  HTML: 02_search_files.html (统计卡片)                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  返回: "✅ 找到 5 个文件\n📍 下一步: 调用 extract_logs"                      │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  步骤 3: extract_logs                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  输入: workflow_id (自动读取 events_files, timestamp, time_window)    │    │
│  │  处理: 遍历文件，过滤 input_focus 关键字和时间范围                     │    │
│  │  输出: file_logs_map={...}, total_logs=128                           │    │
│  │  HTML: 03_extract_logs.html (日志代码块)                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  返回: "✅ 提取 128 条日志\n📍 下一步: 调用 analyze_timeline"                │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  步骤 4: analyze_timeline                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  输入: workflow_id (自动读取 file_logs_map)                           │    │
│  │  处理: 解析日志，提取时间、包名、Activity                              │    │
│  │  输出: timeline_events=[...], activity_flow=[...]                    │    │
│  │  HTML: 04_analyze_timeline.html (时间线和流程图)                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  返回: "✅ 发现 15 个事件\n📍 下一步: 调用 generate_analysis"                │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  步骤 5: generate_analysis                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  输入: workflow_id, analysis_content (AI 提供的分析内容)              │    │
│  │  处理: 包装分析内容为 HTML                                            │    │
│  │  输出: analysis_generated=true                                       │    │
│  │  HTML: 05_generate_analysis.html (分析结论)                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  返回: "✅ 分析已生成\n📍 下一步: 调用 finalize_report"                      │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  步骤 6: finalize_report                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  输入: workflow_id                                                    │    │
│  │  处理: 合并所有 HTML 片段，注入样式和脚本                              │    │
│  │  输出: report_path="/path/to/report.html"                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  返回: "🎉 报告已生成: /path/to/report.html"                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 数据流动

```
global_data 数据流:

init_workflow
    └── { workflow_id, log_path, timestamp, time_window }
                    │
                    ▼
search_files
    └── + { events_files: [...], files_count: 5 }
                    │
                    ▼
extract_logs
    └── + { file_logs_map: {...}, total_logs: 128 }
                    │
                    ▼
analyze_timeline
    └── + { timeline_events: [...], activity_flow: [...] }
                    │
                    ▼
generate_analysis
    └── + { analysis_generated: true }
                    │
                    ▼
finalize_report
    └── + { report_path: "..." }
```

---

## 使用指南

### 1. 集成到 MCP Server

```python
# main.py
from common.mcp import mcp
from workflow.tools import register_workflow_tools

# 注册工作流工具
register_workflow_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### 2. AI Agent 调用流程

AI 只需按照每个工具返回的指引，依次调用：

```
1. 调用 init_scene_workflow(log_path, timestamp, time_window)
   → 获得 workflow_id

2. 调用 search_events(workflow_id)
   → 搜索文件

3. 调用 extract_logs(workflow_id)
   → 提取日志

4. 调用 analyze_timeline(workflow_id)
   → 分析时间线

5. 调用 generate_analysis(workflow_id, analysis_content)
   → AI 提供分析内容

6. 调用 finalize_report(workflow_id)
   → 生成最终报告
```

### 3. 辅助工具

```python
# 查看工作流状态
get_workflow_status(workflow_id)

# 列出所有工作流（支持断点续传）
list_workflows()
```

---

## 扩展开发

### 添加新步骤

1. **创建步骤文件** `steps/my_step.py`:

```python
from workflow.steps.base import BaseStep
from workflow.core.components import HTMLComponents

class MyStep(BaseStep):
    step_name = "my_step"
    
    async def execute(self) -> dict:
        # 获取输入数据
        input_data = self.get_input("previous_output")
        
        # 业务逻辑
        result = process(input_data)
        
        # 返回输出数据（会自动保存到 global_data）
        return {"my_output": result}
    
    def generate_html(self, output_data: dict) -> str:
        return HTMLComponents.section(
            title="我的步骤",
            content=f"<p>{output_data['my_output']}</p>"
        )
```

2. **注册步骤定义** `core/registry.py`:

```python
self.register_step(StepDefinition(
    name="my_step",
    display_name="我的步骤",
    description="执行某些操作",
    step_type=StepType.TRANSFORM,
    mcp_tool_name="my_tool",
    inputs=["previous_output"],
    outputs=["my_output"],
    order=5
))
```

3. **注册 MCP 工具** `tools/mcp_tools.py`:

```python
@mcp.tool()
async def my_tool(workflow_id: str) -> str:
    from ..steps.my_step import MyStep
    step = MyStep(workflow_id)
    return await step.run()
```

### 添加新的 HTML 组件

在 `core/components.py` 中添加静态方法:

```python
@staticmethod
def my_component(data: list[dict]) -> str:
    items_html = ""
    for item in data:
        items_html += f"<div>{item['value']}</div>"
    return f'<div class="my-component">{items_html}</div>'
```

---

## 与 n8n/Dify 的对比

| 特性 | n8n | Dify | 本方案 |
|------|-----|------|--------|
| **定位** | 通用自动化平台 | AI 应用开发平台 | MCP 工具编排 |
| **编排方式** | 可视化 + JSON | 可视化 DAG | 代码定义 |
| **执行环境** | 服务端 | 服务端 | MCP Server |
| **状态存储** | 数据库 | 数据库 | JSON 文件 |
| **AI 集成** | 通过节点 | 原生支持 | 原生 MCP 工具 |
| **学习曲线** | 中等 | 中等 | 低（Python） |
| **适用场景** | 企业自动化 | AI 应用 | AI Agent 增强 |

---

## 总结

本工作流引擎通过以下机制解决了 AI Agent 多步骤任务的挑战：

1. **状态外置**: 使用 JSON 文件持久化状态，AI 不需要记住上下文
2. **步骤拆分**: 每个 MCP 工具只做一件事，简单可靠
3. **自动引导**: 每个工具执行后返回下一步调用说明
4. **渐进生成**: 每步生成 HTML 片段，最后合并成完整报告
5. **断点续传**: 可随时查看进度，从失败点继续执行

这种设计让 AI Agent 能够可靠地执行复杂的多步骤任务，而不会因为上下文过长而丢失关键信息。

