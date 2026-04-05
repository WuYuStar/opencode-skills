#!/usr/bin/env python3
"""
MinerU 精准解析 API - 批量 URL 解析
同时解析多个远程文档 URL
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from mineru_utils import (
    get_token,
    create_headers,
    poll_task,
    process_result,
    get_filename_from_url,
    sanitize_filename,
    MinerUError
)
import requests


def create_batch_tasks(urls: list, token: str, model_version: str = "vlm",
                      enable_formula: bool = True, enable_table: bool = True,
                      is_ocr: bool = False, language: str = "ch",
                      page_ranges: Optional[str] = None, extra_formats: Optional[list] = None) -> str:
    """
    创建批量解析任务
    
    Returns:
        batch_id: 批量任务 ID
    """
    api_url = "https://mineru.net/api/v4/extract/task/batch"
    headers = create_headers(token)
    
    files = []
    for i, url in enumerate(urls):
        file_info = {"url": url}
        if page_ranges:
            file_info["page_ranges"] = page_ranges
        files.append(file_info)
    
    data = {
        "files": files,
        "model_version": model_version,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
        "is_ocr": is_ocr,
        "language": language
    }
    
    if extra_formats:
        data["extra_formats"] = extra_formats
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"创建批量任务失败: {result.get('msg', '未知错误')}")
        
        return result["data"]["batch_id"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def query_batch_result(batch_id: str, token: str) -> list:
    """
    查询批量任务结果
    """
    api_url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
    headers = create_headers(token)
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"查询批量结果失败: {result.get('msg', '未知错误')}")
        
        return result["data"]["extract_result"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def poll_batch_until_done(batch_id: str, token: str, url_mapping: dict,
                         timeout: int = 300, interval: int = 5, verbose: bool = True) -> dict:
    """
    轮询批量任务直到完成
    
    Returns:
        URL 到任务数据的映射
    """
    import time
    
    start_time = time.time()
    completed_results = {}
    url_to_filename = {url: get_filename_from_url(url) for url in url_mapping.keys()}
    
    if verbose:
        print(f"开始轮询批量任务 {batch_id}...")
        print(f"共 {len(url_mapping)} 个文件\n")
    
    while time.time() - start_time < timeout:
        try:
            results = query_batch_result(batch_id, token)
            elapsed = int(time.time() - start_time)
            
            all_done = True
            in_progress = []
            
            for result in results:
                file_name = result.get("file_name", "")
                state = result.get("state", "unknown")
                
                # 找到对应的 URL
                matching_url = None
                for url, fn in url_to_filename.items():
                    if fn in file_name or file_name in fn:
                        matching_url = url
                        break
                
                if state == "done":
                    if matching_url and matching_url not in completed_results:
                        completed_results[matching_url] = result
                        if verbose:
                            print(f"  ✓ [{elapsed}s] {file_name} 完成")
                elif state == "failed":
                    if matching_url and matching_url not in completed_results:
                        completed_results[matching_url] = result
                        err_msg = result.get("err_msg", "未知错误")
                        if verbose:
                            print(f"  ✗ [{elapsed}s] {file_name} 失败: {err_msg}")
                else:
                    all_done = False
                    in_progress.append(file_name)
            
            if all_done:
                if verbose:
                    success_count = sum(1 for r in completed_results.values() if r.get("state") == "done")
                    failed_count = len(completed_results) - success_count
                    print(f"\n批量任务完成（耗时 {elapsed}s）")
                    print(f"  成功: {success_count}")
                    print(f"  失败: {failed_count}")
                return completed_results
            
            if verbose and in_progress:
                print(f"[{elapsed}s] 处理中: {', '.join(in_progress[:3])}{'...' if len(in_progress) > 3 else ''}")
            
            time.sleep(interval)
            
        except MinerUError:
            raise
        except Exception as e:
            if verbose:
                print(f"查询出错: {e}，稍后重试...")
            time.sleep(interval)
    
    raise MinerUError(f"轮询超时 ({timeout}秒)。Batch ID: {batch_id}")


def main():
    parser = argparse.ArgumentParser(
        description="批量解析远程文档 URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从文件读取 URL 列表
  python parse_batch_url.py urls.txt
  
  # 直接在命令行指定多个 URL
  python parse_batch_url.py url1.pdf url2.pdf url3.pdf
  
  # 指定参数
  python parse_batch_url.py urls.txt \\
    --model_version vlm \\
    --output_dir ./batch_output
        """
    )
    
    parser.add_argument("urls", nargs="+", help="URL 列表文件或直接的 URL")
    parser.add_argument("--model_version", default="vlm",
                       choices=["pipeline", "vlm", "MinerU-HTML"],
                       help="模型版本 (默认: vlm)")
    parser.add_argument("--enable_formula", type=lambda x: x.lower() == "true",
                       default=True, help="是否开启公式识别")
    parser.add_argument("--enable_table", type=lambda x: x.lower() == "true",
                       default=True, help="是否开启表格识别")
    parser.add_argument("--is_ocr", type=lambda x: x.lower() == "true",
                       default=False, help="是否启用 OCR")
    parser.add_argument("--language", default="ch",
                       help="文档语言 (默认: ch)")
    parser.add_argument("--page_ranges", help="指定页码范围")
    parser.add_argument("--extra_formats", nargs="+",
                       help="额外导出格式")
    parser.add_argument("--output_dir", default="./batch_output",
                       help="输出目录 (默认: ./batch_output)")
    parser.add_argument("--timeout", type=int, default=600,
                       help="轮询超时时间 (默认: 600秒)")
    
    args = parser.parse_args()
    
    try:
        # 解析 URL 列表
        urls = []
        if len(args.urls) == 1 and args.urls[0].endswith('.txt'):
            # 从文件读取
            with open(args.urls[0], 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            urls = args.urls
        
        if not urls:
            print("错误: 没有提供有效的 URL", file=sys.stderr)
            return 1
        
        if len(urls) > 200:
            print(f"错误: 批量任务最多支持 200 个文件，当前 {len(urls)} 个", file=sys.stderr)
            return 1
        
        print(f"准备批量解析 {len(urls)} 个文件...")
        
        # 获取 Token
        token = get_token()
        
        # 创建批量任务
        print("创建批量解析任务...")
        batch_id = create_batch_tasks(
            urls=urls,
            token=token,
            model_version=args.model_version,
            enable_formula=args.enable_formula,
            enable_table=args.enable_table,
            is_ocr=args.is_ocr,
            language=args.language,
            page_ranges=args.page_ranges,
            extra_formats=args.extra_formats
        )
        print(f"批量任务 ID: {batch_id}\n")
        
        # 轮询等待
        url_mapping = {url: url for url in urls}
        results = poll_batch_until_done(batch_id, token, url_mapping, timeout=args.timeout)
        
        # 处理结果
        print("\n处理结果...")
        success_count = 0
        failed_count = 0
        
        for url, result in results.items():
            base_name = get_filename_from_url(url)
            
            if result.get("state") == "done":
                try:
                    task_data = {
                        "full_zip_url": result.get("full_zip_url"),
                        "task_id": result.get("task_id", batch_id)
                    }
                    md_path = process_result(task_data, args.output_dir, sanitize_filename(base_name), verbose=False)
                    print(f"  ✓ {base_name} -> {md_path}")
                    success_count += 1
                except Exception as e:
                    print(f"  ✗ {base_name} -> 处理失败: {e}")
                    failed_count += 1
            else:
                err_msg = result.get("err_msg", "未知错误")
                print(f"  ✗ {base_name} -> 解析失败: {err_msg}")
                failed_count += 1
        
        print(f"\n批量处理完成！")
        print(f"  成功: {success_count}")
        print(f"  失败: {failed_count}")
        print(f"  输出目录: {args.output_dir}")
        
        return 0 if failed_count == 0 else 1
        
    except MinerUError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n用户中断", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"未知错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
