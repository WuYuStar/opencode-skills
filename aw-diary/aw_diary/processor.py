"""ActivityWatch data processor module.

Implements intelligent event merging and data cleaning.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple, Optional
from urllib.parse import urlparse
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


class SmartMerger:
    """Intelligently merges ActivityWatch events."""
    
    def __init__(self, merge_gap: int = 60, min_duration: int = 30, timezone_str: str = "Asia/Shanghai"):
        """
        Args:
            merge_gap: Merge events within this many seconds
            min_duration: Filter out events shorter than this (seconds)
            timezone_str: Target timezone for display (e.g., "Asia/Shanghai")
        """
        self.merge_gap = merge_gap
        self.min_duration = min_duration
        self.timezone = ZoneInfo(timezone_str)
    
    def process(self, data: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """
        Process raw ActivityWatch data into merged timeline.
        
        Returns list of processed events sorted by time.
        """
        # Combine all events with source tags
        all_events = []
        
        # Process window events
        for event in data.get("window", []):
            processed = self._process_window_event(event)
            if processed:
                all_events.append(processed)
        
        # Process web events (enhance window events with URLs)
        web_events = {}
        for event in data.get("web", []):
            processed = self._process_web_event(event)
            if processed:
                # Store by timestamp for merging
                key = processed["timestamp"]
                web_events[key] = processed
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])
        
        # Merge consecutive events
        merged = self._merge_events(all_events)
        
        # Filter short events
        filtered = [e for e in merged if e["duration"] >= self.min_duration]
        
        # Enhance with web data where possible
        self._enhance_with_web_data(filtered, web_events)
        
        # Merge behavior patterns (coding-preview iterations, etc.)
        pattern_merged = self._merge_behavior_patterns(filtered)
        
        return pattern_merged
    
    def _process_window_event(self, event: Dict) -> Optional[Dict]:
        """Process a window event."""
        data = event.get("data", {})
        if not data:
            return None
        
        return {
            "timestamp": self._parse_timestamp(event["timestamp"]),
            "duration": event.get("duration", 0),
            "type": "window",
            "app": data.get("app", "Unknown"),
            "title": data.get("title", ""),
            "url": None,
            "category": self._categorize_app(data.get("app", ""))
        }
    
    def _process_web_event(self, event: Dict) -> Optional[Dict]:
        """Process a web event."""
        data = event.get("data", {})
        if not data or not data.get("url"):
            return None
        
        return {
            "timestamp": self._parse_timestamp(event["timestamp"]),
            "duration": event.get("duration", 0),
            "type": "web",
            "app": "Browser",
            "title": data.get("title", ""),
            "url": data.get("url"),
            "domain": self._extract_domain(data.get("url", "")),
            "category": "browsing"
        }
    
    def _merge_events(self, events: List[Dict]) -> List[Dict]:
        """Merge consecutive similar events."""
        if not events:
            return []
        
        merged = []
        current = events[0].copy()
        
        for event in events[1:]:
            time_diff = (event["timestamp"] - current["timestamp"]).total_seconds()
            time_gap = time_diff - current["duration"]
            
            # Check if events should be merged
            if (time_gap <= self.merge_gap and 
                self._is_similar_activity(current, event)):
                # Merge: extend duration
                current["duration"] = time_diff + event["duration"]
                # Keep the most informative title
                if len(event.get("title", "")) > len(current.get("title", "")):
                    current["title"] = event["title"]
                # Keep URL if available
                if event.get("url"):
                    current["url"] = event["url"]
                    current["domain"] = event.get("domain")
            else:
                # Save current and start new
                merged.append(current)
                current = event.copy()
        
        # Don't forget the last event
        merged.append(current)
        
        return merged
    
    def _is_similar_activity(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events represent the same activity."""
        # Same app
        if event1["app"] != event2["app"]:
            return False
        
        # Same category
        if event1.get("category") != event2.get("category"):
            return False
        
        # For window events, check title similarity
        if event1["type"] == "window" and event2["type"] == "window":
            title1 = event1.get("title", "")
            title2 = event2.get("title", "")
            
            # If titles are identical, definitely merge
            if title1 == title2:
                return True
            
            # Check if same file/document (for editors)
            if self._extract_document_name(title1) == self._extract_document_name(title2):
                return True
            
            # Check similarity (simple approach)
            similarity = self._title_similarity(title1, title2)
            if similarity > 0.7:
                return True
        
        # For web events, same domain
        if event1["type"] == "web" and event2["type"] == "web":
            domain1 = event1.get("domain", "")
            domain2 = event2.get("domain", "")
            if domain1 and domain2 and domain1 == domain2:
                return True
        
        return False
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate simple similarity between two titles."""
        if not title1 or not title2:
            return 0.0
        
        # Extract meaningful parts (remove common suffixes like " - Google Chrome")
        clean1 = re.sub(r'\s*[-–]\s*(?:Google Chrome|Chrome|Mozilla Firefox|Firefox|Edge|Safari)$', '', title1)
        clean2 = re.sub(r'\s*[-–]\s*(?:Google Chrome|Chrome|Mozilla Firefox|Firefox|Edge|Safari)$', '', title2)
        
        # Simple word overlap
        words1 = set(clean1.lower().split())
        words2 = set(clean2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_document_name(self, title: str) -> str:
        """Extract document/file name from window title."""
        # Match patterns like "filename.ext - App" or "App - filename.ext"
        patterns = [
            r'^(.+?)\s*[-–]\s*(?:Microsoft Word|Word|Excel|PowerPoint|VS Code|Visual Studio Code|Sublime Text)',
            r'(?:Microsoft Word|Word|Excel|PowerPoint|VS Code|Visual Studio Code|Sublime Text)\s*[-–]\s*(.+?)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ""
    
    def _categorize_app(self, app_name: str) -> str:
        """Categorize application by name."""
        app_lower = app_name.lower()
        
        categories = {
            "development": [
                "code", "vscode", "visual studio", "intellij", "pycharm", 
                "sublime", "atom", "vim", "emacs", "terminal", "iterm",
                "github", "gitkraken", "docker"
            ],
            "browser": [
                "chrome", "firefox", "safari", "edge", "opera", "brave"
            ],
            "communication": [
                "slack", "teams", "discord", "zoom", "wechat", "weixin", "telegram",
                "whatsapp", "signal", "mail", "outlook", "gmail", "qq"
            ],
            "productivity": [
                "obsidian", "notion", "evernote", "onenote", "todoist",
                "ticktick", "calendar", "excel", "word", "powerpoint"
            ],
            "media": [
                "spotify", "itunes", "music", "vlc", "mp", "youtube",
                "netflix", "bilibili"
            ],
            "gaming": [
                "steam", "epic", "game", "lol", "dota", "overwatch"
            ]
        }
        
        for category, apps in categories.items():
            for app in apps:
                if app in app_lower:
                    return category
        
        return "other"
    
    def _enhance_with_web_data(self, events: List[Dict], web_events: Dict):
        """Enhance window events with web data where applicable."""
        for event in events:
            if event["category"] == "browser":
                # Find matching web event by timestamp
                ts = event["timestamp"]
                # Look for web events within a small time window
                for web_ts, web_event in web_events.items():
                    time_diff = abs((ts - web_ts).total_seconds())
                    if time_diff < 5:  # Within 5 seconds
                        event["url"] = web_event.get("url")
                        event["domain"] = web_event.get("domain")
                        break
    
    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse ISO timestamp string and convert to local timezone."""
        try:
            # Parse the ISO timestamp (includes timezone info like +00:00)
            dt = datetime.fromisoformat(ts_str)
            
            # If timestamp has timezone info, convert to target timezone
            if dt.tzinfo is not None:
                dt = dt.astimezone(self.timezone)
            else:
                # If no timezone, assume UTC and convert
                dt = dt.replace(tzinfo=timezone.utc).astimezone(self.timezone)
            
            return dt
        except Exception as e:
            print(f"Warning: Failed to parse timestamp '{ts_str}': {e}")
            return datetime.now(self.timezone)
    
    def _merge_behavior_patterns(self, events: List[Dict]) -> List[Dict]:
        """
        Merge specific behavior patterns into higher-level descriptions.
        
        Patterns:
        1. Coding-Preview Iteration: Terminal + Browser/Editor alternating
        2. Information Research: Continuous web browsing
        3. Communication Sessions: Scattered messaging app usage
        """
        if not events:
            return events
        
        result = []
        i = 0
        
        while i < len(events):
            event = events[i]
            
            # Pattern 1: Coding-Preview Iteration
            if self._is_coding_event(event):
                pattern_events = [event]
                j = i + 1
                
                # Collect alternating coding and preview events
                while j < len(events):
                    next_event = events[j]
                    gap = (next_event["timestamp"] - 
                           (pattern_events[-1]["timestamp"] + timedelta(seconds=pattern_events[-1]["duration"]))
                          ).total_seconds()
                    
                    # Allow small gaps (< 2 minutes)
                    if gap > 120:
                        break
                    
                    # Check if it's part of the iteration pattern
                    if self._is_coding_event(next_event) or self._is_preview_event(next_event):
                        pattern_events.append(next_event)
                        j += 1
                    else:
                        break
                
                # If we have enough events for a pattern (>= 3 and total duration > 5 min)
                if len(pattern_events) >= 3:
                    total_duration = sum(e["duration"] for e in pattern_events)
                    if total_duration >= 300:  # 5 minutes
                        merged_event = self._create_iteration_event(pattern_events)
                        result.append(merged_event)
                        i = j
                        continue
            
            # Pattern 2: Information Research (continuous browsing)
            if event["category"] == "browser":
                pattern_events = [event]
                j = i + 1
                
                while j < len(events):
                    next_event = events[j]
                    gap = (next_event["timestamp"] - 
                           (pattern_events[-1]["timestamp"] + timedelta(seconds=pattern_events[-1]["duration"]))
                          ).total_seconds()
                    
                    if gap > 60:  # 1 minute gap max for browsing
                        break
                    
                    if next_event["category"] == "browser":
                        pattern_events.append(next_event)
                        j += 1
                    else:
                        break
                
                if len(pattern_events) >= 2:
                    total_duration = sum(e["duration"] for e in pattern_events)
                    if total_duration >= 300:  # 5 minutes
                        merged_event = self._create_research_event(pattern_events)
                        result.append(merged_event)
                        i = j
                        continue
            
            # Pattern 3: Communication Sessions (scattered messaging)
            if event["category"] == "communication":
                pattern_events = [event]
                j = i + 1
                
                while j < len(events):
                    next_event = events[j]
                    gap = (next_event["timestamp"] - 
                           (pattern_events[-1]["timestamp"] + timedelta(seconds=pattern_events[-1]["duration"]))
                          ).total_seconds()
                    
                    # Communication can have larger gaps (up to 10 minutes)
                    if gap > 600:
                        break
                    
                    if next_event["category"] == "communication":
                        pattern_events.append(next_event)
                        j += 1
                    else:
                        break
                
                if len(pattern_events) >= 2:
                    merged_event = self._create_communication_event(pattern_events)
                    result.append(merged_event)
                    i = j
                    continue
            
            # No pattern matched, keep the event as is
            result.append(event)
            i += 1
        
        return result
    
    def _is_coding_event(self, event: Dict) -> bool:
        """Check if event is a coding/development activity."""
        coding_apps = ["WindowsTerminal.exe", "terminal", "code", "vscode", "vim", 
                      "notepad++.exe", "sublime_text.exe", "pycharm", "intellij"]
        app_lower = event["app"].lower()
        return any(app in app_lower for app in coding_apps) or event.get("category") == "development"
    
    def _is_preview_event(self, event: Dict) -> bool:
        """Check if event is a preview/browsing activity."""
        preview_apps = ["chrome.exe", "firefox.exe", "msedge.exe", "safari.exe",
                       "opera.exe", "brave.exe"]
        app_lower = event["app"].lower()
        is_browser = any(app in app_lower for app in preview_apps)
        
        # Also include PDF viewers as preview
        is_pdf = "pdf" in app_lower and "edit" in app_lower
        
        return is_browser or is_pdf or event.get("category") == "browser"
    
    def _create_iteration_event(self, events: List[Dict]) -> Dict:
        """Create a merged event for coding-preview iteration pattern."""
        start_time = events[0]["timestamp"]
        end_time = events[-1]["timestamp"] + timedelta(seconds=events[-1]["duration"])
        total_duration = (end_time - start_time).total_seconds()
        
        # Extract main theme from titles
        titles = [e.get("title", "") for e in events if e.get("title")]
        theme = self._extract_iteration_theme(titles)
        
        # Count switches
        coding_count = sum(1 for e in events if self._is_coding_event(e))
        preview_count = sum(1 for e in events if self._is_preview_event(e))
        
        return {
            "timestamp": start_time,
            "duration": total_duration,
            "type": "iteration",
            "app": "迭代开发",
            "title": theme or "编码与预览迭代",
            "url": None,
            "category": "development",
            "sub_events": events,
            "iteration_stats": {
                "coding_count": coding_count,
                "preview_count": preview_count,
                "total_switches": len(events) - 1
            }
        }
    
    def _create_research_event(self, events: List[Dict]) -> Dict:
        """Create a merged event for information research pattern."""
        start_time = events[0]["timestamp"]
        end_time = events[-1]["timestamp"] + timedelta(seconds=events[-1]["duration"])
        total_duration = (end_time - start_time).total_seconds()
        
        # Extract domains and topics
        domains = list(set([e.get("domain", "") for e in events if e.get("domain")]))
        titles = [e.get("title", "") for e in events if e.get("title")]
        topic = self._extract_research_topic(titles)
        
        return {
            "timestamp": start_time,
            "duration": total_duration,
            "type": "research",
            "app": "信息检索",
            "title": topic or "网页浏览",
            "url": None,
            "domain": domains[0] if domains else None,
            "domains": domains,
            "category": "browser",
            "sub_events": events
        }
    
    def _create_communication_event(self, events: List[Dict]) -> Dict:
        """Create a merged event for communication session pattern."""
        start_time = events[0]["timestamp"]
        end_time = events[-1]["timestamp"] + timedelta(seconds=events[-1]["duration"])
        total_duration = sum(e["duration"] for e in events)
        
        apps = list(set([e["app"] for e in events]))
        
        return {
            "timestamp": start_time,
            "duration": total_duration,
            "type": "communication_session",
            "app": "通讯软件",
            "title": f"使用 {', '.join(apps)}",
            "url": None,
            "category": "communication",
            "sub_events": events,
            "communication_apps": apps,
            "check_count": len(events)
        }
    
    def _extract_iteration_theme(self, titles: List[str]) -> str:
        """Extract main theme from iteration event titles."""
        if not titles:
            return ""
        
        # Look for common keywords
        keywords = ["LaTeX", "论文", "答辩", "PPT", "代码", "编程", "开发",
                   "markdown", "文档", "编辑", "论文", "thesis", "dissertation"]
        
        for keyword in keywords:
            if any(keyword in title for title in titles):
                return f"{keyword} 迭代开发"
        
        # Return the most common meaningful title
        return titles[0][:50] if titles else ""
    
    def _extract_research_topic(self, titles: List[str]) -> str:
        """Extract research topic from browser event titles."""
        if not titles:
            return ""
        
        # Extract meaningful parts from titles
        topics = []
        for title in titles:
            # Remove common suffixes
            clean = re.sub(r'\s*[-–]\s*(?:Google Chrome|Chrome|Firefox|Edge|Safari)$', '', title)
            clean = re.sub(r'\s*[-–]\s*(?:知乎|LINUX DO|CSDN|博客园|简书)$', '', clean)
            if clean and len(clean) > 5:
                topics.append(clean)
        
        # Find common themes
        if topics:
            # Return first meaningful topic
            return topics[0][:60]
        
        return "信息检索"
    
    def extract_learning_topics(self, events: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract learning topics from browser events.
        
        Returns list of topics with title and source.
        """
        topics = []
        seen_keywords = set()
        
        # Keywords that indicate learning/exploration
        learning_indicators = [
            "github.com", "stackoverflow.com", "知乎", "csdn", "博客园",
            "documentation", "docs", "tutorial", "guide", "how to",
            "什么是", "介绍", "入门", "教程", "文档", "原理",
            "对比", "比较", "评测", "推荐", "分享"
        ]
        
        # Filter navigation and search pages
        skip_patterns = [
            r'^新标签页', r'^Google 搜索', r'^百度搜索', r'^必应搜索',
            r'^搜索', r'^home$', r'^index$', r'^about:blank$',
            r'login', r'signin', r'account', r'password'
        ]
        
        for event in events:
            if event.get("category") != "browser":
                continue
            
            title = event.get("title", "")
            url = event.get("url", "")
            domain = event.get("domain", "")
            
            # Skip navigation pages
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    should_skip = True
                    break
            
            if should_skip or not title or len(title) < 5:
                continue
            
            # Extract main topic from title
            # Remove common suffixes
            clean_title = re.sub(r'\s*[-–]\s*(?:Google Chrome|Chrome|Firefox|Edge|Safari|知乎|CSDN)$', '', title)
            clean_title = re.sub(r'\s*[-–]\s*(?:搜索结果|搜索)$', '', clean_title)
            
            # Extract key phrases (technologies, concepts, products)
            # Look for capitalized words, technical terms, etc.
            tech_patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Capitalized phrases
                r'(UI-[A-Z]+)',  # UI-TARS, etc.
                r'([A-Z]{2,})',  # Acronyms like LLM, AI, API
                r'(LaTeX|Overleaf|TeXPage|GitHub|VS Code|Docker|Kubernetes)',
                r'(体制内|公务员|事业编|国企|互联网|AI|人工智能)',
            ]
            
            extracted_topics = []
            for pattern in tech_patterns:
                matches = re.findall(pattern, clean_title)
                for match in matches:
                    if len(match) > 2 and match not in seen_keywords:
                        extracted_topics.append(match)
                        seen_keywords.add(match)
            
            # If no tech terms found, use the first meaningful part of title
            if not extracted_topics and len(clean_title) > 10:
                # Split by common separators and take first meaningful part
                parts = re.split(r'[|·•\-–]', clean_title)
                if parts:
                    first_part = parts[0].strip()
                    if len(first_part) > 5 and len(first_part) < 80:
                        extracted_topics.append(first_part)
            
            # Create topic entry
            for topic in extracted_topics[:2]:  # Max 2 topics per event
                if len(topics) >= 10:  # Limit total topics
                    break
                    
                # Determine source category
                source = "网页"
                if domain:
                    if "github" in domain:
                        source = "GitHub"
                    elif "zhihu" in domain:
                        source = "知乎"
                    elif "linux.do" in domain:
                        source = "LINUX DO"
                    elif "csdn" in domain:
                        source = "CSDN"
                    elif "overleaf" in domain:
                        source = "Overleaf"
                    elif "texpage" in domain:
                        source = "TeXPage"
                    else:
                        source = domain
                
                topics.append({
                    "topic": topic,
                    "source": source,
                    "title": clean_title[:80]
                })
        
        return topics
    
    def calculate_stats(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not events:
            return {}
        
        total_duration = sum(e["duration"] for e in events)
        
        # App statistics
        app_stats = {}
        for event in events:
            app = event["app"]
            duration = event["duration"]
            app_stats[app] = app_stats.get(app, 0) + duration
        
        # Category statistics
        category_stats = {}
        for event in events:
            cat = event.get("category", "other")
            duration = event["duration"]
            category_stats[cat] = category_stats.get(cat, 0) + duration
        
        # Focus periods (continuous work >30 min)
        focus_periods = []
        current_start = events[0]["timestamp"]
        current_duration = events[0]["duration"]
        
        for event in events[1:]:
            gap = (event["timestamp"] - current_start).total_seconds() - current_duration
            if gap < 60:  # Less than 1 minute gap
                current_duration += gap + event["duration"]
            else:
                if current_duration >= 1800:  # 30 minutes
                    focus_periods.append({
                        "start": current_start,
                        "duration": current_duration
                    })
                current_start = event["timestamp"]
                current_duration = event["duration"]
        
        # Check last period
        if current_duration >= 1800:
            focus_periods.append({
                "start": current_start,
                "duration": current_duration
            })
        
        # Switch count
        switch_count = len(events) - 1
        
        return {
            "total_duration": total_duration,
            "total_hours": total_duration / 3600,
            "event_count": len(events),
            "switch_count": switch_count,
            "app_stats": dict(sorted(app_stats.items(), key=lambda x: x[1], reverse=True)),
            "category_stats": dict(sorted(category_stats.items(), key=lambda x: x[1], reverse=True)),
            "focus_periods": focus_periods,
            "focus_period_count": len(focus_periods)
        }