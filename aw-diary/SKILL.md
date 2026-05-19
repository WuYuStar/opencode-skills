---
name: aw-diary
description: 基于 ActivityWatch 数据生成每日活动轨迹日记，配合 AI 进行生产力分析。用户提到"track my day"、"生成日记"、"ActivityWatch"、"what did I do today"、"帮我写今日总结"、"回顾今天做了什么"、"计算机使用报告"时，都应使用此 skill。即使只是问"我今天效率怎么样"或"帮我看看我昨天干了什么"，也需要调用此 skill 获取精确的 ActivityWatch 活动数据。

compatibility: 需要 Python 3.8+、requests 库，以及可访问的 ActivityWatch 服务器。支持 ActivityWatch v0.12+，需要 window watcher、AFK watcher，可选 web watcher。
---

# ActivityWatch 每日轨迹日记 (aw-diary)

从 ActivityWatch 追踪数据生成 insightful 的每日日记，配合 AI 驱动的生产力分析。

## 快速开始

当用户要求生成日记时，按以下步骤操作：

### 第 1 步：获取并处理数据

```bash
cd ~/.agents/skills/aw-diary
python3 scripts/fetch_data.py --today        # 今天
python3 scripts/fetch_data.py --yesterday    # 昨天
python3 scripts/fetch_data.py --date 2024-01-15  # 指定日期
```

输出结构化 JSON，包含：
- `date`、`weekday`、`total_hours`、`event_count`、`switch_count`
- `app_stats`（应用使用时间）
- `category_stats`（开发、浏览器、通讯等分类）
- `timeline`（处理后的事件，类型包括 iteration/research/communication）
- `learning_topics`（从浏览器标题中提取）

### 第 2 步：使用 AI 生成日记

基于 JSON 数据，按以下格式生成完整日记。使用 `prompts/diary_system_prompt.md` 中的系统提示模板作为风格参考。

### 第 3 步：写入 Obsidian

将生成的日记写入：
```
$VAULT/Daily Notes/轨迹日记-YYYY-MM-DD.md
```

## 日记输出格式

日记必须使用 Obsidian Callouts，结构如下：

```markdown
---
date: 'YYYY-MM-DD'
total_active_time: Xh Xm
focus_score: X.X
top_apps:
- 'app: Xh Xm'
event_count: N
switch_count: N
focus_periods: N
tags:
- 轨迹日记
- activitywatch
- auto-generated
---

# 轨迹日记 - YYYY年MM月DD日（周X）

## 今日概览

> [!summary] 今日概览
> - **总活跃**: X.Xh | **Focus**: X.X/10 | **模式**: 🔄 [模式名]
> - **主项目**: [项目1] (Xh) + [项目2] (Xh)
> - **一句话**: [AI生成的一句话总结]

[2-3段整体描述]

---

## 三关键发现

> [!important] 三关键发现
> 1. 🎯 [最重要的成就/发现]
> 2. ⚠️ [需要注意的问题]
> 3. 💡 [改进建议]

---

## 今日所学

> [!info] 今日所学
> 📚 **[主题1]**：[一句话描述]
> 📚 **[主题2]**：[一句话描述]
> ...

---

## 工作模式识别

> [!tip] 今日工作模式：[模式名]
> 
> [模式分析]

---

## 项目追踪

| 项目 | 时长 | 占比 | 主要工具 |
|------|------|------|----------|
| 🎓 项目1 | Xh | XX% | 工具列表 |

---

## 效率分析

> [!important] Focus Score: X.X/10
> 
> [评分理由]

### 时间分配

| 类别 | 时长 | 占比 | 评价 |
|------|------|------|------|
| 开发工作 | Xh | XX% | ... |

---

## 建议与反馈

> [!tip] 建议 N：[建议标题]
> [建议内容]

> [!quote] 今日亮点
> 🌟 [正面反馈]

---

## 详细时间线

> [!info]- 🕐 详细时间线（点击展开）
>
> [按时间段描述活动，使用效率标记 ⭐/⚡/🔄]
```

## 关键风格规则

1. **时区**：所有时间使用 Asia/Shanghai (UTC+8)
2. **Callouts**：使用 `[!summary]`、`[!important]`、`[!tip]`、`[!info]`、`[!quote]`、`[!warning]`
3. **折叠**：使用 `[!info]-`（带 `-`）实现可折叠区域
4. **表情符号**：⭐（深度专注）、⚡（快速切换）、🔄（被打断）、📊（正常）
5. **语言**：中文
6. **语气**：友好、专业、数据驱动的教练风格
7. **合并**：将连续相似的活动分组（编码-预览迭代）
8. **学习内容**：从浏览器标题中提取知识主题

## 配置

编辑 `config.yaml`：

```yaml
activitywatch:
  host: "172.18.208.1"
  port: 5600
obsidian:
  vault_path: "/home/wuyu/obsidian-vault"
  daily_notes_dir: "Daily Notes"
  filename_template: "轨迹日记-{date}.md"
processing:
  merge_gap: 60
  min_duration: 30
  timezone: "Asia/Shanghai"
analysis:
  depth: "medium"
  language: "zh"
```

## 故障排查

- **连接失败**：检查 ActivityWatch 是否正在运行，以及配置中的 host/port 是否正确
- **无数据**：确保目标日期 ActivityWatch 已正常运行
- **日记为空**：检查 window watcher 和 AFK watcher 是否已启用
