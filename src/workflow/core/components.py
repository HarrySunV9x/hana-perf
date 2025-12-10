"""
HTML 组件库 - 提供所有报告需要的 HTML 组件

设计理念：
- 每个组件是独立的、可复用的
- 组件接收结构化数据，输出 HTML 字符串
- 支持多种样式主题
"""

from typing import Optional
from dataclasses import dataclass
import html


@dataclass
class TimelineEvent:
    """时间线事件"""
    time: str
    title: str
    description: str = ""
    icon: str = ""
    highlight: bool = False


@dataclass
class StatCard:
    """统计卡片"""
    value: str
    label: str
    icon: str = ""
    color: str = ""


@dataclass
class TableRow:
    """表格行"""
    cells: list[str]
    highlight: bool = False


class HTMLComponents:
    """
    HTML 组件生成器
    
    使用方式：
        components = HTMLComponents()
        html = components.header("标题", "副标题")
    """
    
    @staticmethod
    def escape(text: str) -> str:
        """HTML 转义"""
        return html.escape(str(text))
    
    # ==================== 布局组件 ====================
    
    @staticmethod
    def section(
        title: str,
        content: str,
        icon: str = "📋",
        section_id: str = "",
        css_class: str = ""
    ) -> str:
        """
        通用区块容器
        
        Args:
            title: 区块标题
            content: 区块内容（HTML）
            icon: 标题图标
            section_id: HTML id 属性
            css_class: 额外的 CSS 类
        """
        id_attr = f'id="{section_id}"' if section_id else ""
        return f"""
<div class="section {css_class}" {id_attr}>
    <h2 class="section-title">{icon} {HTMLComponents.escape(title)}</h2>
    <div class="section-content">
        {content}
    </div>
</div>
"""
    
    @staticmethod
    def header(
        title: str,
        subtitle: str = "",
        timestamp: str = "",
        extra_info: dict = None
    ) -> str:
        """
        报告头部
        
        Args:
            title: 主标题
            subtitle: 副标题
            timestamp: 时间戳
            extra_info: 额外信息 {"label": "value"}
        """
        meta_items = []
        if timestamp:
            meta_items.append(f'<span class="meta-item">🕐 {HTMLComponents.escape(timestamp)}</span>')
        
        if extra_info:
            for label, value in extra_info.items():
                meta_items.append(
                    f'<span class="meta-item">{HTMLComponents.escape(label)}: {HTMLComponents.escape(value)}</span>'
                )
        
        meta_html = " | ".join(meta_items) if meta_items else ""
        subtitle_html = f'<p class="header-subtitle">{HTMLComponents.escape(subtitle)}</p>' if subtitle else ""
        
        return f"""
<header class="report-header">
    <h1 class="header-title">{HTMLComponents.escape(title)}</h1>
    {subtitle_html}
    <div class="header-meta">{meta_html}</div>
</header>
"""
    
    # ==================== 数据展示组件 ====================
    
    @staticmethod
    def stats_cards(stats: list[StatCard]) -> str:
        """
        统计卡片组
        
        Args:
            stats: StatCard 列表
        """
        cards_html = ""
        for stat in stats:
            icon_html = f'<span class="stat-icon">{stat.icon}</span>' if stat.icon else ""
            style = f'style="--card-color: {stat.color};"' if stat.color else ""
            
            cards_html += f"""
        <div class="stat-card" {style}>
            {icon_html}
            <div class="stat-value">{HTMLComponents.escape(stat.value)}</div>
            <div class="stat-label">{HTMLComponents.escape(stat.label)}</div>
        </div>
"""
        
        return f'<div class="stats-grid">{cards_html}</div>'
    
    @staticmethod
    def table(
        headers: list[str],
        rows: list[TableRow],
        caption: str = "",
        sortable: bool = False
    ) -> str:
        """
        数据表格
        
        Args:
            headers: 表头列表
            rows: TableRow 列表
            caption: 表格标题
            sortable: 是否可排序
        """
        caption_html = f"<caption>{HTMLComponents.escape(caption)}</caption>" if caption else ""
        sortable_class = "sortable" if sortable else ""
        
        th_html = "".join([
            f'<th>{HTMLComponents.escape(h)}</th>' for h in headers
        ])
        
        tr_html = ""
        for row in rows:
            row_class = "highlight" if row.highlight else ""
            td_html = "".join([
                f'<td>{HTMLComponents.escape(cell)}</td>' for cell in row.cells
            ])
            tr_html += f'<tr class="{row_class}">{td_html}</tr>\n'
        
        return f"""
<table class="data-table {sortable_class}">
    {caption_html}
    <thead><tr>{th_html}</tr></thead>
    <tbody>{tr_html}</tbody>
</table>
"""
    
    # ==================== 时间线组件 ====================
    
    @staticmethod
    def timeline_vertical(
        events: list[TimelineEvent],
        title: str = ""
    ) -> str:
        """
        垂直时间线
        
        Args:
            events: TimelineEvent 列表
            title: 时间线标题
        """
        title_html = f'<h3 class="timeline-title">{HTMLComponents.escape(title)}</h3>' if title else ""
        
        items_html = ""
        for event in events:
            highlight_class = "timeline-item--highlight" if event.highlight else ""
            icon = event.icon or "●"
            desc_html = f'<p class="timeline-desc">{HTMLComponents.escape(event.description)}</p>' if event.description else ""
            
            items_html += f"""
        <div class="timeline-item {highlight_class}">
            <div class="timeline-marker">{icon}</div>
            <div class="timeline-time">{HTMLComponents.escape(event.time)}</div>
            <div class="timeline-content">
                <h4 class="timeline-event-title">{HTMLComponents.escape(event.title)}</h4>
                {desc_html}
            </div>
        </div>
"""
        
        return f"""
<div class="timeline-vertical">
    {title_html}
    <div class="timeline-items">{items_html}</div>
</div>
"""
    
    @staticmethod
    def timeline_horizontal(
        events: list[dict],
        total_duration: float,
        title: str = ""
    ) -> str:
        """
        横向时间线/进度条 - 用于展示 App 启动时间分布
        
        Args:
            events: [{"name": "App名", "start": 0, "duration": 100, "color": "#xxx"}]
            total_duration: 总时长（毫秒）
            title: 时间线标题
        """
        title_html = f'<h3 class="timeline-title">{HTMLComponents.escape(title)}</h3>' if title else ""
        
        segments_html = ""
        for event in events:
            width_percent = (event["duration"] / total_duration) * 100
            left_percent = (event.get("start", 0) / total_duration) * 100
            color = event.get("color", "#6366f1")
            
            segments_html += f"""
        <div class="timeline-segment" 
             style="left: {left_percent}%; width: {width_percent}%; background-color: {color};"
             data-name="{HTMLComponents.escape(event['name'])}"
             data-duration="{event['duration']}ms">
            <span class="segment-label">{HTMLComponents.escape(event['name'])}</span>
            <div class="segment-tooltip">
                <strong>{HTMLComponents.escape(event['name'])}</strong><br>
                耗时: {event['duration']}ms
            </div>
        </div>
"""
        
        return f"""
<div class="timeline-horizontal">
    {title_html}
    <div class="progress-track">
        {segments_html}
    </div>
    <div class="time-axis">
        <span class="time-start">0ms</span>
        <span class="time-end">{total_duration}ms</span>
    </div>
</div>
"""
    
    # ==================== 内容组件 ====================
    
    @staticmethod
    def conclusion_box(
        title: str,
        content: str,
        box_type: str = "info"
    ) -> str:
        """
        结论/提示框
        
        Args:
            title: 框标题
            content: 内容（支持 HTML）
            box_type: 类型 info/success/warning/error
        """
        icons = {
            "info": "💡",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        icon = icons.get(box_type, "📌")
        
        return f"""
<div class="conclusion-box conclusion-box--{box_type}">
    <h3 class="conclusion-title">{icon} {HTMLComponents.escape(title)}</h3>
    <div class="conclusion-content">{content}</div>
</div>
"""
    
    @staticmethod
    def log_block(
        filename: str,
        content: str,
        line_count: int,
        language: str = "log",
        max_lines: int = 200,
        collapsible: bool = True
    ) -> str:
        """
        日志代码块
        
        Args:
            filename: 文件名
            content: 日志内容
            line_count: 总行数
            language: 语言类型
            max_lines: 最大显示行数
            collapsible: 是否可折叠
        """
        # 转义内容
        escaped_content = HTMLComponents.escape(content)
        
        # 截断提示
        truncated_html = ""
        if line_count > max_lines:
            truncated_html = f'<div class="log-truncated">⚠️ 显示前 {max_lines} 行，共 {line_count} 行</div>'
        
        collapse_attrs = 'open' if not collapsible else ''
        
        return f"""
<details class="log-block" {collapse_attrs}>
    <summary class="log-header">
        <span class="log-filename">📄 {HTMLComponents.escape(filename)}</span>
        <span class="log-meta">{line_count} 行</span>
    </summary>
    <div class="log-content">
        <pre><code class="language-{language}">{escaped_content}</code></pre>
        {truncated_html}
    </div>
</details>
"""
    
    @staticmethod
    def key_value_list(items: dict, title: str = "") -> str:
        """
        键值对列表
        
        Args:
            items: {"key": "value"} 字典
            title: 列表标题
        """
        title_html = f'<h4 class="kv-title">{HTMLComponents.escape(title)}</h4>' if title else ""
        
        items_html = ""
        for key, value in items.items():
            items_html += f"""
        <div class="kv-item">
            <span class="kv-key">{HTMLComponents.escape(key)}</span>
            <span class="kv-value">{HTMLComponents.escape(str(value))}</span>
        </div>
"""
        
        return f"""
<div class="kv-list">
    {title_html}
    {items_html}
</div>
"""
    
    @staticmethod
    def tag_list(tags: list[str], title: str = "") -> str:
        """
        标签列表
        
        Args:
            tags: 标签列表
            title: 列表标题
        """
        title_html = f'<h4 class="tags-title">{HTMLComponents.escape(title)}</h4>' if title else ""
        tags_html = "".join([
            f'<span class="tag">{HTMLComponents.escape(tag)}</span>' for tag in tags
        ])
        
        return f"""
<div class="tag-list">
    {title_html}
    <div class="tags">{tags_html}</div>
</div>
"""
    
    @staticmethod
    def activity_flow(activities: list[dict]) -> str:
        """
        Activity 流程图
        
        Args:
            activities: [{"package": "com.xxx", "activity": "MainActivity", "time": "09:27:29"}]
        """
        items_html = ""
        for i, activity in enumerate(activities):
            arrow = '<div class="flow-arrow">→</div>' if i < len(activities) - 1 else ""
            
            items_html += f"""
        <div class="flow-item">
            <div class="flow-time">{HTMLComponents.escape(activity.get('time', ''))}</div>
            <div class="flow-box">
                <div class="flow-package">{HTMLComponents.escape(activity.get('package', ''))}</div>
                <div class="flow-activity">{HTMLComponents.escape(activity.get('activity', ''))}</div>
            </div>
        </div>
        {arrow}
"""
        
        return f'<div class="activity-flow">{items_html}</div>'
    
    # ==================== 占位符组件 ====================
    
    @staticmethod
    def placeholder(
        placeholder_id: str,
        description: str = ""
    ) -> str:
        """
        占位符 - 用于后续替换
        
        Args:
            placeholder_id: 占位符 ID
            description: 描述（会显示在注释中）
        """
        return f"""
<!-- PLACEHOLDER:{placeholder_id} -->
<!-- {description} -->
<!-- END_PLACEHOLDER:{placeholder_id} -->
"""
    
    @staticmethod
    def divider(text: str = "") -> str:
        """分隔线"""
        if text:
            return f'<div class="divider"><span>{HTMLComponents.escape(text)}</span></div>'
        return '<hr class="divider" />'

