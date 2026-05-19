#!/bin/bash
# ═══════════════════════════════════════════════════════
# short-win-ai-trader 本地演示环境一键启动脚本
# Linux/Mac 版本
# ═══════════════════════════════════════════════════════

set -e

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  短线致胜 AI 交易智能体 - 本地演示环境启动"
echo "═══════════════════════════════════════════════════════"
echo ""

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.10+"
    exit 1
fi

echo "[1/5] 检查Python环境..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "[错误] Python版本低于3.10 (当前: $PYTHON_VERSION)，请升级"
    exit 1
fi
echo "  Python版本检查通过 ($PYTHON_VERSION)"

echo "[2/5] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv venv
    echo "  虚拟环境创建成功"
fi

# 激活虚拟环境
source venv/bin/activate

echo "[3/5] 安装依赖..."
pip install -q -r requirements.txt || echo "[警告] 部分依赖安装失败，尝试继续..."

echo "[4/5] 创建必要目录..."
mkdir -p cache logs data

echo "[5/5] 启动服务..."
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  服务启动中，请稍候..."
echo ""
echo "  API 文档: http://127.0.0.1:8000/docs"
echo "  ReDoc:    http://127.0.0.1:8000/redoc"
echo "  健康检查: http://127.0.0.1:8000/health"
echo ""
echo "  前端页面:"
echo "    市场看板: src/pages/market-dashboard.html"
echo "    交易笔记: src/pages/trade-journal.html"
echo "    登录页面: src/pages/login.html"
echo ""
echo "  按 Ctrl+C 停止服务"
echo "═══════════════════════════════════════════════════════"
echo ""

# 设置环境变量
export SWAT_API_HOST=0.0.0.0
export SWAT_API_PORT=8000
export SWAT_API_DEBUG=true
export SWAT_API_IFIND_ENABLED=false

# 启动API服务
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload