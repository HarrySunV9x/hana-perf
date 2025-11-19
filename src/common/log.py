import logging
import sys
from pathlib import Path

# 创建全局 logger 实例
logger = logging.getLogger("hana-perf")
logger.setLevel(logging.INFO)

# 确保不重复添加 handler
if not logger.handlers:
    # 文件 handler
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(
        log_dir / "hana-perf.log",
        encoding="utf-8",
        mode="a"
    )
    file_handler.setLevel(logging.INFO)
    
    # 控制台 handler（可选）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 导出 logger 实例
__all__ = ["logger"]