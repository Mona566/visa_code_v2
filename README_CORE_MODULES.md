# 核心模块说明文档

本文档介绍项目中的三个核心模块：`pdf_to_markdown.py`、`llm_analysis.py` 和 `insert_browser.py`。

---

## 📄 pdf_to_markdown.py

### 功能概述
将PDF文件转换为Markdown格式的文本文件，使用腾讯云OCR（光学字符识别）服务进行文字识别。

### 工作流程
1. **PDF渲染**: 使用PyMuPDF将PDF的每一页渲染为JPEG图片
2. **图片压缩**: 自动调整DPI和JPEG质量，确保图片base64编码不超过7MB限制
3. **OCR识别**: 调用腾讯云OCR API识别图片中的文字
4. **格式转换**: 将OCR结果转换为Markdown格式并保存

### 主要函数

#### `init_ocr_client()`
初始化腾讯云OCR客户端。

**要求**:
- 环境变量 `TENCENTCLOUD_SECRET_ID`
- 环境变量 `TENCENTCLOUD_SECRET_KEY`

**返回**: OCR客户端对象

#### `pdf_to_markdown(pdf_path: str, dpi=150, use_accurate=True)`
将PDF文件转换为Markdown文本。

**参数**:
- `pdf_path`: PDF文件路径
- `dpi`: 渲染DPI（默认150，最小72）
- `use_accurate`: 是否使用高精度OCR（默认True，失败时自动降级为Basic OCR）

**返回**: Markdown格式的字符串

**特性**:
- 自动处理多页PDF
- 自动压缩超大的图片（超过7MB时降低DPI和质量）
- 每页失败时自动降级到Basic OCR
- 每页结果用 `<!-- Page N -->` 标记分隔

### 使用示例

```python
from pdf_to_markdown import pdf_to_markdown

# 转换PDF为Markdown
markdown_text = pdf_to_markdown("files/passport.pdf")
print(markdown_text)
```

**命令行使用**:
```bash
python pdf_to_markdown.py files/passport.pdf
# 输出: files/passport.pdf.md
```

### 依赖要求
- `pymupdf` (PyMuPDF): PDF渲染
- `Pillow` (PIL): 图片处理
- `tencentcloud-sdk-python-common`: 腾讯云SDK
- `tencentcloud-sdk-python-ocr`: 腾讯云OCR SDK

### 注意事项
- 单页图片base64编码限制为7MB
- 如果压缩后仍超过限制，会抛出异常，建议手动压缩或使用COS URL方式
- 需要有效的腾讯云凭证（Secret ID和Secret Key）

---

## 🤖 llm_analysis.py

### 功能概述
使用大语言模型（LLM）从Markdown文本中提取结构化的签证申请字段信息。

### 工作流程
1. **加载LLM**: 初始化ChatOpenAI客户端（使用环境变量配置的模型）
2. **构建提示词**: 使用预定义的模板，将Markdown文本插入提示词
3. **调用LLM**: 请求LLM提取结构化字段
4. **解析JSON**: 解析LLM返回的JSON格式结果
5. **错误处理**: 如果JSON格式错误，尝试修复或提取JSON部分

### 主要函数

#### `extract_visa_fields(markdown_text: str) -> dict`
从Markdown文本中提取签证字段。

**参数**:
- `markdown_text`: Markdown格式的文本内容（通常来自PDF OCR结果）

**返回**: 包含提取字段的字典，结构包括：
- Application Information（申请信息）
- Personal Information（个人信息）
- Contact Information（联系信息）
- Passport Information（护照信息）
- Employment / Student Status（就业/学生状态）
- Travel Companions（旅行同伴）
- Host / Accommodation（住宿信息）
- Family Information（家庭信息）
- Education / Qualification（教育/资格）
- Employment History（工作历史）
- Financial Support（财务支持）
- Agency / Assistance（代理/协助）
- Visa / Immigration History（签证/移民历史）
- Travel Document Details（旅行证件详情）
- Travel Details（旅行详情）
- Study Details in Ireland（在爱尔兰的学习详情）
- Emergency Contact（紧急联系人）

