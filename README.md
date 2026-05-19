# OpenCode Skills 仓库

这是一个 AI Agent 技能集合仓库，包含多种专用能力模块，可与 OpenCode 等 AI 编程助手配合使用。

## 技能列表

### 文档与办公

| 技能 | 说明 |
|------|------|
| **docx** | Word 文档创建与编辑，支持格式化、目录、页眉页脚、修订追踪 |
| **pptx** | PowerPoint 演示文稿处理，支持创建、编辑、提取内容 |
| **xlsx** | Excel 表格处理（.xlsx/.csv/.tsv），支持读写、公式、图表、数据清洗 |
| **pdf-skill** | PDF 全面处理（读取、合并、拆分、转换、加密、表单填写） |
| **md2pdf** | Markdown 转 PDF，支持多种模板和中文排版 |
| **ppt-master** | AI 驱动的多格式 PPT 生成系统 |

### Obsidian 生态

| 技能 | 说明 |
|------|------|
| **obsidian-markdown** | Obsidian 风味 Markdown 语法（wikilinks、callouts、properties 等） |
| **obsidian-cli-wsl** | 通过 CLI 与本地 Obsidian 交互（读写笔记、搜索、任务管理） |
| **obsidian-bases** | Obsidian Bases 数据库视图（表格、卡片、筛选、公式） |
| **json-canvas** | JSON Canvas 文件创建编辑（思维导图、流程图） |

### 网络与搜索

| 技能 | 说明 |
|------|------|
| **smart-search** | 多引擎智能搜索（DDGS、Tavily、Brave Search），自动路由 |
| **agent-browser** | 浏览器自动化（导航、点击、填表、截图、测试） |

### AI 与生产力

| 技能 | 说明 |
|------|------|
| **aw-diary** | ActivityWatch 每日活动轨迹日记与生产力分析 |
| **sixdim-prompt** | 六维框架提示词生成工具 |
| **memos-skill** | Memos 笔记系统管理 |
| **paddleocr-text-recognition** | OCR 文字识别（图片和 PDF） |

### Skill 开发与管理

| 技能 | 说明 |
|------|------|
| **skill-creator** | 创建、优化和评估新技能 |
| **find-skills** | 发现并安装社区技能 |

## 使用方法

将本仓库克隆到 OpenCode 的 skills 目录：

```bash
git clone git@github.com:WuYuStar/opencode-skills.git ~/.agents/skills
```

每个技能目录包含 `SKILL.md` 文件，详细说明该技能的用途、触发条件和具体用法。

## 仓库地址

- **GitHub**: https://github.com/WuYuStar/opencode-skills

## 许可证

各技能遵循其各自的许可证条款，详见各目录下的 LICENSE 文件。
