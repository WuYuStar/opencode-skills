---
name: md-to-pdf
description: |
  将 Markdown 文件转换为专业排版的 PDF 文档。
  
  使用此 skill 当用户需要：
  - 将 .md 文件转为 PDF
  - 把 Markdown 文档导出为 PDF 格式
  - 生成美观的 PDF 报告/文档
  - 需要带代码高亮、自动编号的 PDF 输出
  
  此 skill 使用 eisvogel LaTeX 模板和 pandoc 工具，提供专业的文档排版效果，包括：
  - 代码块语法高亮
  - 自动章节编号
  - 优美的页面布局
  - 表格和图片支持
  - 中文支持（需要系统中安装中文字体）
---

# Markdown 转 PDF

使用 eisvogel 模板和 pandoc 将 Markdown 文档转换为专业排版的 PDF。

## 使用方法

### 基本转换

```bash
pandoc "input.md" -o "output.pdf" --template eisvogel --listings -N
```

### 完整命令（含中文支持）

```bash
pandoc "input.md" -o "output.pdf" \
  --template eisvogel \
  --listings \
  -N \
  --pdf-engine=xelatex \
  -V CJKmainfont="Noto Sans CJK SC"
```

## 参数说明

- `--template eisvogel`: 使用 eisvogel LaTeX 模板（模板文件位于 skill 的 templates/ 目录）
- `--listings`: 启用代码块语法高亮
- `-N`: 启用章节自动编号
- `--pdf-engine=xelatex`: 使用 XeLaTeX 引擎（支持 Unicode 和中文）
- `-V CJKmainfont="..."`: 设置中文字体

## 模板位置

eisvogel 模板位于：`<skill-path>/templates/eisvogel.latex`

使用模板时需要指定完整路径或确保模板在 pandoc 的模板搜索路径中。

## 中文支持要求

### 系统依赖

需要安装以下包：

```bash
# Debian/Ubuntu
sudo apt install -y pandoc texlive-xetex texlive-lang-chinese texlive-fonts-extra

# macOS
brew install pandoc mactex
```

### 中文字体

系统需要安装支持中文的字体，如：
- Noto Sans CJK SC
- Source Han Sans SC
- WenQuanYi Micro Hei

## 示例

### 转换单个文件

```bash
pandoc "README.md" -o "README.pdf" --template eisvogel --listings -N
```

### 转换带中文内容的文件

```bash
pandoc "文档.md" -o "文档.pdf" \
  --template eisvogel \
  --listings \
  -N \
  --pdf-engine=xelatex \
  -V CJKmainfont="Noto Sans CJK SC" \
  -V geometry:margin=2.5cm
```

### 合并多个 Markdown 文件

```bash
pandoc "01-intro.md" "02-body.md" "03-conclusion.md" \
  -o "完整文档.pdf" \
  --template eisvogel \
  --listings \
  -N
```

## 故障排除

### 错误：xelatex 不可用

安装 xelatex：
```bash
sudo apt install texlive-xetex
```

### 错误：缺少 .sty 文件

安装额外的 LaTeX 包：
```bash
sudo apt install texlive-fonts-extra texlive-lang-chinese
```

### 错误：中文字体未找到

检查系统字体：
```bash
fc-list :lang=zh | head -10
```

或安装 Noto 字体：
```bash
sudo apt install fonts-noto-cjk
```

## 高级配置

### 自定义模板变量

```bash
pandoc "input.md" -o "output.pdf" \
  --template eisvogel \
  -V title="文档标题" \
  -V author="作者姓名" \
  -V date="\\today" \
  -V geometry:margin=3cm \
  -V fontsize=12pt
```

### 使用其他 PDF 引擎

```bash
# LuaLaTeX（也支持中文）
pandoc "input.md" -o "output.pdf" --template eisvogel --pdf-engine=lualatex

# 纯文本引擎（无 LaTeX，不支持 eisvogel 模板）
pandoc "input.md" -o "output.pdf" --pdf-engine=wkhtmltopdf
```
