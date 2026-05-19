"""AI analyzer module for generating diary content.

Constructs prompts and manages AI-powered analysis of activity data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class DiaryAnalyzer:
    """Analyzes activity data and generates diary content."""
    
    def __init__(self, depth: str = "medium", language: str = "zh"):
        """
        Args:
            depth: Analysis depth (light/medium/deep)
            language: Output language (zh/en)
        """
        self.depth = depth
        self.language = language
    
    def generate_diary(
        self, 
        events: List[Dict[str, Any]], 
        stats: Dict[str, Any],
        date: datetime
    ) -> Dict[str, str]:
        """
        Generate complete diary content.
        
        Returns dict with sections: overview, timeline, analysis, suggestions
        """
        # Build timeline text
        timeline_text = self._build_timeline(events)
        
        # Build statistics text
        stats_text = self._build_stats_text(stats)
        
        # Build prompt
        prompt = self._build_prompt(events, stats, date, timeline_text, stats_text)
        
        # In actual implementation, this would call an AI model
        # For now, return structured content for AI processing
        return {
            "prompt": prompt,
            "timeline": timeline_text,
            "stats": stats_text,
            "metadata": self._build_metadata(stats, date)
        }
    
    def _build_timeline(self, events: List[Dict]) -> str:
        """Build detailed timeline text from events."""
        lines = []
        
        for i, event in enumerate(events):
            start_time = event["timestamp"]
            duration = event["duration"]
            end_time = start_time + timedelta(seconds=duration)
            
            time_str = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            duration_str = self._format_duration(duration)
            
            app = event["app"]
            title = event.get("title", "")
            url = event.get("url")
            category = event.get("category", "other")
            
            # Format based on event type and category
            event_type = event.get("type", "")
            
            if event_type == "iteration":
                # Coding-preview iteration pattern
                stats_info = event.get("iteration_stats", {})
                switches = stats_info.get("total_switches", 0)
                lines.append(f"{time_str} ({duration_str}) ⭐ {app}: {title}")
                lines.append(f"  > 进行编码-预览迭代，期间 {switches} 次切换工具")
                
            elif event_type == "research":
                # Information research pattern
                domains = event.get("domains", [])
                domain_str = ", ".join(domains[:3]) if domains else ""
                lines.append(f"{time_str} ({duration_str}) 🌐 {app}: {title}")
                if domain_str:
                    lines.append(f"  > 访问了: {domain_str}")
                    
            elif event_type == "communication_session":
                # Communication session pattern
                check_count = event.get("check_count", 0)
                apps = event.get("communication_apps", [])
                lines.append(f"{time_str} ({duration_str}) 💬 通讯时段")
                lines.append(f"  > 查看 {', '.join(apps)} 共 {check_count} 次，总时长 {duration_str}")
                
            elif category == "browser" and url:
                domain = event.get("domain", "")
                lines.append(f"{time_str} ({duration_str}) 🌐 {app}: {title}")
                if domain:
                    lines.append(f"  └─ 📍 {domain}")
                    
            elif category == "development":
                lines.append(f"{time_str} ({duration_str}) 💻 {app}: {title}")
                
            elif category == "communication":
                lines.append(f"{time_str} ({duration_str}) 💬 {app}: {title}")
                
            elif category == "productivity":
                lines.append(f"{time_str} ({duration_str}) 📝 {app}: {title}")
                
            elif category == "media":
                lines.append(f"{time_str} ({duration_str}) 🎵 {app}: {title}")
                
            else:
                lines.append(f"{time_str} ({duration_str}) 📊 {app}: {title}")
        
        return "\n".join(lines)
    
    def _build_stats_text(self, stats: Dict) -> str:
        """Build statistics summary text."""
        lines = []
        
        total_hours = stats.get("total_hours", 0)
        lines.append(f"总活跃时间: {total_hours:.1f} 小时")
        
        # Top apps
        app_stats = stats.get("app_stats", {})
        lines.append("\n应用使用时间:")
        for app, duration in list(app_stats.items())[:10]:
            hours = duration / 3600
            lines.append(f"  - {app}: {hours:.1f}h")
        
        # Categories
        category_stats = stats.get("category_stats", {})
        lines.append("\n活动类别:")
        for cat, duration in category_stats.items():
            hours = duration / 3600
            lines.append(f"  - {cat}: {hours:.1f}h")
        
        # Focus periods
        focus_periods = stats.get("focus_periods", [])
        lines.append(f"\n深度工作时段: {len(focus_periods)} 个")
        for i, period in enumerate(focus_periods[:5], 1):
            start = period["start"].strftime("%H:%M")
            duration = period["duration"]
            lines.append(f"  {i}. {start} ({self._format_duration(duration)})")
        
        lines.append(f"\n应用切换次数: {stats.get('switch_count', 0)}")
        
        return "\n".join(lines)
    
    def _build_prompt(
        self, 
        events: List[Dict], 
        stats: Dict, 
        date: datetime,
        timeline_text: str,
        stats_text: str
    ) -> str:
        """Build AI analysis prompt."""
        
        if self.language == "zh":
            prompt = f"""基于以下电脑使用轨迹数据，为用户生成一份轨迹日记。

【日期】{date.strftime('%Y年%m月%d日')} ({self._get_weekday(date)})

【数据概览】
{stats_text}

【详细时间线】
{timeline_text}

请生成以下内容（使用中文）：

## 1. 今日概览（200-300字）
- 描述今天的整体工作/生活节奏
- 主要完成的任务或活动主题
- 整体效率感受

