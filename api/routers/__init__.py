from api.routers.market import router as market_router
from api.routers.sentiment import router as sentiment_router
from api.routers.intraday import router as intraday_router
from api.routers.yingyou import router as yingyou_router
from api.routers.tactics import router as tactics_router
from api.routers.scoring import router as scoring_router
from api.routers.diagnosis import router as diagnosis_router
from api.routers.stock import router as stock_router
from api.routers.news import router as news_router
from api.routers.trade_journal import router as journal_router

# 用户账号体系路由
from api.routers.auth import router as auth_router
from api.routers.user import router as user_router
from api.routers.membership import router as membership_router
from api.routers.order import router as order_router
from api.routers.admin import router as admin_router
