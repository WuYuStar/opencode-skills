---
name: crawl4ai
description: Crawl4AI 网页爬取工具包。当需要抓取网站、提取数据、应对反爬检测（Cloudflare/验证码/封禁）、使用代理轮换、爬取 JS 页面或构建数据管道时，务必使用。支持绕过反爬、动态内容、批量爬取、schema 提取。
version: 0.7.4
crawl4ai_version: ">=0.7.4"
last_updated: 2025-01-19
---

# Crawl4AI

## 概述

此技能提供了使用 Crawl4AI 库进行网页爬取和数据提取的全面支持，包括完整的 SDK 参考、即用型脚本（适用于常见模式）以及高效数据提取的优化工作流程。

## 快速开始

### 安装检查
```bash
# 验证安装
crawl4ai-doctor

# 如有问题，运行设置
crawl4ai-setup
```

### 基础首次爬取
```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:500])  # 前 500 个字符

asyncio.run(main())
```

### 使用提供的脚本
```bash
# 简单的 Markdown 提取
python scripts/basic_crawler.py https://example.com

# 批处理
python scripts/batch_crawler.py urls.txt

# 数据提取
python scripts/extraction_pipeline.py --generate-schema https://shop.com "提取产品信息"
```

## 核心爬取基础

### 1. 基础爬取

了解任何爬取任务的核心组件：

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# 浏览器配置（控制浏览器行为）
browser_config = BrowserConfig(
    headless=True,  # 无界面运行
    viewport_width=1920,
    viewport_height=1080,
    user_agent="custom-agent"  # 可选的自定义用户代理
)

# 爬取器配置（控制爬取行为）
crawler_config = CrawlerRunConfig(
    page_timeout=30000,  # 30 秒超时
    screenshot=True,  # 截图
    remove_overlay_elements=True  # 移除弹窗/覆盖层
)

# 使用 arun() 执行爬取
async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=crawler_config
    )

    # CrawlResult 包含所有内容
    print(f"成功: {result.success}")
    print(f"HTML 长度: {len(result.html)}")
    print(f"Markdown 长度: {len(result.markdown)}")
    print(f"找到的链接数: {len(result.links)}")
```

### 2. 配置深入

**BrowserConfig** - 控制浏览器实例：
- `headless`：是否无界面运行
- `viewport_width/height`：浏览器尺寸
- `user_agent`：自定义用户代理字符串
- `cookies`：预设置 cookie
- `headers`：自定义 HTTP 请求头

**CrawlerRunConfig** - 控制每次爬取：
- `page_timeout`：页面加载/JS 执行的最大时间（毫秒）
- `wait_for`：等待的 CSS 选择器或 JS 条件（可选）
- `cache_mode`：控制缓存行为
- `js_code`：执行自定义 JavaScript
- `screenshot`：捕获页面截图
- `session_id`：在多个爬取中保持会话

### 3. 内容处理

每次爬取都可用的基本内容操作：

```python
result = await crawler.arun(url)

# 访问提取的内容
markdown = result.markdown  # 干净的 Markdown
html = result.html  # 原始 HTML
text = result.cleaned_html  # 清理后的 HTML

# 媒体和链接
images = result.media["images"]
videos = result.media["videos"]
internal_links = result.links["internal"]
external_links = result.links["external"]

# 元数据
title = result.metadata["title"]
description = result.metadata["description"]
```

## Markdown 生成（主要用例）

### 1. 基础 Markdown 提取

Crawl4AI 擅长生成干净、格式良好的 Markdown：

```python
# 简单的 Markdown 提取
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://docs.example.com")

    # 高质量的 Markdown，可直接用于 LLM
    with open("documentation.md", "w") as f:
        f.write(result.markdown)
```

### 2. Fit Markdown（内容过滤）

使用内容过滤器获取相关内容：

```python
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# 选项 1：剪枝过滤器（移除低质量内容）
pruning_filter = PruningContentFilter(threshold=0.4, threshold_type="fixed")

# 选项 2：BM25 过滤器（基于相关性的过滤）
bm25_filter = BM25ContentFilter(user_query="machine learning tutorials", bm25_threshold=1.0)

md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

config = CrawlerRunConfig(markdown_generator=md_generator)

result = await crawler.arun(url, config=config)
# 访问过滤后的内容
print(result.markdown.fit_markdown)  # 过滤后的 Markdown
print(result.markdown.raw_markdown)  # 原始 Markdown
```

### 3. Markdown 自定义

使用选项控制 Markdown 生成：

```python
config = CrawlerRunConfig(
    # 从 Markdown 中排除的元素
    excluded_tags=["nav", "footer", "aside"],

    # 专注于特定 CSS 选择器
    css_selector=".main-content",

    # 清理格式
    remove_forms=True,
    remove_overlay_elements=True,

    # 控制链接处理
    exclude_external_links=True,
    exclude_internal_links=False
)

