@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Input Focus Log Analyzer 启动脚本
:: Windows 批处理版本

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║        Input Focus Log Analyzer v1.0                      ║
echo ║        Android 焦点日志分析工具                            ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到 Python
    echo.
    echo 请先安装 Python 3.6 或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 运行 Python 脚本
python analyze_focus.py %*

echo.
pause

