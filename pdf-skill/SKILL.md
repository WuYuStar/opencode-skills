---
name: pdf-skill
description: 完整的 PDF 处理工具集，支持读取、提取、转换、合并、拆分、编辑、加密、压缩、OCR 等所有 PDF 操作。只要用户提到 .pdf 文件、PDF 文档、扫描件，或需要对 PDF 进行任何处理（查看内容、提取文本/表格/图片、转 Markdown、合并拆分、加解密、填表单、加/去水印、对比、压缩），都应使用此 skill。即使任务只是"帮我看一下这个PDF里写了什么"或"把这个pdf转成word"，也需要触发此 skill 来确保正确处理。
---

# PDF 处理指南

## 概览

本指南介绍使用 Python 库和命令行工具进行 PDF 处理的基本操作。有关高级功能、JavaScript 库和详细示例，请参阅 REFERENCE.md。如需填写 PDF 表单，请阅读 FORMS.md 并按照其说明操作。

## Python 库

### pypdf - 基本操作

#### 合并 PDF
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### 拆分 PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### 旋转页面
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # 顺时针旋转90度
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### reportlab - 创建 PDF

#### 基本 PDF 创建
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# 添加文本
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# 添加线条
c.line(100, height - 140, 400, height - 140)

# 保存
c.save()
```

#### 创建多页 PDF
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# 添加内容
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# 第2页
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# 构建 PDF
doc.build(story)
```

#### 上标和下标

**重要提示**：永远不要在 ReportLab PDF 中使用 Unicode 上标/下标字符（₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹）。内置字体不包含这些字形，会导致它们渲染为纯黑色方块。

相反，在 Paragraph 对象中使用 ReportLab 的 XML 标记标签：
```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

# 下标：使用 <sub> 标签
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# 上标：使用 <super> 标签
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

对于使用 canvas 绘制的文本（非 Paragraph 对象），应手动调整字体大小和位置，而不是使用 Unicode 上标/下标。

## 命令行工具

### qpdf
```bash
# 合并 PDF
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# 拆分页面
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# 旋转页面
qpdf input.pdf output.pdf --rotate=+90:1  # 将第1页旋转90度

# 移除密码
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk（如果可用）
```bash
# 合并
pdftk file1.pdf file2.pdf cat output merged.pdf

# 拆分
pdftk input.pdf burst

# 旋转
pdftk input.pdf rotate 1east output rotated.pdf
```

## 常见任务

### 添加水印
```python
from pypdf import PdfReader, PdfWriter

# 创建水印（或加载现有水印）
watermark = PdfReader("watermark.pdf").pages[0]

# 应用到所有页面
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### 密码保护
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# 添加密码
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## 内容提取（使用 MinerU）

当用户需要**从 PDF 中提取内容**（文本、表格、公式等）并转换为 Markdown 格式时，使用 MinerU API。

### 超时设置（重要）

MinerU 解析大文件或复杂 PDF 时可能需要较长时间（数分钟甚至更久）。**执行 MinerU 相关命令时，必须在 bash 工具中显式设置 `timeout` 参数**：

```json
{
  "command": "python scripts/parse_by_file.py ./large_document.pdf",
  "timeout": 600000
}
```

- **timeout 单位是毫秒**
- **建议至少设置为 600000（10 分钟）**
- 对于超大文件、扫描件或启用 OCR/公式识别时，可适当增加到 900000（15 分钟）或更长
- **切勿使用默认的 2 分钟超时，这会导致解析任务被中断**

### 前置检查
```bash
# 检查 Token
echo $MINERU_TOKEN
# 安装依赖
pip install requests
```

### 基本用法
```bash
# 本地文件解析（输出到 PDF 所在目录）
python scripts/parse_by_file.py ./document.pdf

# 指定输出目录
python scripts/parse_by_file.py ./document.pdf --output_dir ./output

# URL 解析（输出到当前目录）
python scripts/parse_by_url.py https://example.com/doc.pdf

# 小文件免 Token 解析（输出到 PDF 所在目录）
python scripts/parse_by_agent_file.py ./small.pdf
```

**注意**：本地文件解析默认将结果保存到 PDF 文件所在的目录，而非脚本所在目录。如需保存到其他位置，请使用 `--output_dir` 参数。

### 参数说明
| 参数 | 说明 | 示例 |
|------|------|------|
| `--model_version` | 模型版本 | `vlm`, `pipeline`, `MinerU-HTML` |
| `--enable_formula` | 公式识别 | `true` / `false` |
| `--enable_table` | 表格识别 | `true` / `false` |
| `--is_ocr` | OCR 扫描件 | `true` / `false` |
| `--language` | 文档语言 | `ch`, `en`, `japan` |
| `--page_ranges` | 页码范围 | `1-10`, `2,5,8-10` |

**注意**：大文件（≤200MB）用精准 API（需 Token），小文件（≤10MB）可用轻量 API（免 Token）。详见 [references/output_format.md](./references/output_format.md)。

## 快速参考

| 任务 | 最佳工具 | 命令/代码 |
|------|---------|----------|
| 合并 PDF | pypdf | `writer.add_page(page)` |
| 拆分 PDF | pypdf | 每页一个文件 |
| 创建 PDF | reportlab | Canvas 或 Platypus |
| 命令行合并 | qpdf | `qpdf --empty --pages ...` |
| 添加水印 | pypdf | `page.merge_page(watermark)` |
| 密码保护 | pypdf | `writer.encrypt(...)` |
| 内容提取 | MinerU | `scripts/parse_by_file.py` |
| 批量处理 | MinerU | `scripts/parse_batch_file.py` |
| 填写 PDF 表单 | pdf-lib 或 pypdf（参见 FORMS.md） | 参见 FORMS.md |

## 下一步

- 有关高级 pypdfium2 用法，请参阅 REFERENCE.md
- 有关 JavaScript 库（pdf-lib），请参阅 REFERENCE.md
- 如需填写 PDF 表单，请遵循 FORMS.md 中的说明
- 有关 MinerU 的完整参数、批量处理和错误处理，请参阅 [references/error_codes.md](./references/error_codes.md)
- 有关故障排除指南，请参阅 REFERENCE.md
