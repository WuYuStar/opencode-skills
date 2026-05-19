#!/usr/bin/env python3
"""Smart Search - unified search interface combining DDGS, Tavily, and Brave Search."""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


BRAVE_WEB_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_IMAGE_URL = "https://api.search.brave.com/res/v1/images/search"
BRAVE_NEWS_URL = "https://api.search.brave.com/res/v1/news/search"
BRAVE_VIDEO_URL = "https://api.search.brave.com/res/v1/videos/search"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"


def load_env():
    tavily_key = os.environ.get("TAVILY_API_KEY", "")
    brave_key = os.environ.get("BRAVE_API_KEY", "")
    return tavily_key, brave_key


TAVILY_KEY, BRAVE_KEY = load_env()


def classify_query(query: str) -> str:
    image_kw = [
        "图片", "logo", "照片", "截图", "screenshot", "image", "photo",
        "图标", "插图", "画像", "图标", "壁纸", "封面", "海报",
        "校徽", "徽章", "标识", "商标"
    ]
    ql = query.lower()
    if any(kw in ql for kw in image_kw):
        return "brave-images"

    news_kw = ["新闻", "最新", "报道", "快讯", "breaking", "news", "今日"]
    if any(kw in ql for kw in news_kw):
        return "brave"

    research_kw = [
        "对比", "分析", "区别", "优缺点", "比较", "difference", "comparison",
        "vs", "versus", "production", "deploy", "benchmark", "性能"
    ]
    if any(kw in ql for kw in research_kw):
        return "tavily"

    return "tavily"


def missing_key_guide(key_name: str):
    msg = (
        f"\n⚠️  环境变量 {key_name} 未设置\n"
        f"\nSmart Search 需要 API Key 才能使用此引擎。请按以下步骤配置：\n"
        f"\n  1. 将你的 {key_name} 添加到 ~/.bashrc："
        f"\n     echo 'export {key_name}=\"你的{key_name}\"' >> ~/.bashrc"
        f"\n  2. 使其生效："
        f"\n     source ~/.bashrc"
        f"\n"
    )
    print(msg, file=sys.stderr)
    sys.exit(1)