# 自定义 Markdown 生成
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

generator = DefaultMarkdownGenerator(
    options={
        "ignore_links": False,
        "ignore_images": False,
        "image_alt_text": True
    }
)
```

## 数据提取

### 1. 基于 Schema 的提取（最高效）

对于重复模式，生成一次 schema 并重复使用：

```bash
# 第 1 步：使用 LLM 生成 schema（一次性）
python scripts/extraction_pipeline.py --generate-schema https://shop.com "extract products"

# 第 2 步：使用 schema 进行快速提取（无需 LLM）
python scripts/extraction_pipeline.py --use-schema https://shop.com generated_schema.json
```

### 2. 手动 CSS/JSON 提取

当您了解结构时：

```python
schema = {
    "name": "articles",
    "baseSelector": "article.post",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "date", "selector": ".date", "type": "text"},
        {"name": "content", "selector": ".content", "type": "text"}
    ]
}

extraction_strategy = JsonCssExtractionStrategy(schema=schema)
config = CrawlerRunConfig(extraction_strategy=extraction_strategy)
```

### 3. 基于 LLM 的提取

对于复杂或不规则的内容：

```python
extraction_strategy = LLMExtractionStrategy(
    provider="openai/gpt-4o-mini",
    instruction="Extract key financial metrics and quarterly trends"
)
```

## 高级模式

### 1. 深度爬取

发现并爬取页面中的链接：

```python
# 基础链接发现
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url)

    # 提取并处理发现的链接
    internal_links = result.links.get("internal", [])
    external_links = result.links.get("external", [])

    # 爬取发现的内部链接
    for link in internal_links:
        if "/blog/" in link and "/tag/" not in link:  # 过滤链接
            sub_result = await crawler.arun(link)
            # 处理子页面

    # 对于高级深度爬取，考虑使用 URL 种子模式
    # 或自定义爬取策略（参见 complete-sdk-reference.md）
```

### 2. 批量和多 URL 处理

高效爬取多个 URL：

```python
urls = ["https://site1.com", "https://site2.com", "https://site3.com"]

async with AsyncWebCrawler() as crawler:
    # 使用 arun_many() 并发爬取
    results = await crawler.arun_many(
        urls=urls,
        config=crawler_config,
        max_concurrent=5  # 控制并发数
    )

    for result in results:
        if result.success:
            print(f"✅ {result.url}: {len(result.markdown)} 字符")
```

### 3. 会话和身份验证

处理需要登录的内容：

```python
# 首次爬取 - 建立会话并登录
login_config = CrawlerRunConfig(
    session_id="user_session",
    js_code="""
    document.querySelector('#username').value = 'myuser';
    document.querySelector('#password').value = 'mypass';
    document.querySelector('#submit').click();
    """,
    wait_for="css:.dashboard"  # 等待登录后的元素
)

await crawler.arun("https://site.com/login", config=login_config)

# 后续爬取 - 重复使用会话
config = CrawlerRunConfig(session_id="user_session")
await crawler.arun("https://site.com/protected-content", config=config)
```

### 4. 动态内容处理

对于 JavaScript 密集型网站：

```python
config = CrawlerRunConfig(
    # 等待动态内容
    wait_for="css:.ajax-content",

    # 执行 JavaScript
    js_code="""
    // 滚动加载内容
    window.scrollTo(0, document.body.scrollHeight);

    // 点击加载更多按钮
    document.querySelector('.load-more')?.click();
    """,

    # 注意：对于虚拟滚动（Twitter/Instagram 风格），
    # 使用 virtual_scroll_config 参数（参见文档）

    # 延长超时时间以应对慢速加载
    page_timeout=60000
)
```

### 5. 反检测和代理

避免被识别为机器人：

```python
# 代理配置
browser_config = BrowserConfig(
    headless=True,
    proxy_config={
        "server": "http://proxy.server:8080",
        "username": "user",
        "password": "pass"
    }
)

# 对于隐身/防检测浏览，考虑：
# - 通过 user_agent 参数轮换用户代理
# - 使用不同的视口尺寸
# - 在请求之间添加延迟

# 速率限制
import asyncio
for url in urls:
    result = await crawler.arun(url)
    await asyncio.sleep(2)  # 请求之间的延迟
```

## 常见用例

### 文档转 Markdown
```python
# 将整个文档网站转换为干净的 Markdown
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://docs.example.com")

    # 保存为 Markdown 供 LLM 使用
    with open("docs.md", "w") as f:
        f.write(result.markdown)
```

### 电商产品监控
```python
# 为产品页面生成一次 schema
# 然后无需 LLM 成本即可监控价格/库存
schema = load_json("product_schema.json")
products = await crawler.arun_many(product_urls,
    config=CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(schema)))
