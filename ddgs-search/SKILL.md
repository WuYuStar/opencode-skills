---
name: ddgs-search
description: >
  使用 DDGS 进行网络搜索。支持文本、图片、视频、新闻、图书搜索和网页内容提取。
  当用户需要搜索信息、查找图片/视频/新闻/图书、提取网页内容时触发此技能。
---

## 概述

本技能使用 **DDGS** (Dux Distributed Global Search) - 一个 Python 元搜索引擎库，聚合多个搜索引擎的结果。支持 6 种搜索类型，返回结构化数据便于处理。

## 安装

```bash
pip install -U ddgs
```

## 快速开始

```python
from ddgs import DDGS

# 基础文本搜索
results = DDGS().text("Python asyncio 最佳实践", max_results=5)
```

## 搜索类型

### 1. 文本搜索 (`text()`)

搜索网页文本内容，支持多搜索引擎。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `query` | str | 必需 | 搜索关键词 |
| `region` | str | "us-en" | 地区代码 (us-en, uk-en, ru-ru, zh-cn 等) |
| `safesearch` | str | "moderate" | 安全搜索: "on", "moderate", "off" |
| `timelimit` | str | None | 时间限制: "d"(天), "w"(周), "m"(月), "y"(年) |
| `max_results` | int | 10 | 最大结果数 |
| `page` | int | 1 | 页码 |
| `backend` | str | "auto" | 搜索引擎: "bing", "brave", "duckduckgo", "google", "yandex", "yahoo", "wikipedia", 或 "auto" |

**返回值：** 包含 `title`(标题), `href`(链接), `body`(摘要) 的字典列表

**示例：**
```python
results = DDGS().text("AI Agent 框架", max_results=10, backend="auto")
for r in results:
    print(f"- {r['title']}: {r['href']}")
```

**高级用法：**
- 搜索 PDF 文件: `DDGS().text("机器学习 filetype:pdf")`
- 指定网站搜索: `DDGS().text("Python 教程 site:docs.python.org")`
- 多引擎搜索: `DDGS().text("量子计算", backend="bing,google")`

---

### 2. 图片搜索 (`images()`)

搜索图片，支持多种过滤选项。

**参数：** (继承文本搜索所有参数，外加：)
| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `size` | str | None | 尺寸: "Small", "Medium", "Large", "Wallpaper" |
| `color` | str | None | 颜色: "color", "Monochrome", "Red", "Green", "Blue" 等 |
| `type_image` | str | None | 类型: "photo", "clipart", "gif", "transparent", "line" |
| `layout` | str | None | 布局: "Square", "Tall", "Wide" |
| `license_image` | str | None | 许可证: "any", "Public", "Share", "Modify", "ModifyCommercially" 等 |

**返回值：** 包含 `title`(标题), `image`(原图URL), `thumbnail`(缩略图), `url`(来源页), `height`(高度), `width`(宽度), `source`(来源) 的字典列表

**示例：**
```python
results = DDGS().images("日落风景", size="Large", layout="Wide", max_results=5)
for r in results:
    print(f"- {r['title']}: {r['image']}")
```

---

### 3. 视频搜索 (`videos()`)

搜索视频，支持过滤选项。

**参数：** (继承文本搜索所有参数，外加：)
| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `resolution` | str | None | 分辨率: "high", "standart" |
| `duration` | str | None | 时长: "short"(短), "medium"(中), "long"(长) |
| `license_videos` | str | None | 许可证: "creativeCommon", "youtube" |

**返回值：** 包含 `title`(标题), `content`(视频URL), `description`(描述), `duration`(时长), `embed_url`(嵌入链接), `images`(缩略图), `provider`(提供商), `published`(发布时间), `publisher`(发布者), `uploader`(上传者) 的字典列表

**示例：**
```python
results = DDGS().videos("Python 初学者教程", duration="medium", max_results=5)
for r in results:
    print(f"- {r['title']} ({r['duration']}): {r['content']}")
```

---

### 4. 新闻搜索 (`news()`)

搜索最新新闻文章。

**参数：** 与 `text()` 相同（无额外参数）

**返回值：** 包含 `date`(日期), `title`(标题), `body`(摘要), `url`(链接), `image`(配图), `source`(来源) 的字典列表

**示例：**
```python
results = DDGS().news("人工智能监管", timelimit="w", max_results=10)
for r in results:
    print(f"- [{r['date']}] {r['title']} ({r['source']})")
```

---

### 5. 图书搜索 (`books()`)

搜索图书（基于 Anna's Archive）。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `query` | str | 必需 | 图书搜索关键词 |
| `max_results` | int | 10 | 最大结果数 |
| `page` | int | 1 | 页码 |
| `backend` | str | "auto" | 搜索引擎 |

