#!/bin/bash

# =============================================================================
# Duyou.me 周报自动更新脚本
# 功能：定时更新 AI 前沿情报和 GitHub 开源热点
# 用法：./scripts/auto-update-feeds.sh [选项]
# 选项：
#   --ai-only      仅更新 AI 前沿情报
#   --oss-only     仅更新开源热点
#   --both         同时更新两者（默认）
#   --dry-run      预览模式，不实际提交
#   --help         显示帮助信息
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_DIR="/Users/james/git/duyou.me"
GITHUB_TRENDING_DIR="/Users/james/git/obsidian/MrXie GitHub Trending"
BRIEFINGS_DIR="${GITHUB_TRENDING_DIR}/Outputs/Briefings"
TODAY=$(date +"%Y年%m月%d日")
TODAY_EN=$(date +"%B %d, %Y")
DATE_SHORT=$(date +"%Y-%m-%d")

# 默认选项
UPDATE_AI=false
UPDATE_OSS=false
DRY_RUN=false

# =============================================================================
# 函数定义
# =============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  Duyou.me 周报自动更新系统${NC}"
    echo -e "${BLUE}  日期: ${TODAY}${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_step() {
    echo -e "\n${YELLOW}[步骤 $1]${NC} $2"
    echo -e "$(printf '%.0s-' {1..60})"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --ai-only      仅更新 AI 前沿情报"
    echo "  --oss-only     仅更新开源热点"
    echo "  --both         同时更新两者（默认）"
    echo "  --dry-run      预览模式，不实际提交"
    echo "  --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 更新所有内容"
    echo "  $0 --ai-only          # 仅更新 AI 情报"
    echo "  $0 --oss-only         # 仅更新开源热点"
    echo "  $0 --dry-run          # 预览模式"
    exit 0
}

# 解析命令行参数
parse_args() {
    if [ $# -eq 0 ]; then
        UPDATE_AI=true
        UPDATE_OSS=true
        return
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            --ai-only)
                UPDATE_AI=true
                UPDATE_OSS=false
                shift
                ;;
            --oss-only)
                UPDATE_AI=false
                UPDATE_OSS=true
                shift
                ;;
            --both)
                UPDATE_AI=true
                UPDATE_OSS=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    print_step 1 "检查依赖项"
    
    # 检查目录是否存在
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    if [ ! -d "$GITHUB_TRENDING_DIR" ]; then
        print_error "GitHub Trending 目录不存在: $GITHUB_TRENDING_DIR"
        exit 1
    fi
    
    # 检查 Python 环境
    if [ ! -f "${GITHUB_TRENDING_DIR}/venv/bin/activate" ]; then
        print_error "Python 虚拟环境不存在"
        exit 1
    fi
    
    print_success "所有依赖项检查通过"
}

# 获取最新的简报文件
get_latest_briefing() {
    local latest_file=$(ls -t "${BRIEFINGS_DIR}"/Briefing_*.md 2>/dev/null | head -1)
    
    if [ -z "$latest_file" ]; then
        print_error "未找到简报文件"
        return 1
    fi
    
    echo "$latest_file"
    return 0
}

# 更新 AI 前沿情报
update_ai_feed() {
    print_step 2 "更新 AI 前沿情报"
    
    cd "$PROJECT_DIR"
    
    # 更新日期标记
    print_info "更新日期为: ${TODAY}"
    
    # 更新 WeeklyFeed.astro
    sed -i '' "s/最后更新：.*年.*月.*日/最后更新：${TODAY}/g" src/components/WeeklyFeed.astro
    sed -i '' "s/Last updated: .*/Last updated: ${TODAY_EN}/g" src/components/WeeklyFeed.astro
    
    # 更新 briefings.astro
    sed -i '' "s/最后更新：.*年.*月.*日/最后更新：${TODAY}/g" src/pages/briefings.astro
    sed -i '' "s/Last updated: .*/Last updated: ${TODAY_EN}/g" src/pages/briefings.astro
    
    print_success "AI 前沿情报日期已更新"
    
    if [ "$DRY_RUN" = true ]; then
        print_info "[预览模式] 跳过 Git 提交"
        return
    fi
    
    # 提交更改
    git add src/components/WeeklyFeed.astro src/pages/briefings.astro
    git commit -m "Update AI frontier weekly feed to ${TODAY}" || print_info "无更改需要提交"
}

