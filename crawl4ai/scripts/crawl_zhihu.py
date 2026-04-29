#!/usr/bin/env python3
"""
知乎内容爬取脚本 - 带反爬绕过
"""

import asyncio
import sys

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def crawl_zhihu(url: str, output_file: str = "zhihu_content.md"):
    """爬取知乎内容"""

    # 配置浏览器 - 使用更真实的配置绕过反爬
    browser_config = BrowserConfig(
        headless=False,  # 有时有界面浏览器更有帮助
        viewport_width=1920,
        viewport_height=1080,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        extra_args=["--disable-blink-features=AutomationControlled"]
    )

    # 配置爬虫 - 等待页面加载完成
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        wait_for_images=True,
        page_timeout=60000,
        # 等待页面内容加载
        wait_for="css:.ContentItem",
        # 尝试滚动加载
        js_code="""
        // 模拟真实用户行为
        window.scrollTo(0, document.body.scrollHeight / 2);
        await new Promise(r => setTimeout(r, 2000));
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 2000));
        """
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=crawler_config
        )

        if result.success:
            print(f"✅ 爬取成功: {result.url}")
            print(f"   标题: {result.metadata.get('title', 'N/A')}")
            print(f"   内容长度: {len(result.markdown)} 字符")

            # 保存 Markdown
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.markdown)
            print(f"📄 已保存到 {output_file}")
        else:
            print(f"❌ 爬取失败: {result.error_message}")
            print("尝试使用备用方法...")
            
            # 备用方法：更简单的爬取
            simple_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000
            )
            
            simple_browser = BrowserConfig(
                headless=True,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            async with AsyncWebCrawler(config=simple_browser) as simple_crawler:
                result2 = await simple_crawler.arun(url=url, config=simple_config)
                if result2.success:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(result2.markdown)
                    print(f"📄 已保存到 {output_file}")
                else:
                    print(f"❌ 备用方法也失败: {result2.error_message}")

        return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawl_zhihu.py <url> [output_file]")
        sys.exit(1)

    url = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "zhihu_content.md"
    asyncio.run(crawl_zhihu(url, output))