**返回值：** 包含 `title`(书名), `author`(作者), `publisher`(出版社), `info`(信息), `url`(链接), `thumbnail`(封面) 的字典列表

**示例：**
```python
results = DDGS().books("代码整洁之道 Robert Martin", max_results=5)
for r in results:
    print(f"- {r['title']} by {r['author']}: {r['url']}")
```

---

### 6. 内容提取 (`extract()`)

获取网页并提取内容，支持多种格式。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|-----------|------|---------|-------------|
| `url` | str | 必需 | 要提取内容的 URL |
| `fmt` | str | "text_markdown" | 输出格式: "text_markdown", "text_plain", "text_rich", "text"(HTML), "content"(字节) |

**返回值：** 包含 `url` 和 `content` 的字典

**示例：**
```python
result = DDGS().extract("https://example.com/article", fmt="text_markdown")
print(result["content"])
```

---

## 输出格式

### 默认格式：结构化 JSON/字典

结果以 Python 字典形式返回，便于程序处理：

```python
[
    {
        "title": "文章标题",
        "href": "https://example.com/article",
        "body": "文章摘要..."
    },
    ...
]
```

### Markdown 表格格式

为便于对话中阅读，可将结果格式化为 Markdown 表格：

```markdown
| 序号 | 标题 | 链接 | 摘要 |
|---|-------|-----|---------|
| 1 | 文章标题 | [链接](https://...) | 文章摘要... |
| 2 | 另一篇文章 | [链接](https://...) | 另一篇摘要... |
```

**转换为 Markdown 的辅助函数：**
```python
def results_to_markdown(results):
    """将搜索结果转换为 Markdown 表格格式"""
    md = "| 序号 | 标题 | 链接 | 摘要 |\n"
    md += "|---|-------|-----|---------|\n"
    for i, r in enumerate(results, 1):
        title = r.get("title", "N/A")
        href = r.get("href", r.get("url", r.get("content", "N/A")))
        body = r.get("body", r.get("description", ""))[:100]
        md += f"| {i} | {title} | [链接]({href}) | {body}... |\n"
    return md
```

---

## 使用模式

### 模式 1：信息调研

```python
from ddgs import DDGS

ddgs = DDGS()

# 第1步：搜索相关文章
results = ddgs.text("Rust vs Go 性能对比", max_results=10, timelimit="y")

# 第2步：提取第一条结果的内容
if results:
    content = ddgs.extract(results[0]["href"], fmt="text_markdown")
    print(content["content"][:2000])  # 预览前 2000 字符
```

### 模式 2：多类型搜索

```python
ddgs = DDGS()

# 为一个主题收集不同类型的内容
topic = "气候变化解决方案"
text_results = ddgs.text(topic, max_results=5)
news_results = ddgs.news(topic, timelimit="w", max_results=5)
book_results = ddgs.books(topic, max_results=3)

# 展示所有结果
print("=== 文章 ===")
for r in text_results:
    print(f"- {r['title']}: {r['href']}")

print("\n=== 最新新闻 ===")
for r in news_results:
    print(f"- [{r['date']}] {r['title']} ({r['source']})")

print("\n=== 图书 ===")
for r in book_results:
    print(f"- {r['title']} by {r['author']}")
```

### 模式 3：批量处理

```python
ddgs = DDGS()

queries = ["Python async", "Rust 所有权", "Go 并发"]
all_results = {}

for q in queries:
    all_results[q] = ddgs.text(q, max_results=3)

# 保存供后续分析
import json
with open("search_results.json", "w") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)
```

---

## 最佳实践

### 错误处理

DDGS 可能因网络问题或请求限制抛出异常。建议使用 try/except 包裹：

```python
from ddgs import DDGS

ddgs = DDGS()
try:
    results = ddgs.text("搜索关键词", max_results=10)
except Exception as e:
    print(f"搜索失败: {e}")
    results = []
```

### 搜索引擎选择

- 使用 `backend="auto"`（默认）自动选择引擎
- 指定 `backend="bing"` 或 `backend="google"` 使用特定引擎
- 多引擎搜索：`backend="bing,google"`

### 按搜索类型支持的引擎

| 搜索类型 | 可用引擎 |
|-------------|-------------------|
| 文本 | bing, brave, duckduckgo, google, grokipedia, mojeek, yandex, yahoo, wikipedia |
| 图片 | duckduckgo |
| 视频 | duckduckgo |
| 新闻 | bing, duckduckgo, yahoo |
| 图书 | annasarchive |

### 常用地区代码

常见地区代码：`us-en`(美国), `uk-en`(英国), `de-de`(德国), `fr-fr`(法国), `es-es`(西班牙), `ru-ru`(俄罗斯), `zh-cn`(中国), `ja-jp`(日本), `kr-kr`(韩国)
