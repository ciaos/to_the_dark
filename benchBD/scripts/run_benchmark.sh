#!/bin/bash
# 财务管报压测自动化脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查pip包
    python3 -c "import psycopg2, pandas" 2>/dev/null || {
        log_warning "缺少必要的Python包，正在安装..."
        pip3 install psycopg2-binary pandas
    }
    
    log_success "依赖检查完成"
}

# 生成测试数据
generate_data() {
    log_info "生成测试数据..."
    
    cd /home/chaos/benchBD/data
    python3 generate_test_data.py
    
    if [ $? -eq 0 ]; then
        log_success "测试数据生成完成"
    else
        log_error "测试数据生成失败"
        exit 1
    fi
}

# 创建配置文件
create_config() {
    log_info "创建配置文件..."
    
    cd /home/chaos/benchBD/scripts
    python3 benchmark.py --create-config
    
    log_warning "请编辑 config.json 文件，填入正确的数据库连接信息"
    log_info "配置文件位置: /home/chaos/benchBD/config.json"
}

# 运行压测
run_benchmark() {
    log_info "开始运行压测..."
    
    if [ ! -f "/home/chaos/benchBD/config.json" ]; then
        log_error "配置文件不存在，请先运行: $0 setup"
        exit 1
    fi
    
    cd /home/chaos/benchBD/scripts
    python3 benchmark.py ../config.json
    
    if [ $? -eq 0 ]; then
        log_success "压测完成"
    else
        log_error "压测失败"
        exit 1
    fi
}

# 清理数据
cleanup() {
    log_info "清理测试数据..."
    
    rm -f /home/chaos/benchBD/data/*.csv
    rm -f /home/chaos/benchBD/results/*.json
    
    log_success "清理完成"
}

# 显示帮助
show_help() {
    echo "财务管报压测工具"
    echo ""
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  setup      - 初始化环境（检查依赖、生成数据、创建配置）"
    echo "  generate   - 生成测试数据"
    echo "  config     - 创建配置文件"
    echo "  run        - 运行压测"
    echo "  cleanup    - 清理测试数据"
    echo "  help       - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 setup    # 首次使用"
    echo "  $0 run      # 运行压测"
    echo "  $0 cleanup  # 清理数据"
}

# 主函数
main() {
    case "${1:-help}" in
        "setup")
            check_dependencies
            generate_data
            create_config
            log_success "环境初始化完成！"
            log_info "下一步: 编辑配置文件后运行 '$0 run'"
            ;;
        "generate")
            check_dependencies
            generate_data
            ;;
        "config")
            create_config
            ;;
        "run")
            run_benchmark
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