def brave_search(query: str, count: int = 8, freshness: str = "") -> dict:
    if not BRAVE_KEY:
        missing_key_guide("BRAVE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_KEY,
    }
    params = {"q": query, "count": min(count, 20)}
    if freshness:
        params["freshness"] = freshness
    t0 = time.time()
    try:
        resp = requests.get(BRAVE_WEB_URL, headers=headers, params=params, timeout=15)
        elapsed = time.time() - t0
        data = resp.json()
        raw = data.get("web", {}).get("results", [])
        results = []
        for i, r in enumerate(raw[:count]):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("description", ""),
                "score": round(1.0 - (i / max(len(raw), 1) * 0.3), 2),
                "source_engine": "brave",
                "published": r.get("age", r.get("page_age", "")),
            })
        return {"engine": "brave", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "brave", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def brave_images(query: str, count: int = 5) -> dict:
    if not BRAVE_KEY:
        missing_key_guide("BRAVE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_KEY,
    }
    params = {"q": query, "count": min(count, 200), "safesearch": "off"}
    t0 = time.time()
    try:
        resp = requests.get(BRAVE_IMAGE_URL, headers=headers, params=params, timeout=15)
        elapsed = time.time() - t0
        data = resp.json()
        raw = data.get("results", [])
        results = []
        for r in raw[:count]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "image_url": r.get("properties", {}).get("url", ""),
                "thumbnail_url": r.get("thumbnail", {}).get("src", ""),
                "width": r.get("properties", {}).get("width", 0),
                "height": r.get("properties", {}).get("height", 0),
                "confidence": r.get("confidence", ""),
                "source_engine": "brave-images",
                "published": r.get("page_fetched", ""),
            })
        return {"engine": "brave-images", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "brave-images", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def brave_news(query: str, count: int = 8, freshness: str = "pw") -> dict:
    if not BRAVE_KEY:
        missing_key_guide("BRAVE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_KEY,
    }
    params = {"q": query, "count": min(count, 20)}
    if freshness:
        params["freshness"] = freshness
    t0 = time.time()
    try:
        resp = requests.get(BRAVE_NEWS_URL, headers=headers, params=params, timeout=15)
        elapsed = time.time() - t0
        data = resp.json()
        raw = data.get("results", [])
        results = []
        for i, r in enumerate(raw[:count]):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("description", ""),
                "source_engine": "brave-news",
                "published": r.get("age", r.get("page_age", "")),
                "source": r.get("source", ""),
            })
        return {"engine": "brave-news", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "brave-news", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def brave_videos(query: str, count: int = 5, duration: str = "") -> dict:
    if not BRAVE_KEY:
        missing_key_guide("BRAVE_API_KEY")
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_KEY,
    }
    params = {"q": query, "count": min(count, 20)}
    if duration:
        params["duration"] = duration
    t0 = time.time()
    try:
        resp = requests.get(BRAVE_VIDEO_URL, headers=headers, params=params, timeout=15)
        elapsed = time.time() - t0
        data = resp.json()
        raw = data.get("results", [])
        results = []
        for r in raw[:count]:
            vid = r.get("video", {})
            thumb = r.get("thumbnail", {})
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("description", ""),
                "thumbnail_url": thumb.get("src", "") if isinstance(thumb, dict) else str(thumb),
                "duration": vid.get("duration", ""),
                "source_engine": "brave-video",
                "published": r.get("age", r.get("page_age", "")),
                "source": vid.get("creator", vid.get("publisher", "")),
            })
        return {"engine": "brave-video", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "brave-video", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def ddgs_search(query: str, max_results: int = 8) -> dict:
    t0 = time.time()
    try:
        from ddgs import DDGS
        raw = DDGS().text(query, max_results=max_results, backend="auto")
        elapsed = time.time() - t0
        results = []
        for i, r in enumerate(raw):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "content": r.get("body", ""),
                "score": round(1.0 - (i / max(len(raw), 1) * 0.3), 2),
                "source_engine": "ddgs",
                "published": "",
            })
        return {"engine": "ddgs", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "ddgs", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def ddgs_videos(query: str, count: int = 5) -> dict:
    t0 = time.time()
    try:
        from ddgs import DDGS
        raw = DDGS().videos(query, max_results=count)
        elapsed = time.time() - t0
        results = []
        for r in raw:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("content", ""),
                "content": r.get("description", ""),
                "thumbnail_url": r.get("images", {}).get("medium", [{}])[0].get("image") if isinstance(r.get("images"), dict) else "",
                "duration": r.get("duration", ""),
                "source_engine": "ddgs-video",
                "published": r.get("published", ""),
                "source": r.get("uploader", r.get("provider", "")),
            })
        return {"engine": "ddgs-video", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "ddgs-video", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def ddgs_extract(url: str) -> dict:
    t0 = time.time()
    try:
        from ddgs import DDGS
        result = DDGS().extract(url, fmt="text_markdown")
        elapsed = time.time() - t0
        content = result.get("content", "")
        return {"engine": "ddgs-extract", "results": [{"url": url, "title": "", "content": content}], "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "ddgs-extract", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def tavily_extract(urls: list) -> dict:
    if not TAVILY_KEY:
        missing_key_guide("TAVILY_API_KEY")
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_KEY,
        "urls": urls[:20],
        "extract_depth": "advanced",
    }
    t0 = time.time()
    try:
        resp = requests.post(TAVILY_EXTRACT_URL, json=payload, headers=headers, timeout=30)
        elapsed = time.time() - t0
        data = resp.json()
        raw = data.get("results", [])
        results = []
        for r in raw:
            results.append({
                "url": r.get("url", ""),
                "title": r.get("raw_content", "")[:200],
                "content": r.get("raw_content", ""),
            })
        return {"engine": "tavily-extract", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "tavily-extract", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def tavily_search(query: str, max_results: int = 8, search_depth: str = "advanced") -> dict:
    if not TAVILY_KEY:
        missing_key_guide("TAVILY_API_KEY")
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
    }
    t0 = time.time()
    try:
        resp = requests.post(TAVILY_SEARCH_URL, json=payload, headers=headers, timeout=20)
        elapsed = time.time() - t0
        data = resp.json()
        raw = data.get("results", [])
        results = []
        for r in raw:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": round(r.get("score", 0), 3),
                "source_engine": "tavily",
                "published": "",
            })
        return {"engine": "tavily", "results": results, "response_time": round(elapsed, 2)}
    except Exception as e:
        return {"engine": "tavily", "error": str(e), "results": [], "response_time": round(time.time() - t0, 2)}


