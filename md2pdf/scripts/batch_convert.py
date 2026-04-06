#!/usr/bin/env python3
"""
md2pdf Batch Conversion Script
批量转换 Markdown 文件为 PDF
支持并行处理、自动中文检测、智能模板选择
"""

import argparse
import glob
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple


# 中文字符检测正则
CHINESE_CHARS = re.compile(r'[\u4e00-\u9fff]')

# 模板路径（相对于 skill 根目录）
TEMPLATES = {
    'default': 'templates/default.css',
    'modern': 'templates/modern.css',
    'code': 'templates/code-highlight.css',
    'chinese-default': 'templates/chinese-default.css',
    'chinese-modern': 'templates/chinese-modern.css',
}


def detect_chinese(content: str) -> bool:
    """检测内容是否包含中文字符"""
    return bool(CHINESE_CHARS.search(content))


def detect_chinese_in_file(file_path: Path) -> bool:
    """检测文件是否包含中文字符"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(8192)  # 只读取前8KB检测
            return detect_chinese(content)
    except Exception:
        return False


def find_skill_root() -> Path:
    """查找 skill 根目录"""
    # 从脚本位置向上查找
    script_dir = Path(__file__).parent.resolve()
    skill_root = script_dir.parent
    
    # 验证模板目录存在
    if (skill_root / 'templates').exists():
        return skill_root
    
    # 如果找不到，使用当前目录
    return Path.cwd()


def get_template_path(template_name: str, skill_root: Path) -> Optional[Path]:
    """获取模板完整路径"""
    if template_name in TEMPLATES:
        template_path = skill_root / TEMPLATES[template_name]
        if template_path.exists():
            return template_path
    
    # 如果是绝对路径或相对路径
    template_path = Path(template_name)
    if template_path.exists():
        return template_path
    
    # 在模板目录中查找
    template_path = skill_root / 'templates' / f"{template_name}.css"
    if template_path.exists():
        return template_path
    
    return None


def select_template(file_path: Path, skill_root: Path, auto_detect: bool = True, 
                    prefer_chinese: bool = True) -> Optional[Path]:
    """智能选择模板"""
    if not auto_detect:
        return get_template_path('default', skill_root)
    
    # 检测是否包含中文
    has_chinese = detect_chinese_in_file(file_path)
    
    if has_chinese and prefer_chinese:
        # 优先使用中文模板
        template = get_template_path('chinese-modern', skill_root)
        if template:
            return template
        template = get_template_path('chinese-default', skill_root)
        if template:
            return template
    
    # 检测是否包含代码块
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if '```' in content or '`' in content:
                template = get_template_path('code', skill_root)
                if template:
                    return template
    except Exception:
        pass
    
    # 默认使用 modern 模板
    template = get_template_path('modern', skill_root)
    if template:
        return template
    
    return get_template_path('default', skill_root)


def convert_single_file(input_file: Path, output_file: Optional[Path] = None,
                       template: Optional[Path] = None, extra_args: Optional[List[str]] = None) -> Tuple[bool, str]:
    """转换单个文件"""
    if extra_args is None:
        extra_args = []
    
    # 确定输出文件路径
    if output_file is None:
        output_file = input_file.with_suffix('.pdf')
    
    # 构建命令
    cmd = ['md2pdf', '-i', str(input_file), '-o', str(output_file)]
    
    if template and template.exists():
        cmd.extend(['--css', str(template)])
    
    # 添加 markdown 扩展（支持代码高亮、表格等）
    cmd.extend(['--extras', 'tables', '--extras', 'fenced_code'])
    
    cmd.extend(extra_args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )
        
        if result.returncode == 0:
            return True, str(output_file)
        else:
            return False, result.stderr or "Unknown error"
    except subprocess.TimeoutExpired:
        return False, "Conversion timeout"
    except Exception as e:
        return False, str(e)


def convert_file_with_progress(args: Tuple[int, int, Path, Path, Optional[Path], List[str]]) -> Tuple[int, bool, str]:
    """转换文件并返回进度信息"""
    index, total, input_file, output_file, template, extra_args = args
    
    success, message = convert_single_file(input_file, output_file, template, extra_args)
    
    # 打印进度
    status = "✓" if success else "✗"
    progress = f"[{index+1}/{total}]"
    print(f"{progress} {status} {input_file.name}")
    
    if not success:
        print(f"    错误: {message}")
    
    return index, success, message


def batch_convert(input_files: List[Path], output_dir: Optional[Path] = None,
                  template: Optional[str] = None, workers: int = 4,
                  auto_detect: bool = True, extra_args: Optional[List[str]] = None) -> Tuple[int, int]:
    """批量转换文件"""
    if extra_args is None:
        extra_args = []
    
    skill_root = find_skill_root()
    total = len(input_files)
    success_count = 0
    failed_count = 0
    
    print(f"开始批量转换，共 {total} 个文件，使用 {workers} 个并行进程")
    print(f"Skill 根目录: {skill_root}")
    print("")
    
    # 准备任务参数
    tasks = []
    for i, input_file in enumerate(input_files):
        if output_dir:
            output_file = output_dir / f"{input_file.stem}.pdf"
        else:
            output_file = input_file.with_suffix('.pdf')
        
        # 选择模板
        if template:
            template_path = get_template_path(template, skill_root)
        else:
            template_path = select_template(input_file, skill_root, auto_detect)
        
        tasks.append((i, total, input_file, output_file, template_path, extra_args))
    
    # 并行执行
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(convert_file_with_progress, task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                index, success, message = future.result()
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"✗ 任务异常: {e}")
                failed_count += 1
    
    return success_count, failed_count


def expand_globs(patterns: List[str]) -> List[Path]:
    """展开 glob 模式为文件列表"""
    files = set()
    
    for pattern in patterns:
        # 如果包含通配符，使用 glob
        if '*' in pattern or '?' in pattern:
            matched = glob.glob(pattern, recursive=True)
            for match in matched:
                path = Path(match)
                if path.is_file() and path.suffix.lower() in ['.md', '.markdown']:
                    files.add(path.resolve())
        else:
            # 普通路径
            path = Path(pattern)
            if path.is_file() and path.suffix.lower() in ['.md', '.markdown']:
                files.add(path.resolve())
            elif path.is_dir():
                # 如果是目录，查找所有 markdown 文件
                for md_file in path.rglob('*.md'):
                    files.add(md_file.resolve())
                for md_file in path.rglob('*.markdown'):
                    files.add(md_file.resolve())
    
    return sorted(list(files))


def main():
    parser = argparse.ArgumentParser(
        description='批量转换 Markdown 文件为 PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 转换单个文件
  %(prog)s document.md
  
  # 使用指定模板
  %(prog)s document.md --template chinese-modern
  
  # 批量转换多个文件
  %(prog)s "*.md"
  
  # 递归转换目录中的所有 markdown 文件
  %(prog)s ./docs/
  
  # 指定输出目录
  %(prog)s "*.md" --output-dir ./output/
  
  # 使用 8 个并行进程
  %(prog)s "**/*.md" --workers 8
        """
    )
    
    parser.add_argument(
        'inputs',
        nargs='+',
        help='输入文件或模式（支持 glob，如 "*.md"、"**/*.md"）'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        help='输出目录（默认：与输入文件同目录）'
    )
    
    parser.add_argument(
        '-t', '--template',
        choices=list(TEMPLATES.keys()) + ['auto'],
        default='auto',
        help='使用的模板（默认：auto，自动检测）'
    )
    
    parser.add_argument(
        '-w', '--workers',
        type=int,
        default=4,
        help='并行工作进程数（默认：4）'
    )
    
    parser.add_argument(
        '--no-auto-detect',
        action='store_true',
        help='禁用自动模板检测'
    )
    
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help='列出可用模板'
    )
    
    parser.add_argument(
        '--md-arg',
        action='append',
        default=[],
        help='传递给 md2pdf 的额外参数（可多次使用）'
    )
    
    args = parser.parse_args()
    
    # 列出模板
    if args.list_templates:
        print("可用模板:")
        for name, path in TEMPLATES.items():
            print(f"  {name:20} -> {path}")
        return 0
    
    # 展开文件列表
    input_files = expand_globs(args.inputs)
    
    if not input_files:
        print("错误: 未找到匹配的 Markdown 文件")
        return 1
    
    print(f"找到 {len(input_files)} 个文件:")
    for f in input_files[:10]:  # 只显示前10个
        print(f"  - {f}")
    if len(input_files) > 10:
        print(f"  ... 还有 {len(input_files) - 10} 个文件")
    print("")
    
    # 执行批量转换
    template = None if args.template == 'auto' else args.template
    success, failed = batch_convert(
        input_files,
        output_dir=args.output_dir,
        template=template,
        workers=args.workers,
        auto_detect=not args.no_auto_detect,
        extra_args=args.md_arg
    )
    
    # 输出结果
    print("")
    print("=" * 50)
    print(f"转换完成: {success} 成功, {failed} 失败")
    print("=" * 50)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
