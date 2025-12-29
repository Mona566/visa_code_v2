# 单元测试文档

本目录包含所有模块的单元测试。

## 测试结构

```
tests/
├── __init__.py
├── test_utils.py                    # utils.py 模块测试
├── test_form_helpers.py              # form_helpers.py 模块测试
├── test_application_management.py    # application_management.py 模块测试
├── test_page_detection.py            # page_detection.py 模块测试
├── test_fill_pages.py               # fill_page_*.py 模块测试
├── run_tests.py                      # 测试运行脚本
└── README.md                         # 本文档
```

## 运行测试

### 运行所有测试

```bash
# 从项目根目录运行
python tests/run_tests.py

# 或使用 unittest 模块
python -m unittest discover tests -v
```

### 运行特定测试模块

```bash
# 运行 utils 模块测试
python -m unittest tests.test_utils -v

# 运行 form_helpers 模块测试
python -m unittest tests.test_form_helpers -v

# 运行 application_management 模块测试
python -m unittest tests.test_application_management -v

# 运行 page_detection 模块测试
python -m unittest tests.test_page_detection -v

# 运行 fill_pages 模块测试
python -m unittest tests.test_fill_pages -v
```

### 运行特定测试类

```bash
# 运行 TestUtils 类
python -m unittest tests.test_utils.TestUtils -v

# 运行 TestFormHelpers 类
python -m unittest tests.test_form_helpers.TestFormHelpers -v
```

### 运行特定测试方法

```bash
# 运行 test_setup_logging 测试
python -m unittest tests.test_utils.TestUtils.test_setup_logging -v
```

## 测试覆盖范围

### test_utils.py
- `setup_logging()` - 日志设置
- `log_operation()` - 操作日志记录（INFO, SUCCESS, WARN, ERROR）
- `verify_page_state()` - 页面状态验证
- `safe_postback_operation()` - 安全的 PostBack 操作
- 常量定义测试

### test_form_helpers.py
- `fill_dropdown_by_label()` - 通过标签填充下拉框
- `select_radio_by_label()` - 通过标签选择单选按钮
- `fill_text_by_label()` - 通过标签填充文本输入
- `fill_date_by_label()` - 通过标签填充日期输入
- PostBack 行为测试

### test_application_management.py
- `save_page_source_for_debugging()` - 保存页面源码用于调试
- `save_application_number()` - 保存申请编号
- `get_saved_application_number()` - 获取保存的申请编号
- `extract_application_number()` - 从页面提取申请编号
- `retrieve_application()` - 检索申请

### test_page_detection.py
- `check_and_handle_error_page()` - 检查和处理错误页面
- `check_application_error()` - 检查申请错误
- `check_homepage_redirect()` - 检查主页重定向
- `check_page_redirect_after_field_fill()` - 检查字段填充后的页面重定向
- `detect_current_page_state()` - 检测当前页面状态
- `detect_page_number_no_refresh()` - 检测页面编号（不刷新）
- `handle_intermediate_page()` - 处理中间页面
- `restart_from_homepage()` - 从主页重启
- `click_next_button()` - 点击下一步按钮

### test_fill_pages.py
- `fill_page_1()` - 填充第1页
- `fill_page_2()` - 填充第2页
- `fill_page_3()` - 填充第3页
- `fill_page_4()` - 填充第4页
- `fill_page_5()` - 填充第5页
- `fill_page_6()` - 填充第6页
- `fill_page_7()` - 填充第7页
- `fill_page_8()` - 填充第8页
- `fill_page_9()` - 填充第9页
- `fill_page_10()` - 填充第10页（包含提交完成测试）
- 主页重定向测试（所有页面）

## 测试方法

所有测试使用 `unittest` 框架和 `unittest.mock` 来模拟 Selenium WebDriver 对象。这样可以：

1. **无需实际浏览器** - 测试可以在没有浏览器的情况下运行
2. **快速执行** - 模拟测试比实际浏览器测试快得多
3. **可重复性** - 测试结果一致，不受网络或浏览器状态影响
4. **隔离性** - 每个测试独立运行，互不影响

## 编写新测试

添加新测试时，请遵循以下模式：

```python
import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from insert_function.your_module import your_function

class TestYourModule(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_browser = Mock()
        self.mock_wait = Mock()
    
    def test_your_function_success(self):
        """Test your_function successful case"""
        # Arrange
        self.mock_browser.current_url = "https://example.com/test"
        
        # Act
        result = your_function(self.mock_browser, self.mock_wait)
        
        # Assert
        self.assertTrue(result)
```

## 注意事项

1. **Mock 对象** - 所有 Selenium WebDriver 对象都被模拟，确保测试不依赖实际浏览器
2. **文件操作** - 某些测试会创建临时文件，测试结束后会自动清理
3. **时间依赖** - 使用 `patch` 来模拟 `time.sleep()` 和 `time.time()`，避免测试执行时间过长
4. **导入路径** - 确保正确设置 `sys.path` 以便导入项目模块

## 持续集成

这些测试可以集成到 CI/CD 流程中：

```yaml
# 示例 GitHub Actions 配置
- name: Run tests
  run: |
    python -m unittest discover tests -v
```

## 故障排除

如果测试失败：

1. **检查导入路径** - 确保 `sys.path` 正确设置
2. **检查 Mock 对象** - 确保所有必需的属性和方法都被正确模拟
3. **检查依赖** - 确保所有依赖项都已安装
4. **查看详细输出** - 使用 `-v` 标志获取详细输出

## 贡献

添加新功能时，请同时添加相应的单元测试。确保：

- 测试覆盖所有主要功能
- 测试覆盖边界情况和错误情况
- 测试名称清晰描述测试内容
- 测试代码遵循项目代码风格