def merge_results(all_results: list[dict], max_total: int = 15) -> list[dict]:
    seen_urls = set()
    merged = []
    for batch in all_results:
        for r in batch.get("results", []):
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(r)
    merged.sort(key=lambda x: x.get("score", 0), reverse=True)
    return merged[:max_total]


def cmd_search(args):
    engine = args.engine or classify_query(args.query)
    time_map = {"d": "pd", "w": "pw", "m": "pm", "y": "py", "": ""}
    freshness = time_map.get(args.freshness or "", "")

    if engine == "brave":
        result = brave_search(args.query, args.max_results, freshness)
    elif engine == "ddgs":
        result = ddgs_search(args.query, args.max_results)
    elif engine == "brave-images":
        result = brave_images(args.query, args.max_results)
    else:
        result = tavily_search(args.query, args.max_results)

    output = {
        "query": args.query,
        "type": "web",
        "engine_used": result.get("engine", engine),
        "response_time": result.get("response_time", 0),
        "total_results": len(result.get("results", [])),
        "results": result.get("results", []),
    }
    if result.get("error"):
        output["warning"] = result["error"]
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_images(args):
    result = brave_images(args.query, args.count)
    output = {
        "query": args.query,
        "type": "image",
        "engine_used": "brave-images",
        "response_time": result.get("response_time", 0),
        "total_results": len(result.get("results", [])),
        "results": result.get("results", []),
    }
    if result.get("error"):
        output["warning"] = result["error"]
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_all(args):
    engines = {
        "tavily": lambda: tavily_search(args.query, args.max_results),
        "brave": lambda: brave_search(args.query, args.max_results),
        "ddgs": lambda: ddgs_search(args.query, args.max_results),
    }
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_map = {pool.submit(fn): name for name, fn in engines.items()}
        for fut in as_completed(fut_map):
            name = fut_map[fut]
            try:
                results[name] = fut.result()
            except Exception as e:
                results[name] = {"engine": name, "error": str(e), "results": []}

    total_time = round(time.time() - t0, 2)
    engine_results = [results[k] for k in ["tavily", "brave", "ddgs"] if k in results]
    merged = merge_results(engine_results, args.max_results * 2)

    output = {
        "query": args.query,
        "type": "web",
        "engine_used": "all",
        "engines_queried": list(engines.keys()),
        "response_time": total_time,
        "total_results": len(merged),
        "results": merged,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_extract(args):
    if args.engine == "tavily":
        result = tavily_extract(args.url)
    elif args.engine == "ddgs":
        results_list = []
        for url in args.url[:5]:
            r = ddgs_extract(url)
            if r.get("results"):
                results_list.extend(r["results"])
        total_time = sum(r.get("response_time", 0) for r in [ddgs_extract(u) for u in args.url[:5]])
        result = {"engine": "ddgs-extract", "results": results_list, "response_time": round(total_time, 2)}
    else:
        results_list = []
        for url in args.url[:5]:
            r = ddgs_extract(url)
            if r.get("results") and r["results"][0].get("content", "").strip():
                results_list.extend(r["results"])
        remaining = [u for u in args.url[:5] if u not in [r["url"] for r in results_list]]
        if remaining:
            r = tavily_extract(remaining)
            if r.get("results"):
                results_list.extend(r["results"])
        result = {"engine": "auto-extract", "results": results_list, "response_time": 0}

    output = {
        "type": "extract",
        "urls": args.url,
        "engine_used": result.get("engine", ""),
        "response_time": result.get("response_time", 0),
        "total_results": len(result.get("results", [])),
        "results": result.get("results", []),
    }
    if result.get("error"):
        output["warning"] = result["error"]
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_news(args):
    day_map = {1: "pd", 7: "pw", 30: "pm", 0: ""}
    freshness = day_map.get(args.days, "")

    result = brave_news(args.query, args.count, freshness)
    if not result.get("results"):
        fallback = ddgs_search(args.query, args.count)
        output = {
            "query": args.query,
            "type": "news",
            "engine_used": "ddgs",
            "response_time": fallback.get("response_time", 0),
            "total_results": len(fallback.get("results", [])),
            "results": fallback.get("results", []),
        }
        if fallback.get("error"):
            output["warning"] = fallback["error"]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    output = {
        "query": args.query,
        "type": "news",
        "engine_used": "brave-news",
        "response_time": result.get("response_time", 0),
        "total_results": len(result.get("results", [])),
        "results": result.get("results", []),
    }
    if result.get("error"):
        output["warning"] = result["error"]
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_videos(args):
    result = brave_videos(args.query, args.count, args.duration)
    if not result.get("results"):
        fallback = ddgs_videos(args.query, args.count)
        output = {
            "query": args.query,
            "type": "video",
            "engine_used": "ddgs-video",
            "response_time": fallback.get("response_time", 0),
            "total_results": len(fallback.get("results", [])),
            "results": fallback.get("results", []),
        }
        if fallback.get("error"):
            output["warning"] = fallback["error"]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    output = {
        "query": args.query,
        "type": "video",
        "engine_used": "brave-video",
        "response_time": result.get("response_time", 0),
        "total_results": len(result.get("results", [])),
        "results": result.get("results", []),
    }
    if result.get("error"):
        output["warning"] = result["error"]
    print(json.dumps(output, ensure_ascii=False, indent=2))


def cmd_verify(args):
    engines = {
        "tavily": lambda: tavily_search(args.claim, args.max_results),
        "brave": lambda: brave_search(args.claim, args.max_results),
        "ddgs": lambda: ddgs_search(args.claim, args.max_results),
    }
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_map = {pool.submit(fn): name for name, fn in engines.items()}
        for fut in as_completed(fut_map):
            name = fut_map[fut]
            try:
                results[name] = fut.result()
            except Exception as e:
                results[name] = {"engine": name, "error": str(e), "results": []}

    total_time = round(time.time() - t0, 2)
    engine_results = [results[k] for k in ["tavily", "brave", "ddgs"] if k in results]
    merged = merge_results(engine_results, args.max_results * 3)

    output = {
        "claim": args.claim,
        "type": "verify",
        "engine_used": "all",
        "engines_queried": list(engines.keys()),
        "response_time": total_time,
        "total_results": len(merged),
        "results": merged,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Smart Search - Unified search interface")
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Text search with auto engine routing")
    p_search.add_argument("--query", "-q", required=True)
    p_search.add_argument("--engine", choices=["auto", "tavily", "brave", "ddgs"], default="auto")
    p_search.add_argument("--max-results", type=int, default=8)
    p_search.add_argument("--freshness", choices=["d", "w", "m", "y", ""], default="")

    p_images = sub.add_parser("images", help="Image search (Brave)")
    p_images.add_argument("--query", "-q", required=True)
    p_images.add_argument("--count", type=int, default=5)

    p_all = sub.add_parser("all", help="Parallel search across all engines")
    p_all.add_argument("--query", "-q", required=True)
    p_all.add_argument("--max-results", type=int, default=8)

    p_extract = sub.add_parser("extract", help="Extract content from URLs")
    p_extract.add_argument("--url", "-u", nargs="+", required=True)
    p_extract.add_argument("--engine", choices=["auto", "ddgs", "tavily"], default="auto")

    p_news = sub.add_parser("news", help="News search (Brave)")
    p_news.add_argument("--query", "-q", required=True)
    p_news.add_argument("--days", type=int, choices=[1, 7, 30, 0], default=7, help="1=24h, 7=week, 30=month")
    p_news.add_argument("--count", type=int, default=8)

    p_videos = sub.add_parser("videos", help="Video search (Brave)")
    p_videos.add_argument("--query", "-q", required=True)
    p_videos.add_argument("--count", type=int, default=5)
    p_videos.add_argument("--duration", choices=["short", "medium", "long", ""], default="")

    p_verify = sub.add_parser("verify", help="Fact-check with all engines")
    p_verify.add_argument("--claim", "-c", required=True)
    p_verify.add_argument("--max-results", type=int, default=8)

    args = parser.parse_args()
    if args.command == "search":
        cmd_search(args)
    elif args.command == "images":
        cmd_images(args)
    elif args.command == "all":
        cmd_all(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "news":
        cmd_news(args)
    elif args.command == "videos":
        cmd_videos(args)
    elif args.command == "verify":
        cmd_verify(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