**错误处理**:
- 如果LLM返回的不是有效JSON，会尝试提取JSON部分
- 如果仍然失败，会调用LLM修复JSON格式
- 最终失败会抛出 `ValueError`

### 使用示例

```python
from llm_analysis import extract_visa_fields
from pathlib import Path

# 读取Markdown文件
markdown_text = Path("files/passport.pdf.md").read_text(encoding="utf-8")

# 提取字段
fields = extract_visa_fields(markdown_text)
print(fields)
```

**命令行使用**:
```bash
python llm_analysis.py
# 会自动处理 files/ 目录下的三个Markdown文件
```

### 环境变量要求
- `MODEL`: OpenAI模型名称（如 "gpt-4", "gpt-3.5-turbo"）
- `OPENAI_API_KEY`: OpenAI API密钥（通过dotenv加载）

### 依赖要求
- `langchain-openai`: LangChain的OpenAI集成
- `python-dotenv`: 环境变量管理

### 提示词模板
`irish_visa_template_prompt` 定义了详细的字段提取模板，包括：
- 17个主要类别的字段
- 每个字段的选项说明
- 数据来源标注（如 //passport, //id_card）
- 输出格式要求（JSON，缺失字段用null）

---

## 🌐 insert_browser.py

### 功能概述
爱尔兰签证申请表自动填写工具的主入口文件。通过Selenium自动化浏览器操作，自动填写爱尔兰签证在线申请表单。

### 功能模块导入
该文件作为主入口，从 `insert_function` 模块导入所有功能：

#### 工具函数 (`utils`)
- `setup_logging`: 日志初始化
- `log_operation`: 操作日志记录
- `verify_page_state`: 页面状态验证
- `safe_postback_operation`: 安全的PostBack操作
- 各种延迟常量（`OPERATION_DELAY`, `POSTBACK_DELAY`等）

#### 页面检测 (`page_detection`)
- `check_and_handle_error_page`: 检测和处理错误页面
- `check_homepage_redirect`: 检测主页重定向
- `detect_current_page_state`: 检测当前页面状态
- `detect_page_number_no_refresh`: 检测页面编号（不刷新）
- `restart_from_homepage`: 从主页重新开始
- `click_next_button`: 点击"下一步"按钮

#### 表单填写辅助 (`form_helpers`)
- `fill_dropdown_by_label`: 通过标签填写下拉框
- `select_radio_by_label`: 通过标签选择单选按钮
- `fill_text_by_label`: 通过标签填写文本字段
- `fill_date_by_label`: 通过标签填写日期字段

#### 申请管理 (`application_management`)
- `save_application_number`: 保存申请编号
- `get_saved_application_number`: 获取保存的申请编号
- `extract_application_number`: 从页面提取申请编号
- `retrieve_application`: 检索已保存的申请

#### 页面填写器 (`page_fillers`)
- `fill_page_1` 到 `fill_page_10`: 填写表单的各个页面

#### 主流程 (`main_flow`)
- `auto_fill_inis_form`: 自动填写INIS表单（主函数）
- `fill_application_form`: 填写申请表单

### 使用方式

**直接运行**:
```bash
python insert_browser.py
```

这会调用 `auto_fill_inis_form()` 函数，自动完成整个表单填写流程。

### 工作流程（通过 `auto_fill_inis_form`）
1. 初始化浏览器（Chrome）
2. 访问爱尔兰签证申请网站
3. 检测当前页面状态
4. 根据页面状态执行相应操作：
   - 如果是主页，开始新申请或检索已有申请
   - 如果是表单页面，继续填写
   - 如果检测到错误，尝试恢复
5. 逐页填写表单（Page 1-10）
6. 处理各种异常情况（重定向、错误页面等）
7. 保存申请编号供后续使用

### 依赖要求
- `selenium`: 浏览器自动化
- Chrome浏览器和ChromeDriver
- `insert_function` 模块的所有子模块

### 注意事项
- 需要稳定的网络连接
- 需要Chrome浏览器和对应版本的ChromeDriver
- 表单填写过程可能需要较长时间（取决于网络和服务器响应）
- 程序会自动处理各种异常情况（页面重定向、错误恢复等）

---

## 🔄 三个模块的协作流程

