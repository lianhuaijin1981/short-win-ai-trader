@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: 强制切换到项目根目录
cd /d "%~dp0\.."
echo Working directory: %cd%

:: 1. 检查 Python
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ? 错误：未找到 Python，请先安装 Python 3.10+ 并加入环境变量
    pause
    exit /b 1
)
echo Python版本检查通过

:: 2. 创建/激活虚拟环境
echo [2/5] 检查虚拟环境...
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ? 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
)
call venv\Scripts\activate.bat
echo ? 虚拟环境已激活

:: 3. 清理pip缓存并安装依赖
echo [3/5] 安装依赖...
pip cache purge >nul 2>&1
pip install --no-cache-dir -r requirements.txt
if %errorlevel% neq 0 (
    echo ? 依赖安装失败，请检查 requirements.txt
    pause
    exit /b 1
)

:: 4. 启动服务
echo [4/5] 启动演示服务...
echo 访问地址：
echo - API文档：http://127.0.0.1:8000/docs
echo - 市场看板：http://127.0.0.1:8000/market-dashboard.html
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause