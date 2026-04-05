---
name: mineru-pdf
description: 使用 MinerU API 解析 PDF、Word、PPT 等文档，提取内容并转换为 Markdown 格式。当用户提到"解析 PDF"、"提取 PDF 内容"、"PDF 转 Markdown"、"MinerU"、"mineru"、"文档解析"、"批量处理文档"、"从 PDF 提取文本"、"转换文档格式"等场景时触发。支持精准解析 API（需 Token）和 Agent 轻量解析 API（免登录），自动处理异步任务、下载结果、解压并保存 Markdown 文件。
---

# MinerU PDF 解析 Skill

本 Skill 用于调用 MinerU API 解析各种文档（PDF、Word、PPT、图片等），自动处理异步任务、下载结果并提取 Markdown 内容。

## 功能特性

- **单文件 URL 解析**：通过远程 URL 解析文档
- **本地文件上传解析**：上传本地文件进行解析
- **批量文件处理**：支持同时处理多个文件
- **智能 API 选择**：根据文件大小/页数自动选择精准 API 或轻量 API
- **自动结果处理**：轮询等待、下载、解压、提取 Markdown
- **多种输出格式**：支持 Markdown、JSON、DOCX、HTML、LaTeX

## 使用流程（重要）

1. **先检测 Token**：在执行任何解析操作前，先运行 `echo $MINERU_TOKEN` 检查环境变量是否已配置
2. **仅在未配置时提示**：只有当 Token 为空时，才引导用户配置。不要每次都提示
3. **检测依赖**：运行 `python -c "import requests"` 确认依赖已安装

## 前置要求

### 环境变量

在 `.bashrc` 或 `.zshrc` 中设置：

```bash
export MINERU_TOKEN="your_api_token_from_mineru_net"
```

Token 申请地址：https://mineru.net/apiManage

### 依赖安装

```bash
pip install requests
```

## 使用方式

### 方式 1：URL 解析（推荐）

适用于文件已存储在可访问的 URL 上。

```python
# 基本用法
python scripts/parse_by_url.py https://example.com/document.pdf

# 完整参数
python scripts/parse_by_url.py https://example.com/document.pdf \
  --model_version vlm \
  --enable_formula true \
  --enable_table true \
  --language ch \
  --output_dir ./output
```

### 方式 2：本地文件解析

适用于本地文件。

```python
# 基本用法
python scripts/parse_by_file.py ./document.pdf

# 完整参数
python scripts/parse_by_file.py ./document.pdf \
  --model_version vlm \
  --enable_formula true \
  --enable_table true \
  --output_dir ./output
```

### 方式 3：批量 URL 解析

适用于同时解析多个远程文件。

```python
python scripts/parse_batch_url.py urls.txt
```

urls.txt 格式（每行一个 URL）：
```
https://example.com/doc1.pdf
https://example.com/doc2.pdf
```

### 方式 4：批量本地文件解析

适用于同时解析多个本地文件。

```python
python scripts/parse_batch_file.py file1.pdf file2.pdf file3.pdf
```

### 方式 5：Agent 轻量解析（免 Token）

适用于小文件（≤10MB，≤20页），无需 Token。

```python
# URL 模式
python scripts/parse_by_agent_url.py https://example.com/small.pdf

# 文件上传模式
python scripts/parse_by_agent_file.py ./small.pdf
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` / `file_path` | string | 必填 | 文档 URL 或本地文件路径 |
| `model_version` | string | "vlm" | 模型版本：pipeline、vlm、MinerU-HTML |
| `enable_formula` | bool | true | 是否开启公式识别 |
| `enable_table` | bool | true | 是否开启表格识别 |
| `is_ocr` | bool | false | 是否启用 OCR（扫描件建议开启）|
| `language` | string | "ch" | 文档语言：ch、en、japan 等 |
| `page_ranges` | string | null | 指定页码范围，如 "1-10" 或 "2,5,8-10" |
| `output_dir` | string | "./" | 输出目录 |
| `extra_formats` | array | [] | 额外导出格式：["docx", "html", "latex"] |
| `timeout` | int | 300 | 轮询超时时间（秒）|

## 语言代码参考

| 代码 | 说明 |
|------|------|
| ch | 中英文（默认）|
| en | 纯英文 |
| japan | 日文 |
| korean | 韩文 |
| chinese_cht | 繁体中文 |

完整列表见：[references/language_codes.md](./references/language_codes.md)

## 输出文件

解析完成后，会在 `output_dir` 下生成以下文件：

```
output/
├── {filename}.md              # Markdown 格式（主要内容）
├── {filename}_full.zip        # 完整结果压缩包
└── {filename}_extracted/      # 解压后的内容
    ├── full.md                # Markdown 内容
    ├── layout.json            # 版面分析结果
    ├── *_model.json           # 模型推理结果
    └── *_content_list.json    # 内容列表
```

## 文件限制

### 精准解析 API
- 文件大小：≤ 200MB
- 页数：≤ 600 页
- 支持格式：PDF、图片(png/jpg/jpeg/webp/gif/bmp)、Doc、Docx、Ppt、PPTx、HTML

### Agent 轻量解析 API
- 文件大小：≤ 10MB
- 页数：≤ 20 页
- 支持格式：PDF、图片、Docx、PPTx、Xls、Xlsx

## 示例

### 示例 1：解析学术论文 PDF

```python
python scripts/parse_by_url.py https://example.com/paper.pdf \
  --enable_formula true \
  --enable_table true \
  --language en \
  --output_dir ./papers
```

### 示例 2：解析扫描件（启用 OCR）

```python
python scripts/parse_by_file.py ./scanned_doc.pdf \
  --is_ocr true \
  --language ch
```

### 示例 3：只解析前 10 页

```python
python scripts/parse_by_url.py https://example.com/book.pdf \
  --page_ranges "1-10"
```

### 示例 4：批量处理报告

```python
python scripts/parse_batch_file.py ./reports/*.pdf --output_dir ./output
```

## 错误处理

常见错误及解决方法：

| 错误码 | 说明 | 解决建议 |
|--------|------|----------|
| A0202 | Token 错误 | 检查 MINERU_TOKEN 环境变量是否正确 |
| A0211 | Token 过期 | 前往 https://mineru.net/apiManage 申请新 Token |
| -60005 | 文件大小超出限制 | 检查文件大小，精准 API 最大 200MB，轻量 API 最大 10MB |
| -60006 | 文件页数超过限制 | 使用 --page_ranges 参数指定页码范围 |
| -30001 | 轻量 API 文件大小超限 | 使用精准 API 或拆分文件 |

## 注意事项

1. **GitHub/AWS URL 可能超时**：因网络限制，GitHub、AWS 等国外 URL 可能请求超时，建议先将文件下载到国内服务器
2. **每日限额**：每个账号每天享有 2000 页最高优先级解析额度
3. **缓存机制**：API 会缓存 URL 内容 15 分钟，如需获取最新内容可设置 `--no_cache true`
4. **回调通知**：如需实时通知，可配置 callback URL 接收解析完成通知

## 脚本列表

- `parse_by_url.py` - 精准 API URL 解析
- `parse_by_file.py` - 精准 API 本地文件解析
- `parse_batch_url.py` - 批量 URL 解析
- `parse_batch_file.py` - 批量本地文件解析
- `parse_by_agent_url.py` - 轻量 API URL 解析
- `parse_by_agent_file.py` - 轻量 API 文件解析

## 参考文档

- [输出文件格式说明](./references/output_format.md)
- [语言代码参考](./references/language_codes.md)
- [API 错误码完整列表](./references/error_codes.md)
