#!/usr/bin/env python3
"""
ActivityWatch 数据获取脚本
获取指定日期的活动数据，输出结构化 JSON 供 AI 分析
"""
import sys
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'aw_diary'))

from fetcher import ActivityWatchFetcher
from processor import SmartMerger

def load_config():
    config_paths = [
        Path(__file__).parent.parent / 'config.yaml',
    ]
    for path in config_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
    return {}

def format_duration(seconds):
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

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', '-d', help='日期 (YYYY-MM-DD)')
    parser.add_argument('--today', '-t', action='store_true', help='今天')
    parser.add_argument('--yesterday', '-y', action='store_true', help='昨天')
    args = parser.parse_args()
    
    config = load_config()
    aw_config = config.get('activitywatch', {})
    proc_config = config.get('processing', {})
    timezone_str = proc_config.get('timezone', 'Asia/Shanghai')
    
    fetcher = ActivityWatchFetcher(
        host=aw_config.get('host', 'localhost'),
        port=aw_config.get('port', 5600),
        timezone_str=timezone_str
    )
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")
    elif args.yesterday:
        target_date = datetime.now() - timedelta(days=1)
    else:
        target_date = datetime.now()
    
    data = fetcher.get_date_data(target_date)
    
    processor = SmartMerger(
        merge_gap=proc_config.get('merge_gap', 60),
        min_duration=proc_config.get('min_duration', 30),
        timezone_str=timezone_str
    )
    
    events = processor.process(data)
    stats = processor.calculate_stats(events)
    learning_topics = processor.extract_learning_topics(events)
    
    # Build timeline
    timeline = []
    for e in events:
        event_info = {
            'time': e['timestamp'].strftime('%H:%M'),
            'duration': format_duration(e['duration']),
            'app': e['app'],
            'title': e.get('title', ''),
            'category': e.get('category', 'other')
        }
        if e.get('type') == 'iteration':
            event_info['type'] = 'iteration'
            event_info['switches'] = e.get('iteration_stats', {}).get('total_switches', 0)
        elif e.get('type') == 'research':
            event_info['type'] = 'research'
            event_info['domains'] = e.get('domains', [])
        elif e.get('type') == 'communication_session':
            event_info['type'] = 'communication'
            event_info['apps'] = e.get('communication_apps', [])
        else:
            event_info['type'] = 'normal'
        timeline.append(event_info)
    
    output = {
        'date': target_date.strftime('%Y-%m-%d'),
        'weekday': ['周一','周二','周三','周四','周五','周六','周日'][target_date.weekday()],
        'total_hours': round(stats['total_hours'], 1),
        'event_count': stats['event_count'],
        'switch_count': stats['switch_count'],
        'focus_periods': len(stats['focus_periods']),
        'app_stats': {k: round(v/3600, 1) for k, v in list(stats.get('app_stats', {}).items())[:10]},
        'category_stats': {k: round(v/3600, 1) for k, v in stats.get('category_stats', {}).items()},
        'timeline': timeline,
        'learning_topics': [{'topic': t['topic'], 'source': t['source']} for t in learning_topics]
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
