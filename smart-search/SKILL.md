---
name: smart-search
description: >
  整合 DDGS、Tavily、Brave Search 三大引擎的智能搜索。
  当用户需要联网搜索信息、查找图片、对比分析、获取最新新闻或进行任何形式的网络调研时触发。
  支持文本自动路由、图片搜索、全引擎并行。用户经常搜新闻，Brave 最快最适合新闻场景。
  只要需要搜索，就使用此技能。
---

## 概述

Smart Search 将三个搜索引擎整合为一个统一入口，根据查询类型自动选择最佳引擎：

| 引擎 | 擅长 | 限制 |
|------|------|------|
| Tavily | 全文提取、相关性评分、深度研究 | 需 API Key，按量付费 |
| Brave Search | 速度快、图片搜索、新闻、页面年龄 | 需 API Key，按量付费 |
| DDGS | 免费、多引擎聚合、图书搜索 | 内容短，可靠性较低 |

## 安装

```bash
pip install ddgs tavily-python requests --break-system-packages
```

## 环境变量

```bash
export TAVILY_API_KEY="your-tavily-key"
export BRAVE_API_KEY="your-brave-api-key"
```

如果某个 Key 未设置，脚本会提示用户配置并将其保存到 `~/.bashrc`，不会静默降级。

## 七个命令

### 1. 文本搜索 — `search`

```bash
python3 scripts/smart_search.py search --query "你的问题"
```

脚本内部根据查询特征自动路由引擎：
- **新闻/最新消息**（常见场景）→ Brave（最快 + 页面年龄标注）
- 含图片/logo/照片类关键词 → Brave（唯一支持图片搜索）
- 含对比/分析/研究类关键词 → Tavily（全文 + 评分）
- 其他 → Tavily（内容最全面）

参数：`--engine tavily|brave|ddgs` 强制指定，`--max-results N`（默认 8），`--freshness d|w|m|y` 按时间过滤。

### 2. 图片搜索 — `images`

```bash
python3 scripts/smart_search.py images --query "搜索内容"
```

强制 Brave Image Search，返回原图直链、缩略图、尺寸和置信度。`--count N`（默认 5，最大 200）。

### 3. 全引擎并行 — `all`

```bash
python3 scripts/smart_search.py all --query "研究主题"
```

Tavily + Brave + DDGS 同时搜索，去重合并按相关性降序排列。适合最大信息覆盖。

### 4. URL 内容提取 — `extract`

```bash
python3 scripts/smart_search.py extract --url "https://..."
python3 scripts/smart_search.py extract --url "https://a" "https://b"   # 批量
```

优先 DDGS extract（免费），失败后用 Tavily extract。`--engine ddgs|tavily` 可强制指定。

### 5. 新闻搜索 — `news`

```bash
python3 scripts/smart_search.py news --query "AI监管" --days 7
```

主用 Brave News API，返回含时效标注的新闻结果。`--days 1|7|30` 控制时间范围（默认 7），`--count N`（默认 8）。

### 6. 视频搜索 — `videos`

```bash
python3 scripts/smart_search.py videos --query "Python tutorial" --duration short
```

主用 Brave Video API，返回含缩略图、时长、创作者的视频结果。`--duration short|medium|long` 过滤时长，`--count N`（默认 5）。

### 7. 事实核查 — `verify`

```bash
python3 scripts/smart_search.py verify --claim "新疆大学成立于1924年"
```

三引擎并行搜索同一断言，返回多方证据，由 LLM 判断支持/反驳。`--max-results N`（默认 8）。

## 返回值格式

所有命令输出统一 JSON 结构，`type` 字段区分 `web`、`image`、`news`、`video`、`extract`、`verify`。

### 文本/新闻/verify 搜索

```json
{"type": "web", "engine_used": "tavily", "response_time": 3.5, "total_results": 8,
 "results": [{"title": "...", "url": "...", "content": "...", "score": 0.94, "source_engine": "tavily", "published": "2026-03-18"}]}
```

### 图片搜索

```json
{"type": "image", "engine_used": "brave-images",
 "results": [{"title": "...", "url": "...", "image_url": "...", "thumbnail_url": "...", "width": 500, "height": 400, "confidence": "high"}]}
```

### URL 提取

```json
{"type": "extract", "engine_used": "ddgs-extract",
 "results": [{"url": "...", "title": "...", "content": "页面正文..."}]}
```

### 视频搜索

```json
{"type": "video", "engine_used": "brave-video",
 "results": [{"title": "...", "url": "...", "thumbnail_url": "...", "duration": "13:02:53", "source": "Programming with Mosh"}]}
```

### 事实核查

```json
{"type": "verify", "claim": "...", "engine_used": "all", "engines_queried": ["tavily","brave","ddgs"],
 "results": [...]}
```

## 工作流程

接到用户需要搜索的请求时：

1. **新闻/最新消息** → `news --query "..."`（Brave，最快）
2. **图片/logo/照片** → `images --query "..."`
3. **需要看某个网页内容** → `extract --url "..."`
4. **视频教程/演示** → `videos --query "..." --duration short`
5. **事实核查/验证断言** → `verify --claim "..."`
6. **通用文本搜索** → `search --query "..."`（自动路由）
7. **需要最大信息覆盖** → `all --query "..."`
8. 读取返回的 JSON，根据 results 总结回复，附上来源链接
