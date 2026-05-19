---
name: obsidian-cli-wsl
description: 通过 Obsidian CLI 与本地 Obsidian 交互。用于读写笔记、搜索内容、管理任务和属性、插件开发调试等。在 WSL 环境中需要通过 powershell.exe 调用 Obsidian CLI。当用户提到 Obsidian、笔记、知识库、vault 等时使用。
---

# Obsidian CLI (WSL 环境)

## 环境说明

- **操作系统**：WSL2 (Windows Subsystem for Linux)
- **Obsidian 运行位置**：Windows
- **调用方式**：`powershell.exe -Command "obsidian <命令>"`
- **前置条件**：Obsidian 必须正在运行，且已在设置中启用 CLI

## Vault 路径配置

### 检测与配置

**先检查** `$VAULT` 是否已设置：
```bash
echo $VAULT  # 已配置则直接使用
```

**未找到则询问用户**：
> "未检测到 Vault 路径，请提供完整路径（如 `~/obsidian-vault/知识库名`）"

**配置命令**（获得路径后执行）：
```bash
ln -s "用户提供的绝对路径" ~/obsidian-vault
echo 'export VAULT="$HOME/obsidian-vault"' >> ~/.bashrc && source ~/.bashrc
```

### 两种访问方式

| 方式 | 命令示例 | 适用场景 |
|------|----------|----------|
| **Obsidian CLI** | `powershell.exe -Command "obsidian read file='笔记'"` | 需实时响应、链接更新、插件触发 |
| **直接文件访问** | `cat $VAULT/目录/笔记.md` | 批量读写、脚本处理、无需 Obsidian 在线 |

**使用策略**：批量读写/搜索/生成文件用 `$VAULT`；创建日记、管理任务、查看反向链接用 CLI。

### 文件操作示例

```bash
cat $VAULT/笔记.md                              # 读取
cat > $VAULT/新笔记.md << 'EOF'
---
date: 2026-05-10
---
内容
EOF
echo "- [ ] 任务" >> $VAULT/待办.md              # 追加
grep -r "关键词" $VAULT/                         # 搜索
cp/mv/rm $VAULT/文件                            # 复制/移动/删除
```

**注意**：直接修改不触发 Obsidian 实时功能（链接更新、图谱刷新），建议批量操作时关闭 Obsidian。

## WSL 配置要求

**必须启用 WSL interop**，否则无法调用 Windows 程序。检查 `/etc/wsl.conf`：

```ini
[interop]
enabled = true
```

修改后需重启 WSL：

```bash
# 在 Windows PowerShell 中执行
wsl --shutdown
```

如果未启用 interop，会出现错误：`cannot execute binary file: Exec format error`

## 命令格式

在 WSL 中，所有 Obsidian CLI 命令需通过 PowerShell 调用：

```bash
powershell.exe -Command "obsidian <命令> [参数]"
```

**参数**使用 `=` 赋值，含空格的字符串用引号包裹：

```bash
powershell.exe -Command "obsidian create name='My Note' content='Hello world'"
```

**Flags**（布尔开关）不需要赋值，直接写名称：

```bash
powershell.exe -Command "obsidian create name='My Note' silent overwrite"
```

多行内容使用 `\n` 表示换行，`\t` 表示制表符。

## 文件定位

多数命令接受 `file` 或 `path` 来指定目标文件：

- `file=<名称>` — 通过名称解析（类似维基链接，不需要路径或扩展名）
- `path=<路径>` — 从知识库根目录开始的精确路径，如 `folder/note.md`

如果不指定，默认对当前活动文件操作。

## 知识库定位

命令默认针对最近获得焦点的知识库。使用 `vault=<名称>` 作为第一个参数来指定：

```bash
powershell.exe -Command "obsidian vault='My Vault' search query='test'"
```

## 常用命令

### 笔记操作