```
PDF文件 (passport.pdf, id_card.pdf, cover_letter.pdf)
    ↓
[pdf_to_markdown.py]
    ↓ OCR识别
Markdown文件 (passport.pdf.md, id_card.pdf.md, cover_letter.pdf.md)
    ↓
[llm_analysis.py]
    ↓ LLM提取字段
结构化JSON数据 (包含所有签证字段)
    ↓
[insert_browser.py]
    ↓ 自动填写表单
爱尔兰签证在线申请表（已填写）
```

### 完整工作流程示例

```python
# 步骤1: PDF转Markdown
from pdf_to_markdown import pdf_to_markdown

pdf_files = ["files/passport.pdf", "files/id_card.pdf", "files/cover_letter.pdf"]
for pdf_file in pdf_files:
    markdown = pdf_to_markdown(pdf_file)
    with open(f"{pdf_file}.md", "w", encoding="utf-8") as f:
        f.write(markdown)

# 步骤2: 提取字段（可选，用于验证）
from llm_analysis import extract_visa_fields
from pathlib import Path

for md_file in ["files/passport.pdf.md", "files/id_card.pdf.md", "files/cover_letter.pdf.md"]:
    text = Path(md_file).read_text(encoding="utf-8")
    fields = extract_visa_fields(text)
    print(f"提取的字段: {fields}")

# 步骤3: 自动填写表单
# python insert_browser.py
# 或
from insert_browser import auto_fill_inis_form
auto_fill_inis_form()
```

---

## 📋 环境变量配置

### pdf_to_markdown.py 需要
```bash
export TENCENTCLOUD_SECRET_ID="your-secret-id"
export TENCENTCLOUD_SECRET_KEY="your-secret-key"
```

### llm_analysis.py 需要
```bash
export MODEL="gpt-4"  # 或 "gpt-3.5-turbo"
export OPENAI_API_KEY="your-api-key"
```

或使用 `.env` 文件：
```
MODEL=gpt-4
OPENAI_API_KEY=your-api-key
TENCENTCLOUD_SECRET_ID=your-secret-id
TENCENTCLOUD_SECRET_KEY=your-secret-key
```

---

## 🛠️ 安装依赖

```bash
# PDF转Markdown相关
pip install pymupdf Pillow
pip install tencentcloud-sdk-python-common tencentcloud-sdk-python-ocr

# LLM分析相关
pip install langchain-openai python-dotenv

# 浏览器自动化相关
pip install selenium

# 或使用requirements文件（如果有）
pip install -r requirements.txt
```

---

## ⚠️ 注意事项

1. **API密钥安全**: 不要将API密钥提交到版本控制系统，使用环境变量或 `.env` 文件
2. **文件路径**: 确保PDF文件路径正确，输出目录有写入权限
3. **网络连接**: OCR和LLM调用需要稳定的网络连接
4. **费用**: 腾讯云OCR和OpenAI API调用可能产生费用
5. **浏览器**: `insert_browser.py` 需要Chrome浏览器和ChromeDriver
6. **错误处理**: 所有模块都包含错误处理，但建议在生产环境中添加更多日志和监控

---

## 📚 相关文档

- `insert_function/` 目录：包含详细的表单填写逻辑
- `tests/` 目录：包含单元测试
- `debug_md/` 目录：包含调试用的页面快照

---

## 🔍 故障排查

### pdf_to_markdown.py
- **错误**: "请设置环境变量: TENCENTCLOUD_SECRET_ID"
  - **解决**: 设置腾讯云凭证环境变量
- **错误**: "图像经过压缩仍然超过 7MB"
  - **解决**: 手动压缩PDF或使用COS URL方式

### llm_analysis.py
- **错误**: "无法解析LLM返回的JSON格式"
  - **解决**: 检查LLM响应，可能需要调整提示词或使用不同的模型
- **错误**: "MODEL环境变量未设置"
  - **解决**: 设置 `MODEL` 环境变量

### insert_browser.py
- **错误**: ChromeDriver版本不匹配
  - **解决**: 安装与Chrome版本匹配的ChromeDriver
- **错误**: 页面加载超时
  - **解决**: 检查网络连接，可能需要增加等待时间

---

**最后更新**: 2025-01-XX

