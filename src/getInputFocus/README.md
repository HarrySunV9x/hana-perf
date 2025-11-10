# Input Focus Log Analyzer

Android input_focus 日志分析工具，可视化展示指定时间窗口内的焦点变化轨迹。

## 使用方法

### 方式一：快速命令（推荐）⭐

```bash
# 简化模式（推荐）- 仅显示 Focus request，信息更清晰
python analyze_focus.py 1.txt "23:35:11" 10 --simple

# 或使用短参数
python analyze_focus.py 1.txt "23:35:11" 10 -s
```

### 方式二：交互式使用

```bash
python analyze_focus.py
```

然后根据提示输入：
1. 日志文件路径（默认 `1.txt`）
2. 目标时间点
3. 时间窗口大小（默认 10 秒）
4. 显示模式（简化/详细）

### 方式三：Windows 批处理（双击运行）

```bash
analyze.bat
```

## 依赖要求

- Python 3.6+
- 无需额外依赖库（仅使用标准库）

## 项目结构

```
src/getInputFocus/
├── analyze_focus.py           # 主分析脚本
├── analyze.bat                # Windows 批处理启动脚本
├── activity_config.json       # 🆕 Activity 识别配置
├── README.md                  # 本文档
```

