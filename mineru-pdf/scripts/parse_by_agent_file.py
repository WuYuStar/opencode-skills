#!/usr/bin/env python3
"""
MinerU Agent 轻量解析 API - 本地文件上传
免登录，适合小文件（≤10MB，≤20页）
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from mineru_utils import (
    sanitize_filename,
    MinerUError
)
import requests


def create_agent_file_task(file_name: str, language: str = "ch",
                          page_range: Optional[str] = None, enable_table: bool = True,
                          is_ocr: bool = False, enable_formula: bool = True) -> tuple:
    """
    创建 Agent 文件上传任务
    
    Returns:
        (task_id, file_url)
    """
    api_url = "https://mineru.net/api/v1/agent/parse/file"
    
    data = {
        "file_name": file_name,
        "language": language,
        "enable_table": enable_table,
        "is_ocr": is_ocr,
        "enable_formula": enable_formula
    }
    
    if page_range:
        data["page_range"] = page_range
    
    try:
        response = requests.post(api_url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"创建任务失败: {result.get('msg', '未知错误')} (code: {result.get('code')})")
        
        return result["data"]["task_id"], result["data"]["file_url"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def upload_file_to_oss(file_path: str, file_url: str, verbose: bool = True) -> bool:
    """
    上传文件到 OSS
    """
    try:
        if verbose:
            print(f"正在上传文件...")
        
        with open(file_path, 'rb') as f:
            response = requests.put(file_url, data=f, timeout=120)
            response.raise_for_status()
        
        if verbose:
            print(f"文件上传成功")
        return True
        
    except FileNotFoundError:
        raise MinerUError(f"文件不存在: {file_path}")
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"上传失败: {e}")


def query_agent_task(task_id: str) -> dict:
    """
    查询 Agent 任务状态
    """
    api_url = f"https://mineru.net/api/v1/agent/parse/{task_id}"
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise MinerUError(f"查询任务失败: {result.get('msg', '未知错误')}")
        
        return result["data"]
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"请求失败: {e}")


def poll_agent_task(task_id: str, timeout: int = 300, interval: int = 3,
                   verbose: bool = True) -> dict:
    """
    轮询 Agent 任务直到完成
    """
    state_labels = {
        "waiting-file": "等待文件上传",
        "uploading": "文件下载中",
        "pending": "排队中",
        "running": "解析中"
    }
    
    start_time = time.time()
    
    if verbose:
        print(f"开始轮询任务 {task_id}...")
    
    while time.time() - start_time < timeout:
        try:
            data = query_agent_task(task_id)
            state = data.get("state", "unknown")
            elapsed = int(time.time() - start_time)
            
            if state == "done":
                if verbose:
                    print(f"[{elapsed}s] 解析完成！")
                return data
            
            if state == "failed":
                err_msg = data.get("err_msg", "未知错误")
                err_code = data.get("err_code", "")
                raise MinerUError(f"解析失败 [{err_code}]: {err_msg}")
            
            if verbose:
                print(f"[{elapsed}s] {state_labels.get(state, state)}...")
            
            time.sleep(interval)
            
        except MinerUError:
            raise
        except Exception as e:
            if verbose:
                print(f"查询出错: {e}，稍后重试...")
            time.sleep(interval)
    
    raise MinerUError(f"轮询超时 ({timeout}秒)。任务ID: {task_id}")


def download_markdown(markdown_url: str, output_path: str, verbose: bool = True) -> str:
    """
    下载 Markdown 文件
    """
    try:
        if verbose:
            print(f"正在下载 Markdown...")
        
        response = requests.get(markdown_url, timeout=120)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        if verbose:
            print(f"Markdown 已保存: {output_path}")
        
        return output_path
        
    except requests.exceptions.RequestException as e:
        raise MinerUError(f"下载失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="使用 MinerU Agent 轻量 API 解析本地文件（免登录）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
限制:
  - 文件大小 ≤ 10MB
  - 页数 ≤ 20 页
  - 支持 PDF、图片、Docx、PPTx、Xls、Xlsx

示例:
  # 基本用法
  python parse_by_agent_file.py ./small.pdf
  
  # 指定参数
  python parse_by_agent_file.py ./document.pdf \\
    --language en \\
    --page_range "1-10" \\
    --output_dir ./output
        """
    )
    
    parser.add_argument("file_path", help="本地文件路径")
    parser.add_argument("--language", default="ch",
                       help="文档语言 (默认: ch)")
    parser.add_argument("--page_range", help="页码范围，如 '1-10'")
    parser.add_argument("--enable_table", type=lambda x: x.lower() == "true",
                       default=True, help="是否开启表格识别 (默认: true)")
    parser.add_argument("--is_ocr", type=lambda x: x.lower() == "true",
                       default=False, help="是否启用 OCR (默认: false)")
    parser.add_argument("--enable_formula", type=lambda x: x.lower() == "true",
                       default=True, help="是否开启公式识别 (默认: true)")
    parser.add_argument("--output_dir", default="./",
                       help="输出目录 (默认: 当前目录)")
    parser.add_argument("--output_name", help="输出文件名（不含扩展名）")
    parser.add_argument("--timeout", type=int, default=300,
                       help="轮询超时时间 (默认: 300秒)")
    
    args = parser.parse_args()
    
    try:
        # 检查文件
        if not os.path.exists(args.file_path):
            print(f"错误: 文件不存在: {args.file_path}", file=sys.stderr)
            return 1
        
        file_size = os.path.getsize(args.file_path)
        if file_size > 10 * 1024 * 1024:
            print(f"警告: 文件大小 {file_size / 1024 / 1024:.1f}MB 超过 10MB 限制", file=sys.stderr)
            print("建议使用精准 API: python parse_by_file.py ...", file=sys.stderr)
        
        file_name = os.path.basename(args.file_path)
        print(f"使用 Agent 轻量 API 解析: {args.file_path}")
        print(f"文件大小: {file_size / 1024:.1f} KB")
        print("注意：此模式适用于小文件（≤10MB，≤20页），无需 Token\n")
        
        # 创建任务
        print("创建解析任务...")
        task_id, file_url = create_agent_file_task(
            file_name=file_name,
            language=args.language,
            page_range=args.page_range,
            enable_table=args.enable_table,
            is_ocr=args.is_ocr,
            enable_formula=args.enable_formula
        )
        print(f"任务已创建，ID: {task_id}")
        
        # 上传文件
        upload_file_to_oss(args.file_path, file_url)
        
        # 轮询等待
        task_data = poll_agent_task(task_id, timeout=args.timeout)
        
        # 获取 Markdown URL
        markdown_url = task_data.get("markdown_url")
        if not markdown_url:
            raise MinerUError("结果中没有 markdown_url")
        
        # 确定输出文件名
        if args.output_name:
            base_name = sanitize_filename(args.output_name)
        else:
            base_name = sanitize_filename(os.path.splitext(file_name)[0])
        
        # 创建输出目录
        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, f"{base_name}.md")
        
        # 下载 Markdown
        download_markdown(markdown_url, output_path)
        
        print(f"\n成功！Markdown 文件已保存至: {output_path}")
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
