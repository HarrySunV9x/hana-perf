from datetime import datetime, timedelta
from pathlib import Path
import re
from .log import logger


def filter_logs(file_path: str, filter_str: str, timestamp: str, time_window: float = 1.0) -> list[str]:
    """
    # 根据过滤字符串和时间窗口，从文件中过滤日志。

    # 参数说明:
    #   file_path: 日志文件路径（字符串格式）。
    #   filter_str: 用于过滤日志的关键字字符串。
    #   timestamp: 目标时间戳，格式为 "MM-DD HH:MM:SS.ffffff"。
    #   time_window: 以秒为单位的时间窗口（默认为1.0秒），在 timestamp 前后各 time_window/2 的范围内查找。

    # 返回值:
    #   返回匹配关键字且时间范围符合的日志行列表。
    """
    # 验证文件存在
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")
    
    # 解析目标时间（只接受完整格式 "MM-DD HH:MM:SS.ffffff"）
    try:
        # 检查是否为完整格式
        if ' ' not in timestamp or '-' not in timestamp.split()[0]:
            raise ValueError(f"Invalid timestamp format: {timestamp}. Expected 'MM-DD HH:MM:SS.ffffff'")
        
        # 解析完整日期时间格式 "10-28 09:27:29.665281"
        target_time = datetime.strptime(timestamp, '%m-%d %H:%M:%S.%f')
        # 替换为当前年份
        target_time = target_time.replace(year=datetime.now().year)
    except ValueError as e:
        logger.error(f"Invalid timestamp format: {timestamp}, error: {e}")
        raise ValueError(f"Invalid timestamp format: {timestamp}. Expected 'MM-DD HH:MM:SS.ffffff'")
    
    # 计算时间范围
    start_time = target_time - timedelta(seconds=time_window / 2)
    end_time = target_time + timedelta(seconds=time_window / 2)
    
    logger.info(f"Filtering logs '{filter_str}' in {file_path} from {start_time} to {end_time}")
    
    # 读取并过滤日志
    filtered_logs = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 1. 首先按关键字过滤
            if filter_str not in line:
                continue
            
            # 2. 然后按时间范围过滤
            # 提取时间戳（Android 日志格式）
            # 格式: "10-28 09:27:29.665281"
            time_match = re.search(r'(\d{2}-\d{2}\s+)(\d{2}:\d{2}:\d{2}\.\d+)', line)
            
            if time_match:
                try:
                    time_str = time_match.group(0)
                    # 解析完整格式 "10-28 09:27:29.665281"
                    log_time = datetime.strptime(time_str, '%m-%d %H:%M:%S.%f')
                    log_time = log_time.replace(year=datetime.now().year)
                    # 比较完整的日期时间
                    if start_time <= log_time <= end_time:
                        filtered_logs.append(line)
                except ValueError:
                    # 时间解析失败，跳过此行
                    continue
            else:
                # 没有时间戳但包含关键字，也保留
                filtered_logs.append(line)
    
    logger.info(f"Found {len(filtered_logs)} matching log lines")
    return filtered_logs