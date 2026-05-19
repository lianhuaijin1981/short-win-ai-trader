"""静态文件服务 & 前端API代理中间件

为前端页面提供:
1. 静态HTML文件服务（优先使用构建后的 dist 目录）
2. API代理转发（解决跨域问题）
3. SPA 前端路由支持（React Router）
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.core.logger import get_logger

logger = get_logger("swat.static_proxy")

router = APIRouter(tags=["Static"])

# 前端构建输出目录（优先）
DIST_DIR = Path(__file__).parent.parent.parent / "dist"
# 前端源码页面目录（备用）
PAGES_DIR = Path(__file__).parent.parent.parent / "src" / "pages"
# SPA 入口文件
SPA_INDEX = DIST_DIR / "index.html"


def setup_static_files(app):
    """配置静态文件服务 — 支持 React SPA"""
    # 优先挂载构建后的 dist 目录
    if DIST_DIR.exists() and SPA_INDEX.exists():
        # 挂载整个 dist 目录为静态文件（包含 assets 和 public 复制的文件）
        # 这样 /logo-icon.png、/hero-bg-pattern.png 等 public 文件可以直接访问
        app.mount("/dist", StaticFiles(directory=str(DIST_DIR)), name="dist")
        
        # 挂载 dist 目录下的 assets 为静态文件
        assets_dir = DIST_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
            logger.info(f"Assets mounted: /assets -> {assets_dir}")
        
        # 挂载 public 目录下的图片资源（logo、背景图等）到根路径
        public_dir = Path(__file__).parent.parent.parent / "public"
        if public_dir.exists():
            app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")
            logger.info(f"Public files mounted: /public -> {public_dir}")
        
        logger.info(f"SPA mode enabled: dist directory found at {DIST_DIR}")
    else:
        # 备用：挂载源码静态文件
        static_dir = Path(__file__).parent.parent.parent / "src"
        if static_dir.exists():
            app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
            logger.info(f"Static files mounted: /static -> {static_dir}")


@router.get("/pages/{page_name}")
async def serve_page(page_name: str):
    """提供前端页面（兼容旧版HTML页面）"""
    # SPA 模式下，所有页面路由由前端处理
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    
    # 备用：HTML 页面模式
    safe_name = os.path.basename(page_name)
    if not safe_name.endswith('.html'):
        safe_name += '.html'
    
    page_path = PAGES_DIR / safe_name
    
    if not page_path.exists():
        return JSONResponse(
            status_code=404,
            content={"detail": f"页面不存在: {safe_name}"}
        )
    
    return FileResponse(str(page_path))


@router.get("/dashboard")
async def dashboard_redirect():
    """仪表盘页面 — SPA 模式返回 index.html"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    
    page_path = PAGES_DIR / "market-dashboard.html"
    if page_path.exists():
        return FileResponse(str(page_path))
    return JSONResponse(
        status_code=404,
        content={"detail": "市场看板页面未找到"}
    )


@router.get("/login")
async def login_redirect():
    """登录页面 — SPA 模式返回 index.html"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    
    page_path = PAGES_DIR / "login.html"
    if page_path.exists():
        return FileResponse(str(page_path))
    return JSONResponse(
        status_code=404,
        content={"detail": "登录页面未找到"}
    )


@router.get("/pages")
async def list_pages():
    """列出所有可用页面"""
    if SPA_INDEX.exists():
        return {
            "code": 200,
            "mode": "SPA",
            "message": "React SPA mode - all routes handled by frontend",
            "routes": ["/", "/sentiment", "/intraday", "/yingyou", "/tactics", "/scoring", "/diagnosis", "/stock/:code"],
        }
    
    if not PAGES_DIR.exists():
        return JSONResponse(
            status_code=404,
            content={"detail": "页面目录不存在"}
        )
    
    pages = []
    for f in PAGES_DIR.glob("*.html"):
        pages.append({
            "name": f.stem,
            "file": f.name,
            "url": f"/pages/{f.name}",
        })
    
    return {
        "code": 200,
        "pages": pages,
        "total": len(pages),
    }


# ── SPA 路由捕获 ──────────────────────────────────────────

# React Router 前端路由列表（需要返回 index.html 让前端处理）
SPA_ROUTES = [
    "/", "/sentiment", "/intraday", "/yingyou", "/tactics",
    "/scoring", "/diagnosis", "/stock",
]


@router.get("/")
async def spa_root():
    """SPA 根路径"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(
        status_code=404,
        content={"detail": "前端未构建，请运行 npm run build"}
    )


@router.get("/sentiment")
async def spa_sentiment():
    """情绪诊断页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


@router.get("/intraday")
async def spa_intraday():
    """盘中监控页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


@router.get("/yingyou")
async def spa_yingyou():
    """鹰眼优选页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


@router.get("/tactics")
async def spa_tactics():
    """战术策略页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


@router.get("/scoring")
async def spa_scoring():
    """评分系统页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


@router.get("/diagnosis")
async def spa_diagnosis():
    """诊断分析页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


@router.get("/stock/{code}")
async def spa_stock(code: str):
    """个股详情页面"""
    if SPA_INDEX.exists():
        return FileResponse(str(SPA_INDEX))
    return JSONResponse(status_code=404, content={"detail": "SPA not built"})


# ── 静态资源根路径访问 ──────────────────────────────────

@router.get("/logo-icon.png")
async def serve_logo():
    """Logo 图标"""
    logo_path = DIST_DIR / "logo-icon.png"
    if logo_path.exists():
        return FileResponse(str(logo_path), media_type="image/png")
    # 备用：public 目录
    public_logo = Path(__file__).parent.parent.parent / "public" / "logo-icon.png"
    if public_logo.exists():
        return FileResponse(str(public_logo), media_type="image/png")
    return JSONResponse(status_code=404, content={"detail": "Logo not found"})


@router.get("/hero-bg-pattern.png")
async def serve_hero_bg():
    """背景图案"""
    bg_path = DIST_DIR / "hero-bg-pattern.png"
    if bg_path.exists():
        return FileResponse(str(bg_path), media_type="image/png")
    # 备用：public 目录
    public_bg = Path(__file__).parent.parent.parent / "public" / "hero-bg-pattern.png"
    if public_bg.exists():
        return FileResponse(str(public_bg), media_type="image/png")
    return JSONResponse(status_code=404, content={"detail": "Background not found"})


@router.get("/empty-state.png")
async def serve_empty_state():
    """空状态图片"""
    img_path = DIST_DIR / "empty-state.png"
    if img_path.exists():
        return FileResponse(str(img_path), media_type="image/png")
    # 备用：public 目录
    public_img = Path(__file__).parent.parent.parent / "public" / "empty-state.png"
    if public_img.exists():
        return FileResponse(str(public_img), media_type="image/png")
    return JSONResponse(status_code=404, content={"detail": "Empty state image not found"})