```

### 新闻聚合
```python
# 并发爬取多个新闻源
news_urls = ["https://news1.com", "https://news2.com", "https://news3.com"]
results = await crawler.arun_many(news_urls, max_concurrent=5)

# 使用 Fit Markdown 提取文章
for result in results:
    if result.success:
        # 仅获取相关内容
        article = result.fit_markdown
```

### 研究和数据收集
```python
# 学术文献收集，使用聚焦提取
config = CrawlerRunConfig(
    fit_markdown=True,
    fit_markdown_options={
        "query": "machine learning transformers",
        "max_tokens": 10000
    }
)
```

## 资源

### scripts/
- **extraction_pipeline.py** - 三种提取方法，支持 schema 生成
- **basic_crawler.py** - 简单的 Markdown 提取和截图
- **batch_crawler.py** - 多 URL 并发处理

### references/
- **complete-sdk-reference.md** - 完整的 SDK 文档（23K 字），包含所有参数、方法和高级功能

### 示例代码仓库

Crawl4AI 仓库在 `docs/examples/` 中包含大量示例：

#### 核心示例
- **quickstart.py** - 全面的入门示例，包含所有基础模式：
  - 简单爬取、JavaScript 执行、CSS 选择器
  - 内容过滤、链接分析、媒体处理
  - LLM 提取、CSS 提取、动态内容
  - 浏览器比较、SSL 证书

#### 专业示例
- **amazon_product_extraction_*.py** - 电商抓取的三种方法
- **extraction_strategies_examples.py** - 展示所有提取策略
- **deepcrawl_example.py** - 高级深度爬取模式
- **crypto_analysis_example.py** - 复杂数据提取和分析
- **parallel_execution_example.py** - 高性能并发爬取
- **session_management_example.py** - 身份验证和会话处理
- **markdown_generation_example.py** - 高级 Markdown 自定义
- **hooks_example.py** - 爬取生命周期事件的自定义钩子
- **proxy_rotation_example.py** - 代理管理和轮换
- **router_example.py** - 请求路由和 URL 模式

#### 高级模式
- **adaptive_crawling/** - 智能爬取策略
- **c4a_script/** - C4A 脚本示例
- **docker_*.py** - Docker 部署模式

探索示例：
```python
# 示例位于您的 Crawl4AI 安装目录中：
# 查找：docs/examples/ 目录

# 从 quickstart.py 开始了解全面的模式
# 它包括：简单爬取、JS 执行、CSS 选择器、
# 内容过滤、LLM 提取、动态页面等

# 针对特定用例：
# - 电商：amazon_product_extraction_*.py
# - 高性能：parallel_execution_example.py
# - 身份验证：session_management_example.py
# - 深度爬取：deepcrawl_example.py

# 直接运行任何示例：
# python docs/examples/quickstart.py
```

## 最佳实践

1. **从基础爬取开始** - 在接触高级功能之前，先理解 BrowserConfig、CrawlerRunConfig 和 arun()
2. **将 Markdown 生成用于文档和内容** - Crawl4AI 擅长干净的 Markdown 提取
3. **对于结构化数据先尝试 schema 生成** - 比 LLM 提取效率高 10-100 倍
4. **在开发期间启用缓存** - `cache_mode=CacheMode.ENABLED` 以避免重复请求
5. **设置适当的超时时间** - 普通网站 30 秒，JavaScript 密集型网站 60 秒以上
6. **遵守速率限制** - 使用延迟和 `max_concurrent` 参数
7. **对于认证内容重复使用会话** 而不是重新登录

## 故障排除

**JavaScript 未加载：**
```python
config = CrawlerRunConfig(
    wait_for="css:.dynamic-content",  # 等待特定元素
    page_timeout=60000  # 增加超时时间
)
```

**机器人检测问题：**
```python
browser_config = BrowserConfig(
    headless=False,  # 有时可见浏览有帮助
    viewport_width=1920,
    viewport_height=1080,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
# 在请求之间添加延迟
await asyncio.sleep(random.uniform(2, 5))
```

**内容提取问题：**
```python
# 调试正在提取的内容
result = await crawler.arun(url)
print(f"HTML 长度: {len(result.html)}")
print(f"Markdown 长度: {len(result.markdown)}")
print(f"找到的链接数: {len(result.links)}")

# 尝试不同的等待策略
config = CrawlerRunConfig(
    wait_for="js:document.querySelector('.content') !== null"
)
```

**会话/身份验证问题：**
```python
# 验证会话是否保持
config = CrawlerRunConfig(session_id="test_session")
result = await crawler.arun(url, config=config)
print(f"会话 ID: {result.session_id}")
print(f"Cookies: {result.cookies}")
```

有关任何主题的更多详细信息，请参阅 `references/complete-sdk-reference.md`，其中包含所有功能、参数和高级使用模式的综合文档。
