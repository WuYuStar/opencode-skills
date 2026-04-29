#!/usr/bin/env python3
"""
MinerU 精准解析 API - 本地文件上传解析
上传本地文件进行解析，自动下载并提取 Markdown
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from mineru_utils import (
    get_token,
    create_headers,
    poll_task,
    process_result,
    sanitize_filename,
    MinerUError
)
import requests


def apply_upload_urls(token: str, files: list, model_version: str = "vlm",
                     enable_formula: bool = True, enable_table: bool = True,
                     is_ocr: bool = False, language: str = "ch",
                     page_ranges: Optional[str] = None, extra_formats: Optional[list] = None,
                     data_id: Optional[str] = None) -> tuple:
    """
    申请批量文件上传 URL
    
    Returns:
        (batch_id, file_urls)
    """
    api_url = "https://mineru.net/api/v4/file-urls/batch"
    headers = create_headers(token)
    
    data = {
        "files": files,
        "model_version": model_version,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
        "is_ocr": is_ocr,
        "language": language
    }
    
    if page_ranges:
        data["page_ranges"] = page_ranges
    if extra_formats:
        data["extra_formats"] = extra_formats
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"申请上传 URL 失败: {result.get('msg', '未知错误')}")
        
        return result["data"]["batch_id"], result["data"]["file_urls"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def upload_file(file_path: str, upload_url: str, verbose: bool = True) -> bool:
    """
    上传文件到指定的 URL
    """
    try:
        if verbose:
            print(f"正在上传: {file_path}")
        
        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f, timeout=120)
            response.raise_for_status()
        
        if verbose:
            print(f"上传成功: {file_path}")
        return True
        
    except FileNotFoundError:
        raise MinerUError(f"文件不存在: {file_path}")
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"上传失败: {e}")


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


def poll_batch(batch_id: str, token: str, file_mapping: dict,
              timeout: int = 600, interval: int = 5, verbose: bool = True) -> dict:
    """
    轮询批量任务直到所有文件完成
    
    Returns:
        文件名到任务数据的映射
    """
    import time
    
    start_time = time.time()
    completed_files = {}
    
    if verbose:
        print(f"开始轮询批量任务 {batch_id}...")
    
    while time.time() - start_time < timeout:
        try:
            results = query_batch_result(batch_id, token)
            elapsed = int(time.time() - start_time)
            
            all_done = True
            pending_count = 0
            
            for result in results:
                file_name = result.get("file_name", "unknown")
                state = result.get("state", "unknown")
                
                if state == "done":
                    if file_name not in completed_files:
                        completed_files[file_name] = result
                        if verbose:
                            print(f"  [{elapsed}s] ✓ {file_name} 完成")
                elif state == "failed":
                    err_msg = result.get("err_msg", "未知错误")
                    completed_files[file_name] = result
                    if verbose:
                        print(f"  [{elapsed}s] ✗ {file_name} 失败: {err_msg}")
                else:
                    all_done = False
                    pending_count += 1
            
            if all_done:
                if verbose:
                    print(f"\n所有文件处理完成（耗时 {elapsed}s）")
                return completed_files
            
            if verbose and pending_count > 0:
                print(f"[{elapsed}s] 还有 {pending_count} 个文件处理中...")
            
            time.sleep(interval)
            
        except MinerUError:
            raise
        except Exception as e:
            if verbose:
                print(f"查询出错: {e}，稍后重试...")
            time.sleep(interval)
    
    raise MinerUError(f"轮询超时 ({timeout}秒)，任务可能仍在处理中。Batch ID: {batch_id}")


def main():
    parser = argparse.ArgumentParser(
        description="使用 MinerU API 解析本地文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python parse_by_file.py ./document.pdf
  
  # 指定参数
  python parse_by_file.py ./paper.pdf \\
    --model_version vlm \\
    --enable_formula true \\
    --language en \\
    --output_dir ./output
        """
    )
    
    parser.add_argument("file_path", help="本地文件路径")
    parser.add_argument("--model_version", default="vlm",
                       choices=["pipeline", "vlm", "MinerU-HTML"],
                       help="模型版本 (默认: vlm)")
    parser.add_argument("--enable_formula", type=lambda x: x.lower() == "true",
                       default=True, help="是否开启公式识别 (默认: true)")
    parser.add_argument("--enable_table", type=lambda x: x.lower() == "true",
                       default=True, help="是否开启表格识别 (默认: true)")
    parser.add_argument("--is_ocr", type=lambda x: x.lower() == "true",
                       default=False, help="是否启用 OCR (默认: false)")
    parser.add_argument("--language", default="ch",
                       help="文档语言 (默认: ch)")
    parser.add_argument("--page_ranges", help="指定页码范围")
    parser.add_argument("--extra_formats", nargs="+",
                       help="额外导出格式")
    parser.add_argument("--output_dir", default="./",
                       help="输出目录 (默认: 当前目录)")
    parser.add_argument("--timeout", type=int, default=600,
                       help="轮询超时时间 (默认: 600秒)")
    parser.add_argument("--data_id", help="数据 ID")
    
    args = parser.parse_args()
    
    try:
        # 检查文件
        if not os.path.exists(args.file_path):
            print(f"错误: 文件不存在: {args.file_path}", file=sys.stderr)
            return 1
        
        # 获取文件名
        file_name = os.path.basename(args.file_path)
        base_name = os.path.splitext(file_name)[0]
        
        # 获取 Token
        token = get_token()
        print(f"开始处理本地文件: {args.file_path}")
        
        # 申请上传 URL
        print("申请上传链接...")
        file_info = [{"name": file_name}]
        if args.data_id:
            file_info[0]["data_id"] = args.data_id
        if args.page_ranges:
            file_info[0]["page_ranges"] = args.page_ranges
        
        batch_id, file_urls = apply_upload_urls(
            token=token,
            files=file_info,
            model_version=args.model_version,
            enable_formula=args.enable_formula,
            enable_table=args.enable_table,
            is_ocr=args.is_ocr,
            language=args.language,
            extra_formats=args.extra_formats
        )
        
        print(f"批量任务 ID: {batch_id}")
        
        # 上传文件
        upload_file(args.file_path, file_urls[0])
        
        # 轮询等待
        file_mapping = {file_name: args.file_path}
        results = poll_batch(batch_id, token, file_mapping, timeout=args.timeout)
        
        # 处理结果
        result = results.get(file_name)
        if not result:
            raise MinerUError(f"未找到文件 {file_name} 的处理结果")
        
        if result.get("state") == "failed":
            err_msg = result.get("err_msg", "未知错误")
            raise MinerUError(f"解析失败: {err_msg}")
        
        # 创建模拟的 task_data 格式
        task_data = {
            "full_zip_url": result.get("full_zip_url"),
            "task_id": result.get("task_id", batch_id)
        }
        
        # 处理结果
        md_path = process_result(task_data, args.output_dir, sanitize_filename(base_name))
        
        print(f"\n成功！Markdown 文件已保存至: {md_path}")
        return 0
        
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
