#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Input Focus Log Analyzer
分析 Android input_focus 日志，可视化展示指定时间窗口内的焦点变化轨迹
"""

import re
import sys
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class ActivityMapper:
    """Activity 识别映射器（完整路径精准匹配）"""
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.activity_mapping = self.config.get('activity_mapping', {})
        self.special_windows = self.config.get('special_windows', {})
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """加载配置文件"""
        if config_path is None:
            # 默认配置文件在脚本同目录
            script_dir = Path(__file__).parent
            config_path = script_dir / "activity_config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件未找到: {config_path}")
            print(f"请确保 activity_config.json 存在")
            return {"activity_mapping": {}, "special_windows": {}}
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件解析错误: {e}")
            print(f"请检查 JSON 格式是否正确")
            return {"activity_mapping": {}, "special_windows": {}}
    
    def map_activity(self, package_activity: str, window_full: str, show_path: bool = True) -> str:
        """
        映射完整的 package/activity 到友好名称（精准匹配）
        
        Args:
            package_activity: 完整的 package/activity 路径
            window_full: 完整窗口字符串
            show_path: 是否显示完整路径
            
        Returns:
            格式化的显示名称
        """
        # 1. 检查特殊窗口（优先级最高）
        for special_key, special_name in self.special_windows.items():
            if special_key in window_full:
                return special_name
        
        # 2. 精确匹配完整路径（package/activity）
        if package_activity in self.activity_mapping:
            friendly_name = self.activity_mapping[package_activity]
            if show_path:
                return f"{friendly_name} ({package_activity})"
            else:
                return friendly_name
        
        # 3. 未匹配，显示"未知 + 完整路径"
        return f"❓ 未知 ({package_activity})"


# 全局 ActivityMapper 实例
_activity_mapper = None


def get_activity_mapper() -> ActivityMapper:
    """获取全局 ActivityMapper 实例"""
    global _activity_mapper
    if _activity_mapper is None:
        _activity_mapper = ActivityMapper()
    return _activity_mapper


class FocusEvent:
    """焦点事件类"""
    def __init__(self, timestamp: str, event_type: str, window: str, reason: str, full_line: str):
        self.timestamp = timestamp
        self.event_type = event_type
        self.window = window
        self.reason = reason
        self.full_line = full_line
        self.datetime_obj = self._parse_time(timestamp)
    
    def _parse_time(self, timestamp: str) -> datetime:
        """解析时间字符串 MM-DD HH:MM:SS.mmm"""
        try:
            # 假设是当前年份
            current_year = datetime.now().year
            time_str = f"{current_year}-{timestamp}"
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
        except:
            return None
    
    def get_short_window_name(self) -> str:
        """获取窗口名称（基于完整路径精准匹配，显示完整路径）"""
        if not self.window:
            return "NULL"
        
        mapper = get_activity_mapper()
        
        # 提取完整的 package/activity 路径
        if '/' in self.window:
            parts = self.window.split()
            for part in parts:
                if '/' in part:
                    # 使用完整的 package/activity 路径进行匹配，显示完整路径
                    package_activity = part
                    return mapper.map_activity(package_activity, self.window, show_path=True)
        
        # 特殊窗口（没有 / 的情况）
        return mapper.map_activity(self.window, self.window, show_path=True)
    
    def get_event_icon(self) -> str:
        """获取事件图标"""
        if 'entering' in self.event_type.lower():
            return "→"
        elif 'leaving' in self.event_type.lower():
            return "←"
        elif 'request' in self.event_type.lower():
            return "?"
        else:
            return "·"


def parse_log_file(file_path: str) -> List[FocusEvent]:
    """解析日志文件"""
    events = []
    
    # 正则表达式匹配日志格式
    pattern = r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+\d+\s+\d+\s+\w+\s+input_focus:\s+\[(.*?)\]'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(pattern, line)
                if match:
                    timestamp = match.group(1)
                    content = match.group(2)
                    
                    # 解析事件类型、窗口和原因
                    event_type = ""
                    window = ""
                    reason = ""
                    
                    if 'Focus entering' in content:
                        event_type = "Focus entering"
                        parts = content.split(',reason=')
                        window = parts[0].replace('Focus entering', '').strip()
                        reason = parts[1] if len(parts) > 1 else ""
                    elif 'Focus leaving' in content:
                        event_type = "Focus leaving"
                        parts = content.split(',reason=')
                        window = parts[0].replace('Focus leaving', '').strip()
                        reason = parts[1] if len(parts) > 1 else ""
                    elif 'Focus request' in content:
                        event_type = "Focus request"
                        parts = content.split(',reason=')
                        window = parts[0].replace('Focus request', '').strip()
                        reason = parts[1] if len(parts) > 1 else ""
                    elif 'Requesting to set focus to null' in content:
                        event_type = "Focus to null"
                        window = "null"
                        reason = content.split('reason=')[1] if 'reason=' in content else ""
                    
                    event = FocusEvent(timestamp, event_type, window, reason, line.strip())
                    events.append(event)
    
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误：读取文件时出错 - {e}")
        sys.exit(1)
    
    return events


def parse_time_input(time_str: str, events: List[FocusEvent]) -> datetime:
    """解析用户输入的时间"""
    try:
        current_year = datetime.now().year
        
        # 尝试不同的时间格式
        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%m-%d %H:%M:%S.%f",
            "%m-%d %H:%M:%S",
            "%H:%M:%S.%f",
            "%H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                if fmt.startswith("%Y"):
                    target_time = datetime.strptime(time_str, fmt)
                elif fmt.startswith("%m"):
                    target_time = datetime.strptime(f"{current_year}-{time_str}", "%Y-" + fmt)
                else:
                    # 只有时间，使用日志中第一个事件的日期
                    if events:
                        first_date = events[0].datetime_obj.date()
                        target_time = datetime.strptime(f"{first_date} {time_str}", "%Y-%m-%d " + fmt)
                    else:
                        target_time = datetime.strptime(f"{current_year}-01-01 {time_str}", "%Y-%m-%d " + fmt)
                
                return target_time
            except:
                continue
        
        raise ValueError("无法解析时间格式")
    
    except Exception as e:
        print(f"❌ 时间格式错误：{e}")
        print("支持的格式：")
        print("  - HH:MM:SS (例如: 23:35:11)")
        print("  - HH:MM:SS.mmm (例如: 23:35:11.596)")
        print("  - MM-DD HH:MM:SS (例如: 11-10 23:35:11)")
        print("  - YYYY-MM-DD HH:MM:SS (例如: 2025-11-10 23:35:11)")
        sys.exit(1)


def filter_events_by_time(events: List[FocusEvent], target_time: datetime, window_seconds: int = 10, mode: str = "detailed") -> List[FocusEvent]:
    """筛选时间窗口内的事件，并包含目标时间点前面2次事件"""
    start_time = target_time - timedelta(seconds=window_seconds)
    end_time = target_time + timedelta(seconds=window_seconds)
    
    # 1. 筛选时间窗口内的事件
    filtered = []
    before_target = []  # 目标时间点之前的所有事件
    
    for event in events:
        if not event.datetime_obj:
            continue
            
        # 记录目标时间点之前的所有事件
        if event.datetime_obj < target_time:
            before_target.append(event)
        
        # 时间窗口内的事件
        if start_time <= event.datetime_obj <= end_time:
            # 简化模式：只保留 Focus request 事件
            if mode == "simple":
                if 'request' in event.event_type.lower():
                    filtered.append(event)
            else:
                filtered.append(event)
    
    # 2. 找出目标时间点前面最近的2个事件（如果还没包含）
    if before_target:
        # 按时间排序，取最后2个
        before_target_sorted = sorted(before_target, key=lambda x: x.datetime_obj)
        
        # 简化模式：只取 Focus request
        if mode == "simple":
            before_target_sorted = [e for e in before_target_sorted if 'request' in e.event_type.lower()]
        
        # 取最后2个
        previous_events = before_target_sorted[-2:] if len(before_target_sorted) >= 2 else before_target_sorted
        
        # 将这些事件添加到 filtered 中（如果还没有）
        for prev_event in previous_events:
            if prev_event not in filtered:
                filtered.append(prev_event)
    
    # 3. 按时间排序
    filtered.sort(key=lambda x: x.datetime_obj)
    
    return filtered


def visualize_focus_timeline(events: List[FocusEvent], target_time: datetime, window_seconds: int, mode: str = "detailed"):
    """可视化展示焦点变化时间轴"""
    if not events:
        print("⚠️  指定时间窗口内没有找到焦点事件")
        return
    
    print("\n" + "="*80)
    print(f"📊 焦点变化轨迹分析")
    print(f"⏰ 目标时间: {target_time.strftime('%m-%d %H:%M:%S')}")
    print(f"⏱️  时间窗口: ±{window_seconds}秒")
    print(f"📝 事件数量: {len(events)}")
    mode_text = "简化模式 (仅显示 Focus request)" if mode == "simple" else "详细模式 (显示完整流程)"
    print(f"🔍 显示模式: {mode_text}")
    print("="*80 + "\n")
    
    # 1. 时间轴展示
    print("📍 时间轴视图：\n")
    
    # 标记是否已经显示过目标时间点标记
    target_marker_shown = False
    
    for i, event in enumerate(events):
        time_str = event.timestamp.split()[1]  # 只显示时间部分
        time_diff = (event.datetime_obj - target_time).total_seconds()
        
        # 在目标时间点之前插入分隔标记（在第一个时间>目标时间的事件之前）
        if not target_marker_shown and time_diff >= 0:
            print("   " + "─" * 75)
            print(f"   🎯 目标时间点: {target_time.strftime('%H:%M:%S')}")
            print("   " + "─" * 75)
            target_marker_shown = True
        
        # 标记前置事件（时间窗口之外的）
        start_time = target_time - timedelta(seconds=window_seconds)
        if event.datetime_obj < start_time:
            time_marker = "⬆️"  # 前置事件标记
        elif abs(time_diff) < 0.1:
            time_marker = "🎯"
        else:
            time_marker = "  "
        
        # 时间差显示
        if time_diff >= 0:
            diff_str = f"+{time_diff:.3f}s"
        else:
            diff_str = f"{time_diff:.3f}s"
        
        # 事件类型颜色编码
        icon = event.get_event_icon()
        window_name = event.get_short_window_name()
        
        # 格式化输出
        print(f"{time_marker} {time_str} [{diff_str:>9}] {icon} {event.event_type:15} | {window_name}")
        
        # 显示详细原因（缩进）
        if event.reason:
            print(f"{'':25}   └─ 原因: {event.reason}")
    
    # 如果所有事件都在目标时间点之前，在最后显示目标时间点标记
    if not target_marker_shown:
        print("   " + "─" * 75)
        print(f"   🎯 目标时间点: {target_time.strftime('%H:%M:%S')}")
        print("   " + "─" * 75)
        print("   （目标时间点之后暂无事件）")
    
    # 2. 焦点流转图
    print("\n" + "-"*80)
    print("🔄 焦点流转图：\n")
    
    focus_chain = []
    if mode == "simple":
        # 简化模式：使用 Focus request
        for event in events:
            if 'request' in event.event_type.lower() and 'null' not in event.window.lower():
                focus_chain.append(event.get_short_window_name())
    else:
        # 详细模式：使用 Focus entering
        for event in events:
            if 'entering' in event.event_type.lower():
                focus_chain.append(event.get_short_window_name())
    
    if focus_chain:
        print("    " + "\n    ↓\n    ".join(focus_chain))
    else:
        print("    (无明确的焦点切换事件)")
    
    print("\n" + "="*80 + "\n")


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║        Input Focus Log Analyzer v1.0                      ║
║        Android 焦点日志分析工具                            ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Android Input Focus Log Analyzer - 分析焦点变化轨迹',
        add_help=False  # 自定义帮助信息
    )
    parser.add_argument('file', nargs='?', help='日志文件路径')
    parser.add_argument('time', nargs='?', help='目标时间点')
    parser.add_argument('window', nargs='?', type=int, default=10, help='时间窗口大小（秒）')
    parser.add_argument('--simple', '-s', action='store_true', help='简化模式：仅显示 Focus request 事件')
    parser.add_argument('--detailed', '-d', action='store_true', help='详细模式：显示完整流程（默认）')
    parser.add_argument('--help', '-h', action='store_true', help='显示帮助信息')
    
    # 如果命令行参数不够，进入交互模式
    args = parser.parse_args()
    
    # 显示帮助
    if args.help:
        print("""