## 2. 详细时间线（默认折叠）
将详细时间线放在 Obsidian 可折叠 Callout 中：
```markdown
> [!info]- 🕐 详细时间线（点击展开）
>
> [按上午/下午/晚上分段描述，每行都要以 > 开头]
> - 每个时段的主要活动
> - 具体做了什么（根据窗口标题和URL推断）
> - 效率标记：⭐深度专注 / ⚡快速切换 / 🔄被打断
```

注意：`-` 表示默认折叠，`+` 表示默认展开。每行内容都要以 `> ` 开头。

## 3. 效率分析

### 专注度评分：X/10
- 评分理由（基于连续专注时长、切换频率）

### 深度工作时段
- 列出 2-4 个深度工作时段（连续专注 >30分钟）
- 说明每个时段的具体内容

### 打断分析
- 主要打断源（哪些应用导致频繁切换）
- 打断模式分析

### 时间分配
| 类别 | 时长 | 占比 | 评价 |
|------|------|------|------|
| 开发工作 | Xh Xm | XX% | 充足/不足/合理 |
| 学习阅读 | Xh Xm | XX% | ... |
| 通讯协作 | Xh Xm | XX% | ... |
| 娱乐休闲 | Xh Xm | XX% | ... |
| 其他 | Xh Xm | XX% | ... |

## 4. 今日所学

基于用户今天浏览的网页和使用的工具，提取用户了解/学习到的新知识：

格式要求：
- 使用 `> [!info] 今日所学` Callout
- 每条格式：`📚 [主题/概念]：[一句话描述，不超过30字]`
- 数量不限，但只保留有实质内容的（去除导航页、重复内容）
- 来源可以是：技术项目、工具软件、职业信息、行业动态等

示例：
📚 UI-TARS：字节跳动的原生 Agent GUI 自动化交互方案
📚 LaTeX 平台：对比了 TeXPage、Overleaf、LoongTeX 的功能特性
📚 职业讨论：LINUX DO 社区关于体制内工作与 AI 应用开发行情的讨论

## 5. 建议与反馈

### 改进建议（1-2条具体、可执行）
- 基于今天数据的发现
- 具体行动建议

### 今日亮点
- 1条正面反馈（如"保持了XX分钟连续编程"）

语气要求：
- 友好专业，像一位了解用户工作习惯的高效能教练
- 具体而非笼统，用数据说话
- 客观分析，不带评判
- 适当使用 emoji 增加可读性

排版要求（使用 Obsidian Callout 增强可读性）：
- 今日概览使用 `> [!summary] 今日概览` 蓝色信息框
- 关键统计数据使用 `> [!info] 数据统计` 蓝色框
- 深度工作时段使用 `> [!success] 深度工作时段` 绿色成功框
- 效率分析和洞察使用 `> [!tip] 分析洞察` 绿色提示框
- 需要改进的地方使用 `> [!warning] 注意` 橙色警告框
- 今日亮点使用 `> [!quote] 今日亮点` 灰色引用框
- 重要结论使用 `> [!important] 重要结论` 紫色重要框
"""
        else:
            prompt = f"""Generate a daily trajectory diary based on the following computer usage data.

【Date】{date.strftime('%Y-%m-%d')} ({date.strftime('%A')})

【Data Overview】
{stats_text}

【Detailed Timeline】
{timeline_text}

Please generate (in English):

## 1. Daily Overview (200-300 words)
## 2. Detailed Timeline (morning/afternoon/evening)
## 3. Productivity Analysis
   - Focus score (1-10)
   - Deep work periods
   - Interruption analysis
   - Time allocation table
## 4. Suggestions & Highlights

Tone: Friendly, professional, data-driven coach.
"""
        
        return prompt
    
    def _build_metadata(self, stats: Dict, date: datetime) -> Dict:
        """Build YAML frontmatter metadata."""
        total_seconds = stats.get("total_duration", 0)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        # Calculate focus score (simple heuristic)
        focus_periods = stats.get("focus_periods", [])
        switch_count = stats.get("switch_count", 0)
        total_hours = stats.get("total_hours", 0)
        
        if total_hours > 0:
            # Improved scoring algorithm
            # Base score: 5
            focus_score = 5
            
            # Bonus for focus periods (max +3)
            focus_score += min(len(focus_periods), 3)
            
            # Switch frequency evaluation
            switches_per_hour = switch_count / total_hours
            if switches_per_hour < 15:
                focus_score += 1  # Low switching, good focus
            elif switches_per_hour > 25:
                focus_score -= 1  # Too much switching
            
            # Duration evaluation
            if total_hours < 4:
                focus_score -= 1  # Short day
            elif total_hours > 8:
                focus_score += 1  # Long productive day
            
            focus_score = min(10, max(1, focus_score))
        else:
            focus_score = 0
        
        # Top apps
        app_stats = stats.get("app_stats", {})
        top_apps = []
        for app, duration in list(app_stats.items())[:5]:
            app_hours = int(duration // 3600)
            app_minutes = int((duration % 3600) // 60)
            top_apps.append(f"{app}: {app_hours}h {app_minutes}m")
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_active_time": f"{hours}h {minutes}m",
            "focus_score": round(focus_score, 1),
            "top_apps": top_apps,
            "event_count": stats.get("event_count", 0),
            "switch_count": stats.get("switch_count", 0),
            "focus_periods": len(focus_periods),
            "tags": ["轨迹日记", "activitywatch", "auto-generated"]
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _get_weekday(self, date: datetime) -> str:
        """Get Chinese weekday name."""
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[date.weekday()]