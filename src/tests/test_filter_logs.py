import pytest
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.filter_logs import filter_logs


class TestFilterLogs:
    """filter_logs 函数测试套件"""
    
    @pytest.fixture
    def sample_log_file(self):
        """创建示例日志文件"""
        content = """	行  504: 10-28 09:27:27.499986  3399  3500 I input_focus: [Focus request 93064f5 NotificationShade,reason=UpdateInputWindows]
	行  857: 10-28 09:27:32.215816  3399  4570 I input_focus: [Focus leaving 93064f5 NotificationShade,reason=NOT_VISIBLE]
	行  870: 10-28 09:27:32.287284  3399  3500 I input_focus: [Focus request 67786e8 com.android.launcher/com.android.launcher.Launcher,reason=UpdateInputWindows]
	行  873: 10-28 09:27:32.298227  3399  4570 I input_focus: [Focus entering 67786e8 com.android.launcher/com.android.launcher.Launcher,reason=setFocusedWindow]
	行 1711: 10-28 09:27:42.227797  3399  3500 I input_focus: [Focus request ea05c44 com.oplus.logkit/com.oplus.logkit.collect.activity.CollectActivity,reason=UpdateInputWindows]
	行 1714: 10-28 09:27:42.238526  3399  4570 I input_focus: [Focus leaving 93064f5 NotificationShade,reason=setFocusedWindow]
	行 1715: 10-28 09:27:42.238575  3399  4570 I input_focus: [Focus entering ea05c44 com.oplus.logkit/com.oplus.logkit.collect.activity.CollectActivity,reason=setFocusedWindow]
	行 1856: 10-28 09:27:47.705679  3399  3500 I input_focus: [Focus request recents_animation_input_consumer,reason=UpdateInputWindows]
	行 1861: 10-28 09:27:47.721710  3399  4570 I input_focus: [Focus leaving ea05c44 com.oplus.logkit/com.oplus.logkit.collect.activity.CollectActivity,reason=setFocusedWindow]
	行 1862: 10-28 09:27:47.721805  3399  4570 I input_focus: [Focus entering recents_animation_input_consumer,reason=setFocusedWindow]
	行 1882: 10-28 09:27:48.657705  3399  3500 I input_focus: [Focus request 67786e8 com.android.launcher/com.android.launcher.Launcher,reason=UpdateInputWindows]
	行 1887: 10-28 09:27:48.667577  3399  4570 I input_focus: [Focus leaving recents_animation_input_consumer,reason=NOT_VISIBLE]
	行 1888: 10-28 09:27:48.667627  3399  4570 I input_focus: [Focus entering 67786e8 com.android.launcher/com.android.launcher.Launcher,reason=setFocusedWindow]
	行 1938: 10-28 09:27:49.665126  3399  4570 I input_focus: [Focus entering 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=Window became focusable. Previous reason: NOT_VISIBLE]
	行 1986: 10-28 09:27:51.716891  3399  3500 I input_focus: [Focus request 46f9b2c PopupWindow:1609c86,reason=UpdateInputWindows]
	行 1988: 10-28 09:27:51.729712  3399  4570 I input_focus: [Focus leaving 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=Waiting for window because NO_WINDOW]
	行 1990: 10-28 09:27:51.746979  3399  4570 I input_focus: [Focus entering 46f9b2c PopupWindow:1609c86,reason=Window became focusable. Previous reason: NOT_VISIBLE]
	行 2001: 10-28 09:27:52.311427  3399  3500 I input_focus: [Focus request 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=UpdateInputWindows]
	行 2006: 10-28 09:27:52.328142  3399  4570 I input_focus: [Focus entering 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=setFocusedWindow]
	行 2010: 10-28 09:27:52.333823  3399  3500 I input_focus: [Requesting to set focus to null window,reason=UpdateInputWindows]
	行 2012: 10-28 09:27:52.351700  3399  4570 I input_focus: [Focus leaving 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=Waiting for window because NO_WINDOW]
	行 2025: 10-28 09:27:52.441527  3399  3500 I input_focus: [Focus request 9aea1d8 com.tencent.mm/com.tencent.mm.plugin.scanner.ui.BaseScanUI,reason=UpdateInputWindows]
	行 2032: 10-28 09:27:52.501633  3399  4570 I input_focus: [Focus entering 9aea1d8 com.tencent.mm/com.tencent.mm.plugin.scanner.ui.BaseScanUI,reason=Window became focusable. Previous reason: NOT_VISIBLE]
	行 2087: 10-28 09:27:55.098916  3399  3500 I input_focus: [Requesting to set focus to null window,reason=UpdateInputWindows]
	行 2089: 10-28 09:27:55.131659  3399  4570 I input_focus: [Focus leaving 9aea1d8 com.tencent.mm/com.tencent.mm.plugin.scanner.ui.BaseScanUI,reason=Waiting for window because NO_WINDOW]
	行 2100: 10-28 09:27:55.153383  3399  3500 I input_focus: [Focus request 7179a82 com.tencent.mm/com.tencent.mm.plugin.profile.ui.ContactInfoUI,reason=UpdateInputWindows]
	行 2114: 10-28 09:27:55.214801  3399  4570 I input_focus: [Focus entering 7179a82 com.tencent.mm/com.tencent.mm.plugin.profile.ui.ContactInfoUI,reason=Window became focusable. Previous reason: NOT_VISIBLE]
	行 2152: 10-28 09:27:56.334700  3399  3500 I input_focus: [Focus request 4aa11f2 com.oplus.screenshot/LongshotCapture,reason=UpdateInputWindows]
	行 2156: 10-28 09:27:56.351749  3399  4570 I input_focus: [Focus leaving 7179a82 com.tencent.mm/com.tencent.mm.plugin.profile.ui.ContactInfoUI,reason=Waiting for window because NO_WINDOW]
	行 2157: 10-28 09:27:56.360143  3399  4570 I input_focus: [Focus entering 4aa11f2 com.oplus.screenshot/LongshotCapture,reason=Window became focusable. Previous reason: NOT_VISIBLE]
	行 2166: 10-28 09:27:57.704558  3399  3500 I input_focus: [Focus request 7179a82 com.tencent.mm/com.tencent.mm.plugin.profile.ui.ContactInfoUI,reason=UpdateInputWindows]
	行 2167: 10-28 09:27:57.719092  3399  4570 I input_focus: [Focus entering 7179a82 com.tencent.mm/com.tencent.mm.plugin.profile.ui.ContactInfoUI,reason=setFocusedWindow]
	行 2182: 10-28 09:27:58.365880  3399  4570 I input_focus: [Focus leaving 7179a82 com.tencent.mm/com.tencent.mm.plugin.profile.ui.ContactInfoUI,reason=NO_WINDOW]
	行 2185: 10-28 09:27:58.387367  3399  3500 I input_focus: [Focus request 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=UpdateInputWindows]
	行 2188: 10-28 09:27:58.408542  3399  4570 I input_focus: [Focus entering 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=Window became focusable. Previous reason: NOT_VISIBLE]
	行 2223: 10-28 09:27:59.548540  3399  3500 I input_focus: [Focus request 93064f5 NotificationShade,reason=UpdateInputWindows]
	行 2224: 10-28 09:27:59.561017  3399  4570 I input_focus: [Focus leaving 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=Waiting for window because NOT_FOCUSABLE]
	行 2225: 10-28 09:27:59.561053  3399  4570 I input_focus: [Focus entering 93064f5 NotificationShade,reason=Window became focusable. Previous reason: NOT_FOCUSABLE]
	行 2263: 10-28 09:28:02.423916  3399  3500 I input_focus: [Focus request 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=UpdateInputWindows]
	行 2271: 10-28 09:28:02.435898  3399  3500 I input_focus: [Requesting to set focus to null window,reason=UpdateInputWindows]
	行 2272: 10-28 09:28:02.440264  3399  4570 I input_focus: [Focus leaving 93064f5 NotificationShade,reason=setFocusedWindow]
	行 2273: 10-28 09:28:02.440377  3399  4570 I input_focus: [Focus entering 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=setFocusedWindow]
	行 2275: 10-28 09:28:02.449323  3399  4570 I input_focus: [Focus leaving 20132c7 com.tencent.mm/com.tencent.mm.ui.LauncherUI,reason=Waiting for window because NO_WINDOW]
	行 2278: 10-28 09:28:02.469377  3399  3500 I input_focus: [Focus request ea05c44 com.oplus.logkit/com.oplus.logkit.collect.activity.CollectActivity,reason=UpdateInputWindows]
	行 2283: 10-28 09:28:02.500036  3399  4570 I input_focus: [Focus entering ea05c44 com.oplus.logkit/com.oplus.logkit.collect.activity.CollectActivity,reason=Window became focusable. Previous reason: NOT_VISIBLE]"""
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # 清理
        Path(temp_path).unlink(missing_ok=True)
    
    def test_filter_by_keyword(self, sample_log_file):
        """测试关键字过滤"""
        result = filter_logs(
            file_path=sample_log_file,
            filter_str="input_focus:",
            timestamp="09:27:51.746979",
            time_window=2.0
        )
        
        # 打印结果（运行时加 -s 参数可见）
        print(f"\n{'='*60}")
        print(f"✅ 找到 {len(result)} 条匹配的日志:")
        print(f"{'='*60}")
        for i, line in enumerate(result, 1):
            print(f"{i}. {line.rstrip()}")
        print(f"{'='*60}\n")
        
        # 应该找到时间范围内的日志
        assert len(result) == 9
        assert all("input_focus:" in line for line in result)
    
    def test_filter_no_match(self, sample_log_file):
        """测试无匹配情况"""
        result = filter_logs(
            file_path=sample_log_file,
            filter_str="NOTEXIST",
            timestamp="09:27:29.665281"
        )
        
        assert len(result) == 0
    
    def test_file_not_exist(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            filter_logs(
                file_path="not_exist.txt",
                filter_str="ERROR",
                timestamp="09:27:29.665281"
            )

# 单独运行此测试文件
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

