#!/bin/bash

# =============================================================================
# Duyou.me 周报自动更新 - 快速安装脚本
# 用法：./scripts/setup-auto-update.sh [选项]
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/Users/james/git/duyou.me"

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  Duyou.me 自动更新系统安装向导${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_step() {
    echo -e "\n${YELLOW}[步骤 $1]${NC} $2"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 检查是否在项目目录
check_project_dir() {
    if [ "$(pwd)" != "$PROJECT_DIR" ]; then
        print_error "请在项目根目录运行此脚本"
        print_info "cd $PROJECT_DIR"
        exit 1
    fi
}

# 赋予脚本执行权限
setup_permissions() {
    print_step 1 "设置脚本权限"
    chmod +x scripts/auto-update-feeds.sh
    print_success "脚本权限已设置"
}

# 测试脚本
test_script() {
    print_step 2 "测试脚本（预览模式）"
    ./scripts/auto-update-feeds.sh --dry-run
    print_success "脚本测试通过"
}

# 选择定时方式
choose_scheduler() {
    print_step 3 "选择定时任务方式"
    echo ""
    echo "请选择您喜欢的定时任务方式："
    echo "  1) launchd (推荐 - macOS 原生支持)"
    echo "  2) cron (传统方式)"
    echo "  3) 仅手动执行，不设置定时任务"
    echo ""
    read -p "请输入选项 (1/2/3): " choice
    
    case $choice in
        1)
            setup_launchd
            ;;
        2)
            setup_cron
            ;;
        3)
            print_info "跳过定时任务设置"
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac
}

# 设置 launchd
setup_launchd() {
    print_info "正在配置 launchd..."
    
    # 复制 plist 文件
    cp scripts/com.duyoume.weekly-feed-updater.plist ~/Library/LaunchAgents/
    print_success "配置文件已复制到 ~/Library/LaunchAgents/"
    
    # 加载任务
    launchctl load ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist
    print_success "定时任务已加载"
    
    # 验证
    if launchctl list | grep -q duyoume; then
        print_success "任务已成功启动"
        print_info "下次执行时间：下周一上午 9:00"
    else
        print_error "任务启动失败"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}常用命令：${NC}"
    echo "  查看状态: launchctl list | grep duyoume"
    echo "  立即执行: launchctl start com.duyoume.weekly-feed-updater"
    echo "  停止任务: launchctl unload ~/Library/LaunchAgents/com.duyoume.weekly-feed-updater.plist"
    echo "  查看日志: tail -f /tmp/duyou-feeds-update.log"
}

# 设置 cron
setup_cron() {
    print_info "正在配置 cron..."
    
    echo ""
    echo "请选择更新频率："
    echo "  1) 每周一上午 9:00（推荐）"
    echo "  2) 每天凌晨 2:00"
    echo "  3) 每周三和周日下午 8:00"
    echo ""
    read -p "请输入选项 (1/2/3): " freq_choice
    
    case $freq_choice in
        1)
            CRON_EXPR="0 9 * * 1"
            ;;
        2)
            CRON_EXPR="0 2 * * *"
            ;;
        3)
            CRON_EXPR="0 20 * * 3,0"
            ;;
        *)
            print_error "无效选项"
            exit 1
            ;;
    esac
    
    # 创建临时 crontab 文件
    TEMP_CRON=$(mktemp)
    echo "$CRON_EXPR cd $PROJECT_DIR && ./scripts/auto-update-feeds.sh --both >> /tmp/duyou-feeds-update.log 2>&1" > "$TEMP_CRON"
    
    # 安装 crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    print_success "Cron 任务已安装"
    
    # 验证
    if crontab -l | grep -q auto-update-feeds; then
        print_success "任务已成功启动"
    else
        print_error "任务安装失败"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}常用命令：${NC}"
    echo "  查看任务: crontab -l"
    echo "  编辑任务: crontab -e"
    echo "  删除任务: crontab -r"
    echo "  查看日志: tail -f /tmp/duyou-feeds-update.log"
}

# 显示完成信息
show_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  安装完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "接下来您可以："
    echo ""
    echo "1. 手动执行更新："
    echo "   ./scripts/auto-update-feeds.sh --both"
    echo ""
    echo "2. 查看详细文档："
    echo "   cat scripts/README-AUTO-UPDATE.md"
    echo ""
    echo "3. 监控执行情况："
    echo "   tail -f /tmp/duyou-feeds-update.log"
    echo ""
    echo "4. 访问网站查看效果："
    echo "   open https://duyou.me"
    echo ""
}

# 主程序
main() {
    print_header
    check_project_dir
    setup_permissions
    test_script
    choose_scheduler
    show_completion
    
    print_success "所有设置完成！祝您使用愉快！🎉"
}

main "$@"
