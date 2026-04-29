#!/usr/bin/env python3
"""
MinerU 精准解析 API - 批量本地文件解析
同时上传并解析多个本地文件
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
    process_result,
    sanitize_filename,
    MinerUError
)
import requests


def apply_batch_upload(token: str, files: list, model_version: str = "vlm",
                      enable_formula: bool = True, enable_table: bool = True,
                      is_ocr: bool = False, language: str = "ch",
                      extra_formats: Optional[list] = None) -> tuple:
    """
    申请批量上传 URL
    
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


def upload_files(file_paths: list, upload_urls: list, verbose: bool = True) -> dict:
    """
    批量上传文件
    
    Returns:
        文件路径到上传状态的映射
    """
    results = {}
    
    for i, (file_path, upload_url) in enumerate(zip(file_paths, upload_urls)):
        try:
            if verbose:
                print(f"  [{i+1}/{len(file_paths)}] 上传: {os.path.basename(file_path)}")
            
            with open(file_path, 'rb') as f:
                response = requests.put(upload_url, data=f, timeout=120)
                response.raise_for_status()
            
            results[file_path] = True
            
        except FileNotFoundError:
            print(f"    ✗ 文件不存在: {file_path}")
            results[file_path] = False
        except requests.exceptions.RequestException as e:
            print(f"    ✗ 上传失败: {e}")
            results[file_path] = False
    
    return results


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


def poll_batch_until_done(batch_id: str, token: str, file_mapping: dict,
                         timeout: int = 600, interval: int = 5, verbose: bool = True) -> dict:
    """
    轮询批量任务直到完成
    
    Returns:
        文件名到任务数据的映射
    """
    import time
    
    start_time = time.time()
    completed_files = {}
    
    if verbose:
        print(f"\n开始轮询批量任务 {batch_id}...")
    
    while time.time() - start_time < timeout:
        try:
            results = query_batch_result(batch_id, token)
            elapsed = int(time.time() - start_time)
            
            all_done = True
            in_progress = []
            
            for result in results:
                file_name = result.get("file_name", "")
                state = result.get("state", "unknown")
                
                if state == "done":
                    if file_name not in completed_files:
                        completed_files[file_name] = result
                        if verbose:
                            print(f"  ✓ [{elapsed}s] {file_name} 完成")
                elif state == "failed":
                    if file_name not in completed_files:
                        completed_files[file_name] = result
                        err_msg = result.get("err_msg", "未知错误")
                        if verbose:
                            print(f"  ✗ [{elapsed}s] {file_name} 失败: {err_msg}")
                else:
                    all_done = False
                    in_progress.append(file_name)
            
            if all_done:
                if verbose:
                    success_count = sum(1 for r in completed_files.values() if r.get("state") == "done")
                    failed_count = len(completed_files) - success_count
                    print(f"\n批量任务完成（耗时 {elapsed}s）")
                    print(f"  成功: {success_count}")
                    print(f"  失败: {failed_count}")
                return completed_files
            
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
        description="批量解析本地文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解析多个文件
  python parse_batch_file.py file1.pdf file2.pdf file3.pdf
  
  # 使用通配符
  python parse_batch_file.py ./reports/*.pdf
  
  # 指定参数
  python parse_batch_file.py *.pdf \\
    --model_version vlm \\
    --output_dir ./batch_output
        """
    )
    
    parser.add_argument("files", nargs="+", help="要解析的本地文件路径")
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
        # 验证文件
        file_paths = []
        for pattern in args.files:
            if '*' in pattern or '?' in pattern:
                import glob
                file_paths.extend(glob.glob(pattern))
            else:
                file_paths.append(pattern)
        
        # 去重并验证存在性
        file_paths = list(dict.fromkeys(file_paths))  # 保持顺序去重
        valid_files = [f for f in file_paths if os.path.isfile(f)]
        
        if not valid_files:
            print("错误: 没有找到有效的文件", file=sys.stderr)
            return 1
        
        if len(valid_files) > 200:
            print(f"错误: 批量任务最多支持 200 个文件，当前 {len(valid_files)} 个", file=sys.stderr)
            return 1
        
        print(f"准备批量解析 {len(valid_files)} 个文件...")
        for i, f in enumerate(valid_files, 1):
            print(f"  {i}. {f}")
        
        # 获取 Token
        token = get_token()
        
        # 准备文件信息
        file_infos = []
        for file_path in valid_files:
            file_name = os.path.basename(file_path)
            info = {"name": file_name}
            if args.page_ranges:
                info["page_ranges"] = args.page_ranges
            file_infos.append(info)
        
        # 申请上传 URL
        print("\n申请上传链接...")
        batch_id, upload_urls = apply_batch_upload(
            token=token,
            files=file_infos,
            model_version=args.model_version,
            enable_formula=args.enable_formula,
            enable_table=args.enable_table,
            is_ocr=args.is_ocr,
            language=args.language,
            extra_formats=args.extra_formats
        )
        print(f"批量任务 ID: {batch_id}")
        
        # 上传文件
        print(f"\n上传 {len(valid_files)} 个文件...")
        upload_results = upload_files(valid_files, upload_urls)
        
        # 检查上传结果
        failed_uploads = [f for f, success in upload_results.items() if not success]
        if failed_uploads:
            print(f"\n警告: {len(failed_uploads)} 个文件上传失败")
            for f in failed_uploads:
                print(f"  - {f}")
        
        # 轮询等待
        file_mapping = {os.path.basename(f): f for f in valid_files}
        results = poll_batch_until_done(batch_id, token, file_mapping, timeout=args.timeout)
        
        # 处理结果
        print("\n处理结果...")
        success_count = 0
        failed_count = 0
        
        for file_name, result in results.items():
            # 找到对应的原始文件路径
            original_path = file_mapping.get(file_name)
            if not original_path:
                # 尝试匹配
                for path in valid_files:
                    if os.path.basename(path) == file_name:
                        original_path = path
                        break
            
            if not original_path:
                continue
            
            base_name = os.path.splitext(file_name)[0]
            
            if result.get("state") == "done":
                try:
                    task_data = {
                        "full_zip_url": result.get("full_zip_url"),
                        "task_id": result.get("task_id", batch_id)
                    }
                    md_path = process_result(task_data, args.output_dir, 
                                           sanitize_filename(base_name), verbose=False)
                    print(f"  ✓ {file_name} -> {md_path}")
                    success_count += 1
                except Exception as e:
                    print(f"  ✗ {file_name} -> 处理失败: {e}")
                    failed_count += 1
            else:
                err_msg = result.get("err_msg", "未知错误")
                print(f"  ✗ {file_name} -> 解析失败: {err_msg}")
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
