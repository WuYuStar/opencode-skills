"""Obsidian writer module.

Handles writing diary entries to Obsidian vault.
"""

import os
import yaml
from datetime import datetime
from typing import Dict, Any, Optional


class ObsidianWriter:
    """Writes diary entries to Obsidian Daily Notes."""
    
    def __init__(
        self, 
        vault_path: str, 
        daily_notes_dir: str = "Daily Notes",
        filename_template: str = "轨迹日记-{date}.md"
    ):
        """
        Args:
            vault_path: Path to Obsidian vault
            daily_notes_dir: Directory within vault for daily notes
            filename_template: Filename template with {date} placeholder
        """
        self.vault_path = vault_path
        self.daily_notes_dir = daily_notes_dir
        self.filename_template = filename_template
        
        # Ensure directory exists
        self.notes_path = os.path.join(vault_path, daily_notes_dir)
        os.makedirs(self.notes_path, exist_ok=True)
    
    def write_diary(
        self, 
        date: datetime, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """
        Write diary entry to Obsidian.
        
        Returns path to written file.
        """
        date_str = date.strftime("%Y-%m-%d")
        filename = self.filename_template.format(date=date_str)
        filepath = os.path.join(self.notes_path, filename)
        
        # Build frontmatter
        frontmatter = self._build_frontmatter(metadata)
        
        # Build full content
        full_content = self._build_diary_content(frontmatter, content, date)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        return filepath
    
    def _build_frontmatter(self, metadata: Dict) -> str:
        """Build YAML frontmatter."""
        # Clean metadata for YAML
        clean_meta = {}
        for key, value in metadata.items():
            if isinstance(value, list):
                clean_meta[key] = value
            else:
                clean_meta[key] = value
        
        return yaml.dump(
            clean_meta, 
            allow_unicode=True, 
            sort_keys=False,
            default_flow_style=False
        )
    
    def _build_diary_content(
        self, 
        frontmatter: str, 
        content: str, 
        date: datetime
    ) -> str:
        """Build complete diary markdown content with callouts."""
        date_display = date.strftime("%Y年%m月%d日")
        weekday = self._get_weekday(date)
        
        template = f"""---
{frontmatter}---

# 轨迹日记 - {date_display}（{weekday}）

{content}

---

> [!info] 日记元数据
> - **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> - **数据来源**: ActivityWatch
> - **时区**: Asia/Shanghai (UTC+8)
> - **自动生成**: 本日记由 AI 根据 ActivityWatch 追踪数据自动生成
"""
        
        return template
    
    def preview_diary(
        self, 
        date: datetime, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Generate diary content without writing to file."""
        frontmatter = self._build_frontmatter(metadata)
        return self._build_diary_content(frontmatter, content, date)
    
    def file_exists(self, date: datetime) -> bool:
        """Check if diary already exists for date."""
        date_str = date.strftime("%Y-%m-%d")
        filename = self.filename_template.format(date=date_str)
        filepath = os.path.join(self.notes_path, filename)
        return os.path.exists(filepath)
    
    def _get_weekday(self, date: datetime) -> str:
        """Get Chinese weekday name."""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[date.weekday()]
    
    def get_diary_path(self, date: datetime) -> str:
        """Get full path for diary file."""
        date_str = date.strftime("%Y-%m-%d")
        filename = self.filename_template.format(date=date_str)
        return os.path.join(self.notes_path, filename)
    
    @staticmethod
    def create_callout(callout_type: str, title: str, content: str) -> str:
        """
        Create an Obsidian callout box.
        
        Args:
            callout_type: Type of callout (info, tip, warning, success, quote, important)
            title: Callout title
            content: Callout content (can be multiline)
        
        Returns:
            Formatted callout string
        """
        lines = content.strip().split('\n')
        # First line after title should not have extra >
        if lines:
            formatted_lines = [lines[0]]
            for line in lines[1:]:
                formatted_lines.append(f'> {line}')
            formatted_content = '\n> '.join(formatted_lines)
        else:
            formatted_content = ''
        
        return f"> [!{callout_type}] {title}\n> {formatted_content}"
    
    @staticmethod
    def create_summary_callout(stats: Dict) -> str:
        """Create a summary callout with key statistics."""
        total_hours = stats.get('total_hours', 0)
        focus_score = stats.get('focus_score', 0)
        focus_periods = len(stats.get('focus_periods', []))
        switch_count = stats.get('switch_count', 0)
        
        content = f"""**总活跃时间**: {total_hours:.1f} 小时
**Focus Score**: {focus_score}/10
**深度工作时段**: {focus_periods} 个
**应用切换**: {switch_count} 次
**主要任务**: 查看时间线了解详细活动"""
        
        return ObsidianWriter.create_callout('summary', '今日概览', content)
    
    @staticmethod
    def create_tip_callout(title: str, advice: str) -> str:
        """Create a tip callout with actionable advice."""
        return ObsidianWriter.create_callout('tip', title, advice)
    
    @staticmethod
    def create_warning_callout(title: str, warning: str) -> str:
        """Create a warning callout."""
        return ObsidianWriter.create_callout('warning', title, warning)
    
    @staticmethod
    def create_success_callout(title: str, achievement: str) -> str:
        """Create a success callout for achievements."""
        return ObsidianWriter.create_callout('success', title, achievement)
    
    @staticmethod
    def create_quote_callout(title: str, quote: str) -> str:
        """Create a quote callout for highlights."""
        return ObsidianWriter.create_callout('quote', title, quote)
    
    @staticmethod
    def create_important_callout(title: str, content: str) -> str:
        """Create an important callout for key insights."""
        return ObsidianWriter.create_callout('important', title, content)