使用方法:
    python analyze_focus.py <文件> <时间> [窗口大小] [选项]

参数:
    文件          日志文件路径 (默认: 1.txt)
    时间          目标时间点 (格式: HH:MM:SS 或 MM-DD HH:MM:SS)
    窗口大小       前后时间窗口，单位秒 (默认: 10)

选项:
    --simple, -s  简化模式：仅显示 Focus request 事件
    --detailed, -d 详细模式：显示完整流程（默认）
    --help, -h    显示此帮助信息

示例:
    # 交互模式
    python analyze_focus.py
    
    # 简化模式（推荐）
    python analyze_focus.py 1.txt "23:35:11" 10 --simple
    
    # 详细模式
    python analyze_focus.py 1.txt "23:35:11" 10 --detailed
    
    # 简写
    python analyze_focus.py 1.txt "23:35:11" 10 -s
        """)
        sys.exit(0)
    
    # 确定显示模式
    if args.simple:
        mode = "simple"
    else:
        mode = "detailed"  # 默认详细模式
    
    # 1. 获取文件路径
    if args.file:
        file_path = args.file
    else:
        file_path = input("📁 请输入日志文件路径 (回车使用默认 '1.txt'): ").strip()
        if not file_path:
            file_path = "1.txt"
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        # 尝试在当前脚本目录查找
        script_dir = Path(__file__).parent
        alt_path = script_dir / file_path
        if alt_path.exists():
            file_path = str(alt_path)
        else:
            print(f"❌ 错误：找不到文件 {file_path}")
            sys.exit(1)
    
    print(f"✅ 正在读取文件: {file_path}")
    
    # 2. 解析日志
    events = parse_log_file(file_path)
    print(f"✅ 成功解析 {len(events)} 条焦点事件")
    
    if not events:
        print("❌ 文件中没有找到有效的焦点事件")
        sys.exit(1)
    
    # 显示时间范围
    first_time = events[0].timestamp
    last_time = events[-1].timestamp
    print(f"📅 时间范围: {first_time} ~ {last_time}")
    
    # 3. 获取目标时间
    if args.time:
        time_input = args.time
    else:
        print("\n示例时间格式:")
        print(f"  - {events[0].timestamp.split()[1]} (使用日志中的时间)")
        print(f"  - 23:35:11")
        time_input = input("\n⏰ 请输入目标时间点: ").strip()
    
    target_time = parse_time_input(time_input, events)
    
    # 4. 获取时间窗口大小
    if args.window:
        window_seconds = args.window
    else:
        window_input = input("⏱️  请输入时间窗口大小（秒，回车使用默认10秒）: ").strip()
        window_seconds = int(window_input) if window_input else 10
    
    # 5. 在交互模式下询问显示模式
    if not args.file or not args.time:  # 交互模式
        print("\n显示模式选择:")
        print("  1. 简化模式 - 仅显示 Focus request（推荐，更清晰）")
        print("  2. 详细模式 - 显示完整流程（包括 leaving/entering）")
        mode_input = input("请选择模式 (1/2，回车使用简化模式): ").strip()
        mode = "simple" if mode_input != "2" else "detailed"
    
    # 6. 筛选并可视化
    filtered_events = filter_events_by_time(events, target_time, window_seconds, mode)
    visualize_focus_timeline(filtered_events, target_time, window_seconds, mode)
    
    # 7. 导出选项（仅在交互模式下询问）
    if not args.file or not args.time:  # 交互模式
        try:
            export = input("💾 是否导出详细日志到文件？(y/N): ").strip().lower()
            if export == 'y':
                output_file = f"focus_analysis_{target_time.strftime('%Y%m%d_%H%M%S')}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"Input Focus Analysis Report\n")
                    f.write(f"Target Time: {target_time}\n")
                    f.write(f"Window: ±{window_seconds}s\n")
                    f.write(f"Total Events: {len(filtered_events)}\n")
                    f.write("="*80 + "\n\n")
                    
                    for event in filtered_events:
                        f.write(event.full_line + "\n")
                
                print(f"✅ 已导出到: {output_file}")
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