# 更新开源热点
update_oss_feed() {
    print_step 3 "更新 GitHub 开源热点"
    
    cd "$GITHUB_TRENDING_DIR"
    
    # 运行抓取脚本
    print_info "运行 GitHub Scout 抓取脚本..."
    source venv/bin/activate
    python scripts/scout.py
    deactivate
    
    print_success "GitHub 数据抓取完成"
    
    # 获取最新简报
    LATEST_BRIEFING=$(get_latest_briefing)
    if [ $? -ne 0 ]; then
        print_error "无法获取最新简报"
        return 1
    fi
    
    print_info "最新简报: $(basename $LATEST_BRIEFING)"
    
    cd "$PROJECT_DIR"
    
    # 更新日期标记
    print_info "更新日期为: ${TODAY}"
    
    # 更新 OpenSourceFeed.astro
    sed -i '' "s/最后更新：.*年.*月.*日/最后更新：${TODAY}/g" src/components/OpenSourceFeed.astro
    sed -i '' "s/Last updated: .*/Last updated: ${TODAY_EN}/g" src/components/OpenSourceFeed.astro
    
    # 更新 opensource.astro
    sed -i '' "s/最后更新：.*年.*月.*日/最后更新：${TODAY}/g" src/pages/opensource.astro
    sed -i '' "s/Last updated: .*/Last updated: ${TODAY_EN}/g" src/pages/opensource.astro
    
    print_success "开源热点日期已更新"
    
    if [ "$DRY_RUN" = true ]; then
        print_info "[预览模式] 跳过 Git 提交"
        return
    fi
    
    # 提交更改
    git add src/components/OpenSourceFeed.astro src/pages/opensource.astro
    git commit -m "Update open source weekly feed to ${TODAY}" || print_info "无更改需要提交"
}

# 推送到远程仓库
push_to_remote() {
    if [ "$DRY_RUN" = true ]; then
        print_info "[预览模式] 跳过推送"
        return
    fi
    
    print_step 4 "推送到远程仓库"
    
    cd "$PROJECT_DIR"
    
    git push
    print_success "代码已推送到远程仓库"
    print_info "网站将在几分钟后自动部署"
}

# 生成报告
generate_report() {
    print_step 5 "生成更新报告"
    
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  更新完成报告${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "日期: ${TODAY}"
    echo -e "AI 前沿情报: $([ $UPDATE_AI = true ] && echo '✓ 已更新' || echo '- 跳过')"
    echo -e "开源热点: $([ $UPDATE_OSS = true ] && echo '✓ 已更新' || echo '- 跳过')"
    echo -e "预览模式: $([ $DRY_RUN = true ] && echo '是' || echo '否')"
    echo -e "${GREEN}========================================${NC}\n"
}

# =============================================================================
# 主程序
# =============================================================================

main() {
    parse_args "$@"
    print_header
    
    # 检查依赖
    check_dependencies
    
    # 执行更新
    if [ "$UPDATE_AI" = true ]; then
        update_ai_feed
    fi
    
    if [ "$UPDATE_OSS" = true ]; then
        update_oss_feed
    fi
    
    # 推送更改
    if [ "$UPDATE_AI" = true ] || [ "$UPDATE_OSS" = true ]; then
        push_to_remote
    fi
    
    # 生成报告
    generate_report
    
    print_success "所有任务完成！"
}

# 执行主程序
main "$@"
