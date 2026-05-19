"""Command-line interface for aw-diary.

Main entry point for the ActivityWatch diary generator.
"""

import os
import sys
import yaml
import click
from datetime import datetime, timedelta
from pathlib import Path

from .fetcher import ActivityWatchFetcher
from .processor import SmartMerger
from .analyzer import DiaryAnalyzer
from .writer import ObsidianWriter


def load_config() -> dict:
    """Load configuration from config file."""
    config_paths = [
        Path.home() / ".agents" / "skills" / "aw-diary" / "config.yaml",
        Path("config.yaml"),
    ]
    
    for path in config_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    
    # Default config
    return {
        "activitywatch": {"host": "localhost", "port": 5600},
        "obsidian": {
            "vault_path": str(Path.home() / "obsidian-vault"),
            "daily_notes_dir": "Daily Notes",
            "filename_template": "轨迹日记-{date}.md"
        },
        "processing": {"merge_gap": 60, "min_duration": 30},
        "analysis": {"depth": "medium", "language": "zh"}
    }


@click.command()
@click.option('--date', '-d', help='指定日期 (YYYY-MM-DD)')
@click.option('--today', '-t', is_flag=True, help='生成今日日记')
@click.option('--yesterday', '-y', is_flag=True, help='生成昨日日记')
@click.option('--preview', '-p', is_flag=True, help='预览模式，不写入文件')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.option('--force', '-f', is_flag=True, help='强制覆盖已存在的日记')
def main(date, today, yesterday, preview, verbose, force):
    """
    ActivityWatch 轨迹日记生成器
    
    从 ActivityWatch 数据生成每日轨迹日记，并写入 Obsidian。
    
    示例:
        aw-diary --today              # 生成今日日记
        aw-diary -d 2024-01-15        # 生成指定日期日记
        aw-diary -y -p                # 预览昨日日记（不保存）
    """
    # Load config
    config = load_config()
    
    # Determine target date
    target_date = None
    if today:
        target_date = datetime.now()
    elif yesterday:
        target_date = datetime.now() - timedelta(days=1)
    elif date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            click.echo("错误: 日期格式应为 YYYY-MM-DD", err=True)
            sys.exit(1)
    else:
        # Default to today
        target_date = datetime.now()
    
    if verbose:
        click.echo(f"目标日期: {target_date.strftime('%Y-%m-%d')}")
    
    # Initialize components
    try:
        # ActivityWatch fetcher
        aw_config = config.get("activitywatch", {})
        fetcher = ActivityWatchFetcher(
            host=aw_config.get("host", "localhost"),
            port=aw_config.get("port", 5600),
            timezone_str=config.get("processing", {}).get("timezone", "Asia/Shanghai")
        )
        
        # Check connection
        if verbose:
            click.echo("正在连接 ActivityWatch...")
        
        if not fetcher.check_connection():
            click.echo(
                f"错误: 无法连接到 ActivityWatch ({aw_config.get('host', 'localhost')}:{aw_config.get('port', 5600)})",
                err=True
            )
            click.echo("请确保 ActivityWatch 正在运行。", err=True)
            sys.exit(1)
        
        if verbose:
            click.echo("✓ ActivityWatch 连接成功")
        
        # Fetch data
        if verbose:
            click.echo("正在获取数据...")
        
        data = fetcher.get_date_data(target_date)
        
        event_counts = {
            "window": len(data.get("window", [])),
            "web": len(data.get("web", [])),
            "afk": len(data.get("afk", []))
        }
        
        if verbose:
            click.echo(f"  窗口事件: {event_counts['window']}")
            click.echo(f"  网页事件: {event_counts['web']}")
            click.echo(f"  AFK 事件: {event_counts['afk']}")
        
        if sum(event_counts.values()) == 0:
            click.echo("警告: 该日期没有 ActivityWatch 数据", err=True)
            click.echo("请确保 ActivityWatch 在目标日期正在运行。", err=True)
            sys.exit(1)
        
        # Process data
        if verbose:
            click.echo("正在处理数据...")
        
        processor = SmartMerger(
            merge_gap=config.get("processing", {}).get("merge_gap", 60),
            min_duration=config.get("processing", {}).get("min_duration", 30),
            timezone_str=config.get("processing", {}).get("timezone", "Asia/Shanghai")
        )
        
        events = processor.process(data)
        stats = processor.calculate_stats(events)
        
        if verbose:
            click.echo(f"  原始事件: {sum(event_counts.values())}")
            click.echo(f"  合并后事件: {len(events)}")
            click.echo(f"  总活跃时间: {stats.get('total_hours', 0):.1f} 小时")
        
        # Analyze
        if verbose:
            click.echo("正在生成分析...")
        
        analyzer = DiaryAnalyzer(
            depth=config.get("analysis", {}).get("depth", "medium"),
            language=config.get("analysis", {}).get("language", "zh")
        )
        
        diary_data = analyzer.generate_diary(events, stats, target_date)
        
        # In a real implementation, we would call an AI model here
        # For this skill, we output the prompt and structured data
        # The AI agent using this skill will process the prompt
        
        # Obsidian writer
        obsidian_config = config.get("obsidian", {})
        writer = ObsidianWriter(
            vault_path=obsidian_config.get("vault_path", str(Path.home() / "obsidian-vault")),
            daily_notes_dir=obsidian_config.get("daily_notes_dir", "Daily Notes"),
            filename_template=obsidian_config.get("filename_template", "轨迹日记-{date}.md")
        )
        
        # Check if file exists
        if not force and writer.file_exists(target_date):
            click.echo(f"日记已存在: {writer.get_diary_path(target_date)}")
            click.echo("使用 --force 覆盖，或使用 --preview 预览")
            sys.exit(0)
        
        # Generate or preview
        if preview:
            # Show preview
            preview_content = writer.preview_diary(
                target_date,
                diary_data["prompt"],  # In real use, this would be AI output
                diary_data["metadata"]
            )
            click.echo("\n" + "="*60)
            click.echo("预览模式（未写入文件）")
            click.echo("="*60)
            click.echo(preview_content)
            click.echo("="*60)
        else:
            # Write to file
            # Note: In actual implementation, we would:
            # 1. Send diary_data["prompt"] to AI
            # 2. Get AI-generated content
            # 3. Write that content to Obsidian
            
            # For now, write structured data as placeholder
            filepath = writer.write_diary(
                target_date,
                diary_data["prompt"],  # Placeholder for AI output
                diary_data["metadata"]
            )
            
            click.echo(f"✓ 日记已生成: {filepath}")
            click.echo(f"  总活跃时间: {stats.get('total_hours', 0):.1f} 小时")
            click.echo(f"  事件数量: {len(events)}")
            click.echo(f"  深度工作时段: {stats.get('focus_period_count', 0)}")
            
            if not preview:
                click.echo("\n注意: 当前输出为结构化数据，需要 AI 分析生成最终日记内容")
                click.echo("请使用 AI 助手处理生成的文件，或启用 AI 自动分析功能")
    
    except Exception as e:
        click.echo(f"错误: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()