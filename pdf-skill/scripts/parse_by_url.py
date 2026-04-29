#!/usr/bin/env python3
"""
MinerU 精准解析 API - URL 解析
通过远程 URL 解析文档，自动下载并提取 Markdown
"""

import argparse
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from mineru_utils import (
    get_token,
    create_task,
    poll_task,
    process_result,
    get_filename_from_url,
    MinerUError
)


def main():
    parser = argparse.ArgumentParser(
        description="使用 MinerU API 解析远程文档 URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python parse_by_url.py https://example.com/document.pdf
  
  # 指定参数
  python parse_by_url.py https://example.com/paper.pdf \\
    --model_version vlm \\
    --enable_formula true \\
    --language en \\
    --output_dir ./output
  
  # 只解析前 10 页
  python parse_by_url.py https://example.com/book.pdf --page_ranges "1-10"
        """
    )
    
    parser.add_argument("url", help="文档 URL")
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
                       help="文档语言 (默认: ch，可选: ch, en, japan, korean 等)")
    parser.add_argument("--page_ranges", help="指定页码范围，如 '1-10' 或 '2,5,8-10'")
    parser.add_argument("--extra_formats", nargs="+",
                       help="额外导出格式，如 docx html latex")
    parser.add_argument("--output_dir", default="./",
                       help="输出目录 (默认: 当前目录)")
    parser.add_argument("--timeout", type=int, default=600,
                       help="轮询超时时间，单位秒 (默认: 600)")
    parser.add_argument("--data_id", help="数据 ID，用于业务标识")
    parser.add_argument("--no_cache", action="store_true",
                       help="绕过缓存获取最新内容")
    
    args = parser.parse_args()
    
    try:
        # 获取 Token
        token = get_token()
        print(f"开始解析: {args.url}")
        
        # 创建任务
        print("创建解析任务...")
        task_id = create_task(
            url=args.url,
            token=token,
            model_version=args.model_version,
            enable_formula=args.enable_formula,
            enable_table=args.enable_table,
            is_ocr=args.is_ocr,
            language=args.language,
            page_ranges=args.page_ranges,
            extra_formats=args.extra_formats,
            data_id=args.data_id,
            no_cache=args.no_cache
        )
        print(f"任务已创建，ID: {task_id}")
        
        # 轮询等待完成
        task_data = poll_task(task_id, token, timeout=args.timeout)
        
        # 获取文件名
        base_filename = get_filename_from_url(args.url)
        if args.data_id:
            base_filename = f"{base_filename}_{args.data_id}"
        
        # 处理结果
        md_path = process_result(task_data, args.output_dir, base_filename)
        
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
        return 1


if __name__ == "__main__":
    sys.exit(main())
