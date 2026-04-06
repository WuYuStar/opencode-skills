#!/usr/bin/env bash
# md2pdf Skill Setup Script
# 环境检查和安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  md2pdf Skill 环境检查工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python 版本
check_python() {
    echo -e "${BLUE}[1/5] 检查 Python 版本...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}✗ 未找到 Python${NC}"
        echo "请安装 Python 3.10 或更高版本"
        return 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION (符合要求 >= 3.10)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Python $PYTHON_VERSION (建议升级到 >= 3.10)${NC}"
        return 0
    fi
}

# 检查 md2pdf
check_md2pdf() {
    echo -e "${BLUE}[2/5] 检查 md2pdf CLI...${NC}"
    
    if command -v md2pdf &> /dev/null; then
        MD2PDF_VERSION=$(md2pdf --version 2>&1 | head -1)
        echo -e "${GREEN}✓ md2pdf 已安装: $MD2PDF_VERSION${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ md2pdf 未安装${NC}"
        echo "正在安装 md2pdf..."
        
        if pip install "md2pdf[cli]" --break-system-packages 2>/dev/null || \
           pip3 install "md2pdf[cli]" --break-system-packages 2>/dev/null || \
           pip install "md2pdf[cli]" --user 2>/dev/null || \
           pip3 install "md2pdf[cli]" --user 2>/dev/null; then
            echo -e "${GREEN}✓ md2pdf 安装成功${NC}"
            return 0
        else
            echo -e "${RED}✗ md2pdf 安装失败${NC}"
            echo "请手动安装: pip install 'md2pdf[cli]'"
            return 1
        fi
    fi
}

# 检查 WeasyPrint 依赖
check_weasyprint() {
    echo -e "${BLUE}[3/5] 检查 WeasyPrint 依赖...${NC}"
    
    if python3 -c "import weasyprint" 2>/dev/null || \
       python -c "import weasyprint" 2>/dev/null; then
        echo -e "${GREEN}✓ WeasyPrint 已安装${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ WeasyPrint 未安装或导入失败${NC}"
        echo "尝试安装 WeasyPrint..."
        
        if pip install weasyprint --break-system-packages 2>/dev/null || \
           pip3 install weasyprint --break-system-packages 2>/dev/null; then
            echo -e "${GREEN}✓ WeasyPrint 安装成功${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ WeasyPrint 安装可能失败${NC}"
            echo "md2pdf 可能会自动安装依赖"
            return 0
        fi
    fi
}

# 检查中文字体
check_chinese_fonts() {
    echo -e "${BLUE}[4/5] 检查中文字体...${NC}"
    
    FONTS_FOUND=""
    FONTS_MISSING=""
    
    # 检查各种中文字体
    if fc-list :lang=zh 2>/dev/null | grep -qi "noto.*cjk"; then
        FONTS_FOUND="${FONTS_FOUND}Noto CJK, "
    else
        FONTS_MISSING="${FONTS_MISSING}Noto CJK (noto-fonts-cjk), "
    fi
    
    if fc-list :lang=zh 2>/dev/null | grep -qi "source.*han"; then
        FONTS_FOUND="${FONTS_FOUND}Source Han, "
    else
        FONTS_MISSING="${FONTS_MISSING}Source Han (fonts-adobe-source-han-sans), "
    fi
    
    if fc-list :lang=zh 2>/dev/null | grep -qi "wenquanyi"; then
        FONTS_FOUND="${FONTS_FOUND}WenQuanYi, "
    else
        FONTS_MISSING="${FONTS_MISSING}WenQuanYi (fonts-wqy-microhei), "
    fi
    
    if fc-list :lang=zh 2>/dev/null | grep -qi "microsoft.*yahei\|msyh\|simhei\|simsun"; then
        FONTS_FOUND="${FONTS_FOUND}Windows 中文字体, "
    fi
    
    if [ -n "$FONTS_FOUND" ]; then
        echo -e "${GREEN}✓ 发现中文字体: ${FONTS_FOUND%, }${NC}"
    fi
    
    if [ -n "$FONTS_MISSING" ]; then
        echo -e "${YELLOW}⚠ 建议安装的中文字体: ${FONTS_MISSING%, }${NC}"
        echo ""
        echo "安装命令:"
        echo "  Ubuntu/Debian:"
        echo "    sudo apt install fonts-noto-cjk fonts-wqy-microhei"
        echo "  macOS:"
        echo "    brew install font-noto-sans-cjk"
        echo "  或手动下载: https://www.google.com/get/noto/"
    fi
    
    # 显示可用中文字体列表
    echo ""
    echo -e "${BLUE}系统中可用的中文字体 (前10个):${NC}"
    fc-list :lang=zh | head -10 | while read font; do
        echo "  - $font"
    done
    
    return 0
}

# 检查其他依赖
check_dependencies() {
    echo -e "${BLUE}[5/5] 检查其他依赖...${NC}"
    
    # 检查 markdown 扩展
    echo "检查可选依赖..."
    
    if python3 -c "import markdown" 2>/dev/null || python -c "import markdown" 2>/dev/null; then
        echo -e "${GREEN}✓ markdown 模块可用${NC}"
    else
        echo -e "${YELLOW}⚠ markdown 模块可能未安装${NC}"
    fi
    
    if python3 -c "import pymdownx" 2>/dev/null || python -c "import pymdownx" 2>/dev/null; then
        echo -e "${GREEN}✓ pymdownx 扩展可用 (支持表情符号等)${NC}"
    else
        echo -e "${YELLOW}⚠ pymdownx 扩展未安装 (可选)${NC}"
        echo "  安装: pip install pymdown-extensions"
    fi
    
    return 0
}

# 显示模板信息
show_templates() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  可用模板${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    if [ -d "$SKILL_DIR/templates" ]; then
        echo "模板位置: $SKILL_DIR/templates"
        echo ""
        for template in "$SKILL_DIR/templates"/*.css; do
            if [ -f "$template" ]; then
                basename "$template"
            fi
        done
    else
        echo -e "${YELLOW}⚠ 模板目录未找到${NC}"
    fi
}

# 显示使用帮助
show_usage() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  快速使用指南${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "基础转换:"
    echo "  md2pdf -i document.md"
    echo ""
    echo "使用模板:"
    echo "  md2pdf --css $SKILL_DIR/templates/chinese-modern.css -i document.md"
    echo ""
    echo "批量转换:"
    echo "  python3 $SCRIPT_DIR/batch_convert.py '*.md'"
    echo ""
    echo "查看帮助:"
    echo "  md2pdf --help"
}

# 主函数
main() {
    local HAS_ERROR=0
    
    check_python || HAS_ERROR=1
    check_md2pdf || HAS_ERROR=1
    check_weasyprint || true  # 非致命错误
    check_chinese_fonts || true  # 非致命错误
    check_dependencies || true  # 非致命错误
    
    show_templates
    
    if [ $HAS_ERROR -eq 0 ]; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  环境检查通过！${NC}"
        echo -e "${GREEN}========================================${NC}"
        show_usage
        exit 0
    else
        echo ""
        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}  环境检查完成，但有警告/错误${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo ""
        echo "请根据上述提示修复问题后重试。"
        exit 1
    fi
}

# 运行主函数
main "$@"
