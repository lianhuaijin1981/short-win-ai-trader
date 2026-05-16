"""测试: 模块七交割单诊断"""

import pytest
from datetime import datetime

from short_win_ai_trader.modules.m07_trade_diagnosis.importer import TradeImporter
from short_win_ai_trader.modules.m07_trade_diagnosis.attribution import TradeAttribution
from short_win_ai_trader.modules.m07_trade_diagnosis.profiler import TradeProfiler
from short_win_ai_trader.modules.m07_trade_diagnosis.error_library import ErrorLibrary
from short_win_ai_trader.modules.m07_trade_diagnosis.custom_analyzer import CustomAnalyzer
from short_win_ai_trader.data_platform.data_models import TradeRecord


class TestTradeImporter:
    """交割单导入测试"""

    @pytest.fixture
    def importer(self):
        return TradeImporter()

    def test_manual_entry(self, importer):
        """测试手动录入"""
        record = importer.manual_entry(
            ticker="600519",
            stock_name="贵州茅台",
            trade_date="2026-05-10",
            trade_type="买入",
            price=1800.0,
            volume=100,
            trade_mode="打板",
            profit_loss=5000.0,
        )
        assert record.ticker == "600519.SH"
        assert record.stock_name == "贵州茅台"
        assert record.trade_type == "买入"
        assert record.profit_loss == 5000.0

    def test_auto_detect_mode(self, importer):
        """测试交易模式自动识别"""
        mode = importer._auto_detect_mode(100.0, 20000, 2000000)
        assert mode == "打板"


class TestTradeAttribution:
    """交易归因测试"""

    @pytest.fixture
    def attribution(self):
        return TradeAttribution()

    @pytest.fixture
    def win_trade(self):
        return TradeRecord(
            trade_id="T001",
            ticker="600519.SH",
            stock_name="贵州茅台",
            trade_date=datetime(2026, 5, 10),
            trade_type="买入",
            price=1800.0,
            volume=100,
            amount=180000.0,
            trade_mode="打板",
            profit_loss=5000.0,
            profit_loss_pct=2.78,
        )

    @pytest.fixture
    def loss_trade(self):
        return TradeRecord(
            trade_id="T002",
            ticker="000001.SZ",
            stock_name="平安银行",
            trade_date=datetime(2026, 5, 10),
            trade_type="买入",
            price=12.0,
            volume=1000,
            amount=12000.0,
            trade_mode="低吸",
            profit_loss=-800.0,
            profit_loss_pct=-6.67,
        )

    def test_analyze_profit(self, attribution, win_trade):
        """测试盈利归因"""
        factors = attribution.analyze_profit(win_trade, {"emotion_cycle": "发酵期"})
        assert len(factors) > 0
        assert any("行情" in f for f in factors)

    def test_analyze_loss(self, attribution, loss_trade):
        """测试亏损溯源"""
        result = attribution.analyze_loss(loss_trade, {"emotion_cycle": "退潮期"})
        assert result["error_type"] is not None
        assert len(result["reasons"]) > 0

    def test_diagnose_win(self, attribution, win_trade):
        """测试盈利交易诊断"""
        diagnosis = attribution.diagnose(win_trade)
        assert diagnosis.is_profitable is True
        assert len(diagnosis.success_factors) > 0

    def test_diagnose_loss(self, attribution, loss_trade):
        """测试亏损交易诊断"""
        diagnosis = attribution.diagnose(loss_trade)
        assert diagnosis.is_profitable is False
        assert diagnosis.error_type is not None


class TestTradeProfiler:
    """交易画像测试"""

    @pytest.fixture
    def profiler(self):
        return TradeProfiler()

    @pytest.fixture
    def sample_trades(self):
        trades = []
        for i in range(10):
            trades.append(TradeRecord(
                trade_id=f"T{i:03d}",
                ticker=f"600{i:03d}.SH",
                stock_name=f"股票{i}",
                trade_date=datetime(2026, 5, 1 + i),
                trade_type="买入",
                price=100.0 + i,
                volume=100,
                amount=(100.0 + i) * 100,
                trade_mode="打板" if i % 2 == 0 else "低吸",
                profit_loss=2000.0 if i % 3 != 0 else -1500.0,
                profit_loss_pct=2.0 if i % 3 != 0 else -1.5,
            ))
        return trades

    def test_generate_profile(self, profiler, sample_trades):
        """测试画像生成"""
        profile = profiler.generate_profile(sample_trades)
        assert profile.total_trades == 10
        assert 0 <= profile.win_rate <= 100
        assert profile.style != ""

    def test_detect_style(self, profiler, sample_trades):
        """测试风格判定"""
        style = profiler._detect_style(sample_trades)
        assert style in ["龙头接力型", "分歧低吸型", "趋势波段型", "事件催化套利型", "综合型", "未定型"]


class TestErrorLibrary:
    """错题库测试"""

    def test_add_and_find(self, tmp_path):
        """测试添加和查找"""
        lib = ErrorLibrary(library_path=str(tmp_path / "errors.json"))
        lib.add_entry({
            "error_type": "标的选择错误",
            "ticker": "600519.SH",
            "loss_amount": -2000,
            "loss_pct": -5.5,
            "key_tags": ["高位", "无板块联动"],
        })
        assert lib.get_summary()["total"] == 1

    def test_similar_alerts(self, tmp_path):
        """测试相似预警"""
        lib = ErrorLibrary(library_path=str(tmp_path / "errors.json"))
        lib.add_entry({
            "error_type": "宏观行情错误",
            "emotion_cycle": "退潮期",
            "trade_mode": "打板",
            "key_tags": ["退潮", "追高"],
        })
        alerts = lib.find_similar_alerts("600519.SH", {
            "emotion_cycle": "退潮期",
            "trade_mode": "打板",
            "tags": ["退潮"],
        })
        assert len(alerts) > 0


class TestCustomAnalyzer:
    """自定义标的分析测试"""

    @pytest.fixture
    def analyzer(self):
        return CustomAnalyzer()

    def test_analyze(self, analyzer):
        """测试全维度研判"""
        modules_data = {
            "emotion": {"current_cycle": "发酵期", "theme_position": "主升加速"},
            "watch": {"anchor_position": "主线分支龙头"},
            "yingyou": {"top_match": {"name": "炒股养家", "score": 92}},
            "tactics": {"matched_tactics": ["三倍量突破战法", "筹码峰战法"]},
            "scoring": {
                "total_score": 85.5,
                "rating": "优质标的",
                "is_high_position": True,
                "chip_risk": True,
                "dimension_scores": [
                    {"dimension": "技术形态强度", "score": 90},
                    {"dimension": "市场情绪适配", "score": 88},
                    {"dimension": "基本面安全垫", "score": 45},
                ],
            },
            "trade_plan": None,
        }

        result = analyzer.analyze("603083.SH", "剑桥科技", modules_data, "龙头接力型")
        assert result.ticker == "603083.SH"
        assert result.comprehensive_score == 85.5
        assert len(result.success_logic) > 0
        assert len(result.risk_points) > 0
        assert result.style_advice != ""
