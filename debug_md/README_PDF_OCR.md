# PDF转Markdown工具

使用腾讯云OCR接口识别PDF文件并转换为Markdown格式的Python工具。

## 功能特性

- ✅ PDF文件上传和解析
- ✅ PDF转图片（支持自定义DPI）
- ✅ 调用腾讯云OCR接口进行文字识别
- ✅ OCR结果自动转换为Markdown格式
- ✅ 支持多页PDF批量处理
- ✅ 支持标题、段落等元素识别

## 安装依赖

### 1. 安装Python包

```bash
pip install -r requirements_pdf_ocr.txt
```

### 2. 安装系统依赖（poppler）

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
1. 下载 [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/)
2. 解压并添加到系统PATH环境变量

### 3. 配置腾讯云凭证

在使用前，需要配置腾讯云的SecretId和SecretKey。有以下三种方式：

**方式1: 环境变量（推荐）**

```bash
export TENCENTCLOUD_SECRET_ID="your-secret-id"
export TENCENTCLOUD_SECRET_KEY="your-secret-key"
```

**方式2: 配置文件**

在 `~/.tencentcloud/credentials` 文件中配置：

```ini
[default]
secret_id = your-secret-id
secret_key = your-secret-key
```

**方式3: 命令行参数**

在运行命令时通过参数传入（不推荐，安全性较低）

## 使用方法

### 基本用法

```bash
# 使用环境变量中的凭证
python pdf_to_markdown.py document.pdf --output output.md
```

### 完整示例

```bash
# 转换PDF并保存到文件（使用环境变量凭证）
python pdf_to_markdown.py document.pdf \
    --output output.md \
    --dpi 300

# 转换PDF并输出到控制台
python pdf_to_markdown.py document.pdf

# 使用命令行参数指定凭证（不推荐）
python pdf_to_markdown.py document.pdf \
    --secret-id your-secret-id \
    --secret-key your-secret-key \
    --output result.md

# 指定地域
python pdf_to_markdown.py document.pdf \
    --region ap-beijing \
    --output result.md
```

### 参数说明

- `pdf_path`: PDF文件路径（必需）
- `--output` / `-o`: 输出Markdown文件路径（可选）
- `--secret-id`: 腾讯云SecretId（可选，优先使用环境变量）
- `--secret-key`: 腾讯云SecretKey（可选，优先使用环境变量）
- `--region`: 腾讯云地域（默认: ap-shanghai）
- `--dpi`: PDF转图片的DPI（默认: 300）

## 代码示例

### 作为模块使用

```python
import os
from pdf_to_markdown import TencentOCRClient, PDFToMarkdownConverter

# 初始化OCR客户端（使用环境变量中的凭证）
ocr_client = TencentOCRClient(
    region="ap-shanghai"
)

# 或者直接传入凭证
# ocr_client = TencentOCRClient(
#     secret_id="your-secret-id",
#     secret_key="your-secret-key",
#     region="ap-shanghai"
# )

# 初始化转换器
converter = PDFToMarkdownConverter(
    ocr_client=ocr_client,
    dpi=300
)

# 转换PDF
markdown = converter.convert_pdf_to_markdown(
    pdf_path="document.pdf",
    output_path="output.md"
)

print(markdown)
```

### 单独调用OCR接口

```python
import os
import base64
from pdf_to_markdown import TencentOCRClient

# 初始化客户端（使用环境变量中的凭证）
ocr_client = TencentOCRClient(region="ap-shanghai")

# 读取图片并转换为Base64
with open("image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# 调用OCR
result = ocr_client.recognize_image(image_base64)
print(result)
```

## 处理流程

1. **PDF转图片**: 使用`pdf2image`将PDF每页转换为300 DPI的JPEG图片
2. **图片编码**: 将图片转换为Base64编码字符串
3. **OCR识别**: 调用腾讯云OCR接口 `GeneralAccurateOCR`（高精度通用印刷体识别）
4. **结果转换**: 将OCR返回的结构化数据转换为Markdown格式
5. **合并输出**: 将所有页面的Markdown合并为完整文档

## OCR元素类型映射

| OCR类型 | Markdown格式 |
|---------|-------------|
| `title` | `# 标题文本` |
| `table` | `**[Table]** 表格内容` |
| `figure` | `**[Figure at 图片描述]**` |
| `paragraph` | 普通文本 |
| `header` | 普通文本 |
| `footer` | 普通文本 |
| `figure_text` | 普通文本 |

## 错误处理

- PDF文件不存在：检查文件路径
- OCR接口调用失败：检查网络连接和腾讯云凭证配置
- 凭证未配置：设置环境变量或配置文件，参考"配置腾讯云凭证"章节
- PDF转图片失败：检查poppler是否正确安装
- 依赖包缺失：运行 `pip install -r requirements_pdf_ocr.txt`

## 注意事项

1. **腾讯云凭证**: 必须配置有效的SecretId和SecretKey，建议使用环境变量或配置文件方式
2. **地域选择**: 根据您的腾讯云账户选择合适的地域（如ap-shanghai、ap-beijing等）
3. **文件大小**: 大文件处理时间较长，建议使用异步处理
4. **DPI设置**: 更高的DPI会提高识别准确度，但会增加处理时间
5. **API配额**: 注意腾讯云OCR API的调用配额和费用
6. **图片大小限制**: 腾讯云OCR对单张图片有大小限制，建议DPI不超过300

## 获取腾讯云凭证

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 访问 [访问管理 - API密钥管理](https://console.cloud.tencent.com/cam/capi)
3. 创建或查看您的SecretId和SecretKey
4. 将凭证配置到环境变量或配置文件中

## 相关文档

- [腾讯云Python SDK文档](https://cloud.tencent.com/document/sdk/Python)
- [腾讯云OCR产品文档](https://cloud.tencent.com/document/product/866)
- [通用印刷体识别API文档](https://cloud.tencent.com/document/product/866/33526)

## 许可证

本项目遵循项目主许可证。