```bash
# 读取笔记
powershell.exe -Command "obsidian read file='My Note'"

# 创建笔记
powershell.exe -Command "obsidian create name='New Note' content='# Hello' template='Template' silent"

# 追加内容
powershell.exe -Command "obsidian append file='My Note' content='New line'"

# 比较版本
powershell.exe -Command "obsidian diff file=README from=1 to=3"
```

### 搜索

```bash
# 搜索知识库
powershell.exe -Command "obsidian search query='search term' limit=10"

# 查看未解析的链接
powershell.exe -Command "obsidian unresolved"

# 查看反向链接
powershell.exe -Command "obsidian backlinks file='My Note'"
```

### 日记

```bash
# 打开今日日记
powershell.exe -Command "obsidian daily"

# 读取今日日记
powershell.exe -Command "obsidian daily:read"

# 追加任务到日记
powershell.exe -Command "obsidian daily:append content='- [ ] New task'"
```

### 属性和任务

```bash
# 设置属性
powershell.exe -Command "obsidian property:set name='status' value='done' file='My Note'"

# 查看日记任务
powershell.exe -Command "obsidian tasks daily todo"
```

### 标签

```bash
# 查看所有标签（按使用次数排序）
powershell.exe -Command "obsidian tags sort=count counts"
```

## 快捷选项

- `--copy`：将输出复制到剪贴板
- `silent`：执行后不在 Obsidian 中打开文件
- `total`：在列表命令中返回数量

## 插件开发

### 开发/测试循环

1. **重载插件**以应用修改：
   ```bash
   powershell.exe -Command "obsidian plugin:reload id=my-plugin"
   ```

2. **检查错误**：
   ```bash
   powershell.exe -Command "obsidian dev:errors"
   ```

3. **截图或检查 DOM**：
   ```bash
   powershell.exe -Command "obsidian dev:screenshot path=screenshot.png"
   powershell.exe -Command "obsidian dev:dom selector='.workspace-leaf' text"
   ```

4. **查看控制台输出**：
   ```bash
   powershell.exe -Command "obsidian dev:console level=error"
   ```

### 其他开发者命令

在应用上下文中运行 JavaScript：

```bash
powershell.exe -Command "obsidian eval code='app.vault.getFiles().length'"
```

**重要：eval 命令中的引号处理**

当 JavaScript 代码需要包含字符串引号时（如文件路径），Windows 命令行解析器会自动去掉双引号，导致 JavaScript 语法错误。此时应使用**单引号**作为 JS 字符串引号，并通过 bash 的引号拼接语法 `\'"'\'` 来传递：

```bash
# 错误：直接使用双引号会被 Windows 去掉
powershell.exe -Command "obsidian eval code='app.vault.getAbstractFileByPath(\"test.md\")'"
# 结果：test is not defined

# 正确：使用单引号 + bash 引号拼接
powershell.exe -Command 'obsidian eval code="app.vault.delete(app.vault.getAbstractFileByPath('"'"'test.md'"'"'))"'
# 结果：成功执行
```

通用模板（将 `FILENAME` 替换为实际文件名）：
```bash
powershell.exe -Command 'obsidian eval code="app.vault.delete(app.vault.getAbstractFileByPath('"'"'FILENAME'"'"'))"'
```

检查 CSS 值：

```bash
powershell.exe -Command "obsidian dev:css selector='.workspace-leaf' prop=background-color"
```

切换移动端模拟：

```bash
powershell.exe -Command "obsidian dev:mobile on"
```

## 注意事项

- 如果 `powershell.exe` 未找到，说明 WSL interop 未启用，需检查 `/etc/wsl.conf` 中 `[interop] enabled = true`
- 当 Obsidian 未运行时，CLI 命令会失败
- 多行内容通过 `\n` 传递时需注意转义

## 参考

- 完整文档：https://help.obsidian.md/cli
- 在 WSL 中运行 Windows 程序：https://wsl.dev/technical-documentation/interop/
