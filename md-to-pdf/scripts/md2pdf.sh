#!/usr/bin/env bash
# Markdown to PDF 转换脚本
# 使用 eisvogel 模板

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_PATH="$SKILL_DIR/templates/eisvogel.latex"

# 显示帮助
show_help() {
    cat << EOF
用法: $(basename "$0") <input.md> [output.pdf] [选项]

将 Markdown 文件转换为 PDF

参数:
  input.md      输入的 Markdown 文件路径
  output.pdf    输出的 PDF 文件路径（可选，默认为 input.pdf）

选项:
  --chinese, -c     启用中文支持（使用 xelatex 和 CJK 字体）
  --no-number, -n   禁用章节编号
  --margin M        设置页边距（默认 2.5cm）
  --help, -h        显示此帮助信息

示例:
  $(basename "$0") doc.md
  $(basename "$0") doc.md output.pdf
  $(basename "$0") 文档.md 文档.pdf --chinese
  $(basename "$0") doc.md --margin 3cm
EOF
}

# 检查依赖
check_dependencies() {
    if ! command -v pandoc &> /dev/null; then
        echo "错误: 未安装 pandoc" >&2
        echo "请安装: sudo apt install pandoc" >&2
        exit 1
    fi
}

# 默认参数
INPUT_FILE=""
OUTPUT_FILE=""
USE_CHINESE=false
USE_NUMBERING=true
MARGIN="2.5cm"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --chinese|-c)
            USE_CHINESE=true
            shift
            ;;
        --no-number|-n)
            USE_NUMBERING=false
            shift
            ;;
        --margin)
            MARGIN="$2"
            shift 2
            ;;
        -*)
            echo "未知选项: $1" >&2
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$INPUT_FILE" ]]; then
                INPUT_FILE="$1"
            elif [[ -z "$OUTPUT_FILE" ]]; then
                OUTPUT_FILE="$1"
            else
                echo "错误: 多余的参数 $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# 验证输入文件
if [[ -z "$INPUT_FILE" ]]; then
    echo "错误: 请指定输入文件" >&2
    show_help
    exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "错误: 文件不存在: $INPUT_FILE" >&2
    exit 1
fi

# 生成输出文件名
if [[ -z "$OUTPUT_FILE" ]]; then
    OUTPUT_FILE="${INPUT_FILE%.md}.pdf"
fi

echo "转换: $INPUT_FILE → $OUTPUT_FILE"

# 构建 pandoc 命令
PANDOC_ARGS=(
    "$INPUT_FILE"
    -o "$OUTPUT_FILE"
    --template "$TEMPLATE_PATH"
    --listings
)

# 添加编号选项
if $USE_NUMBERING; then
    PANDOC_ARGS+=(-N)
fi

# 中文支持
if $USE_CHINESE; then
    echo "使用中文支持..."
    PANDOC_ARGS+=(
        --pdf-engine=xelatex
        -V "CJKmainfont=Noto Sans CJK SC"
        -V "geometry:margin=$MARGIN"
    )
else
    PANDOC_ARGS+=(-V "geometry:margin=$MARGIN")
fi

# 执行转换
if pandoc "${PANDOC_ARGS[@]}"; then
    echo "✓ 成功生成: $OUTPUT_FILE"
else
    echo "✗ 转换失败" >&2
    
    # 提供故障排除建议
    if $USE_CHINESE; then
        echo ""
        echo "提示: 如果提示缺少 xelatex，请运行:"
        echo "  sudo apt install texlive-xetex texlive-lang-chinese texlive-fonts-extra"
    else
        echo ""
        echo "提示: 如果文档包含中文，请添加 --chinese 选项"
    fi
    
    exit 1
fi
