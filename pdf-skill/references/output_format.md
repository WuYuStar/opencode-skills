# MinerU 输出文件格式说明

## 标准输出结构（精准解析 API）

解析完成后，下载的 ZIP 压缩包包含以下文件：

```
{task_id}/
├── full.md                    # Markdown 格式的主文档
├── layout.json                # 版面分析结果（原 middle.json）
├── {filename}_model.json      # 模型推理结果（原 model.json）
├── {filename}_content_list.json  # 结构化内容列表（原 content_list.json）
└── images/                    # 提取的图片目录（如有）
    ├── image_001.png
    ├── image_002.png
    └── ...
```

## 各文件详细说明

### 1. full.md

Markdown 格式的文档内容，包含：
- 标题层级（# ## ###）
- 段落文本
- 表格（Markdown 表格格式）
- 公式（LaTeX 格式，行内 `$...$`，块级 `$$...$$`）
- 图片引用（`![描述](images/image_xxx.png)`）

**示例：**
```markdown
# 论文标题

## 摘要
本文研究了...

## 1. 引言
如图 1 所示：

![图 1 示例图片](images/image_001.png)

### 1.1 背景
公式示例：$E = mc^2$

表格示例：
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |
```

### 2. layout.json

版面分析的中间结果，包含页面布局信息：

```json
{
  "pages": [
    {
      "page_no": 1,
      "width": 595,
      "height": 842,
      "blocks": [
        {
          "type": "text",
          "bbox": [100, 100, 400, 150],
          "text": "段落内容..."
        },
        {
          "type": "image",
          "bbox": [100, 200, 400, 400],
          "image_path": "images/image_001.png"
        }
      ]
    }
  ]
}
```

**字段说明：**
- `page_no`: 页码
- `width/height`: 页面尺寸（像素）
- `blocks`: 内容块列表
  - `type`: 类型（text/title/image/table/formula）
  - `bbox`: 边界框 [x1, y1, x2, y2]
  - `text`: 文本内容

### 3. *_model.json

模型推理的原始结果，包含更详细的语义信息：

```json
{
  "pages": [
    {
      "page_no": 1,
      "elements": [
        {
          "category_type": "text",
          "bbox": [100, 100, 400, 150],
          "content": "文本内容",
          "confidence": 0.98
        }
      ]
    }
  ]
}
```

### 4. *_content_list.json

结构化的内容列表，按阅读顺序组织：

```json
[
  {
    "type": "title",
    "level": 1,
    "content": "一级标题"
  },
  {
    "type": "text",
    "content": "段落文本..."
  },
  {
    "type": "image",
    "path": "images/image_001.png",
    "caption": "图片说明"
  },
  {
    "type": "table",
    "content": "| 列1 | 列2 |\n|-----|-----|"
  },
  {
    "type": "formula",
    "content": "$E = mc^2$"
  }
]
```

**内容类型：**
- `title`: 标题（带 level 字段）
- `text`: 正文段落
- `image`: 图片
- `table`: 表格
- `formula`: 公式
- `header/footer`: 页眉页脚

## HTML 文件解析输出

当解析 HTML 文件时（model_version=MinerU-HTML），输出略有不同：

```
{task_id}/
├── full.md        # Markdown 格式
└── main.html      # 提取后的正文 HTML
```

## 额外导出格式

通过 `extra_formats` 参数可导出：

### DOCX 格式
- 保留文档结构和样式
- 表格转换为 Word 表格
- 公式转换为 Office Math 对象

### HTML 格式
- 包含完整样式
- 图片内嵌或引用
- 响应式布局

### LaTeX 格式
- 学术论文格式
- 公式保持 LaTeX 语法
- 适合学术出版

## 图片处理

### 图片提取
- 自动识别文档中的图片
- 保存为 PNG/JPEG 格式
- 在 Markdown 中引用相对路径

### 图片命名规则
```
images/
├── image_{page_no}_{index}.png    # 普通图片
├── table_{page_no}_{index}.png    # 表格截图（如无法解析为文本）
└── formula_{page_no}_{index}.png  # 公式截图（如无法解析）
```

## 公式处理

### 行内公式
Markdown 中使用 `$...$` 包裹：
```markdown
质能方程 $E = mc^2$ 由爱因斯坦提出。
```

### 块级公式
Markdown 中使用 `$$...$$` 包裹：
```markdown
$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$
```

### 公式识别精度
- **pipeline 模型**: 基础公式识别
- **vlm 模型**: 更强的公式理解能力，支持复杂排版

## 表格处理

### Markdown 表格
```markdown
| 姓名 | 年龄 | 城市 |
|------|------|------|
| 张三 | 25   | 北京 |
| 李四 | 30   | 上海 |
```

### 复杂表格
- 合并单元格会保留为 HTML 表格
- 跨页表格尝试合并
- 表格标题单独提取

## 多栏布局处理

MinerU 会自动识别并处理：
- 单栏布局
- 双栏布局（学术论文常见）
- 多栏混合布局
- 侧边栏内容

输出 Markdown 按阅读顺序组织，保持逻辑连贯性。

## 扫描件处理

启用 OCR (`is_ocr=true`) 时：
- 识别图片中的文字
- 保留版面结构
- 支持倾斜校正
- 支持多语言 OCR

## 最佳实践

### 1. 获取纯文本内容
```python
import json

# 读取 content_list.json
with open('xxx_content_list.json', 'r') as f:
    content_list = json.load(f)

# 提取所有文本
text_parts = []
for item in content_list:
    if item['type'] in ['text', 'title']:
        text_parts.append(item['content'])

full_text = '\n\n'.join(text_parts)
```

### 2. 提取所有图片
```python
import os
import shutil

# 复制图片到目标目录
source_dir = 'xxx_extracted/images'
target_dir = './my_images'

os.makedirs(target_dir, exist_ok=True)
for img in os.listdir(source_dir):
    shutil.copy2(os.path.join(source_dir, img), target_dir)
```

### 3. 处理表格数据
```python
import pandas as pd

# 从 Markdown 读取表格
with open('full.md', 'r') as f:
    content = f.read()

# 使用 pandas 读取 Markdown 表格
# 需要安装: pip install tabulate
from io import StringIO
import re

# 提取表格
for table_match in re.finditer(r'\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|', content):
    table_text = table_match.group()
    df = pd.read_csv(StringIO(table_text), sep='|', skipinitialspace=True)
    print(df)
```
