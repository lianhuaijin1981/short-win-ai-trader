/**
 * 游资诊股模块 - 前端展示层
 * 
 * 功能：
 * 1. 20个内置游资 + 用户自定义（新增/编辑/删除）
 * 2. 游资列表动态排序（按当日匹配分）
 * 3. 游资深度分析卡片
 * 4. 实时行情状态显示
 * 5. 多游资综合推荐Top3
 */

import { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactEChartsCore from 'echarts-for-react';
import {
  TrendingUp,
  Target,
  Award,
  AlertTriangle,
  Zap,
  Users,
  ShieldAlert,
  Plus,
  Edit,
  Trash2,
  X,
  Check,
  BarChart3,
  Activity,
} from 'lucide-react';
import DataCard from '@/components/DataCard';
import { cn } from '@/lib/utils';
import {
  BUILT_IN_HOT_MONEY,
  calculateAllMatchScores,
  calculateStockProbability,
  getSentimentPhaseColor,
  getMarketFitLabel,
  getStyleTagColor,
  createCustomHotMoney,
} from '@/data/hotMoneyData';
import type {
  HotMoneyTrader,
  MarketState,
  StyleTag,
  SentimentPhase,
  CustomHotMoneyFormData,
} from '@/data/hotMoneyData';

// ═══════════════════════════════════════════════════════════════
// 本地存储管理
// ═══════════════════════════════════════════════════════════════

const STORAGE_KEY = 'custom_hot_money';

function loadCustomTraders(): HotMoneyTrader[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

function saveCustomTraders(traders: HotMoneyTrader[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(traders));
  } catch {
    // ignore
  }
}

// ═══════════════════════════════════════════════════════════════
// 模拟行情状态（实际应从API获取）
// ═══════════════════════════════════════════════════════════════

const MOCK_MARKET_STATES: MarketState[] = [
  {
    date: new Date().toISOString().split('T')[0],
    sentimentPhase: '分歧',
    sentimentScore: 5,
    mainLineStrength: 6,
    mainLineType: '单一主线',
    maxConsecutive: 5,
    consecutiveCount: 8,
    totalVolume: 17000,
    volumeStatus: '平量',
    preferredMarketCap: '小盘',
    earlySealCount: 15,
    firstBoardCount: 35,
    consecutiveBoardCount: 12,
  },
  {
    date: new Date().toISOString().split('T')[0],
    sentimentPhase: '冰点',
    sentimentScore: 2,
    mainLineStrength: 3,
    mainLineType: '无主线',
    maxConsecutive: 3,
    consecutiveCount: 4,
    totalVolume: 14000,
    volumeStatus: '缩量',
    preferredMarketCap: '小盘',
    earlySealCount: 8,
    firstBoardCount: 20,
    consecutiveBoardCount: 5,
  },
  {
    date: new Date().toISOString().split('T')[0],
    sentimentPhase: '高潮',
    sentimentScore: 9,
    mainLineStrength: 9,
    mainLineType: '单一主线',
    maxConsecutive: 7,
    consecutiveCount: 25,
    totalVolume: 22000,
    volumeStatus: '放量',
    preferredMarketCap: '中盘',
    earlySealCount: 30,
    firstBoardCount: 50,
    consecutiveBoardCount: 30,
  },
];

// ═══════════════════════════════════════════════════════════════
// 模拟股票推荐数据
// ═══════════════════════════════════════════════════════════════

const MOCK_STOCKS = [
  { code: '002196', name: '方正电机', marketCap: 45, volRatio: 3.33, consecutive: 1, position: '低位' as const, sector: '新能源汽车', sealTime: '09:35', changePercent: 10.03, currentPrice: 15.36 },
  { code: '001333', name: '光华股份', marketCap: 52, volRatio: 2.62, consecutive: 1, position: '低位' as const, sector: '化工新材料', sealTime: '09:42', changePercent: 10.01, currentPrice: 26.05 },
  { code: '002031', name: '巨轮智能', marketCap: 88, volRatio: 1.08, consecutive: 1, position: '中位' as const, sector: '机器人', sealTime: '10:15', changePercent: 9.95, currentPrice: 8.4 },
  { code: '001259', name: '利仁科技', marketCap: 38, volRatio: 1.37, consecutive: 5, position: '高位' as const, sector: '消费电子', sealTime: '09:25', changePercent: 10.0, currentPrice: 60.5 },
  { code: '002066', name: '瑞泰科技', marketCap: 55, volRatio: 2.0, consecutive: 1, position: '低位' as const, sector: '建材', sealTime: '09:50', changePercent: 10.0, currentPrice: 26.06 },
  { code: '002181', name: '粤传媒', marketCap: 62, volRatio: 1.09, consecutive: 1, position: '中位' as const, sector: '文化传媒', sealTime: '10:20', changePercent: 10.0, currentPrice: 19.69 },
  { code: '002348', name: '高乐股份', marketCap: 35, volRatio: 1.29, consecutive: 1, position: '低位' as const, sector: '玩具', sealTime: '09:55', changePercent: 10.02, currentPrice: 13.72 },
  { code: '002374', name: '中锐股份', marketCap: 28, volRatio: 1.21, consecutive: 1, position: '低位' as const, sector: '包装印刷', sealTime: '10:05', changePercent: 9.91, currentPrice: 3.55 },
  { code: '002395', name: '双象股份', marketCap: 48, volRatio: 1.55, consecutive: 1, position: '中位' as const, sector: '化工', sealTime: '10:10', changePercent: 10.02, currentPrice: 21.19 },
  { code: '002407', name: '多氟多', marketCap: 180, volRatio: 1.6, consecutive: 1, position: '中位' as const, sector: '氟化工', sealTime: '10:25', changePercent: 10.02, currentPrice: 36.47 },
];

// ═══════════════════════════════════════════════════════════════
// 工具组件
// ═══════════════════════════════════════════════════════════════

function ScoreRing({ percent, size = 48 }: { percent: number; size?: number }) {
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  const color = percent >= 80 ? '#22c55e' : percent >= 60 ? '#c9a84c' : percent >= 40 ? '#f59e0b' : '#ef4444';

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#141e33" strokeWidth={strokeWidth} />
        <motion.circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute text-[10px] font-mono font-semibold" style={{ color }}>{percent}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: '强适配' | '弱适配' | '回避' | '中性' }) {
  const colors = {
    '强适配': 'bg-[rgba(34,197,94,0.15)] text-[#22c55e] border-[rgba(34,197,94,0.3)]',
    '弱适配': 'bg-[rgba(245,158,11,0.15)] text-[#f59e0b] border-[rgba(245,158,11,0.3)]',
    '回避': 'bg-[rgba(239,68,68,0.15)] text-[#ef4444] border-[rgba(239,68,68,0.3)]',
    '中性': 'bg-[rgba(107,114,128,0.15)] text-[#6b7280] border-[rgba(107,114,128,0.3)]',
  };
  return (
    <span className={cn('text-[10px] px-1.5 py-0.5 rounded-full border', colors[status])}>
      {status}
    </span>
  );
}

// ═══════════════════════════════════════════════════════════════
// 添加/编辑游资表单
// ═══════════════════════════════════════════════════════════════

const ALL_STYLE_TAGS: StyleTag[] = ['首板', '连板', '趋势', '低吸', '打板', '大票', '小票', '情绪', '主线', '套利', '龙头', '补涨', '反包', '做T', '隔日', '高标', '全能'];
const ALL_SENTIMENT_PHASES: SentimentPhase[] = ['冰点', '分歧', '修复', '高潮', '退潮', '混沌'];

interface TraderFormProps {
  initialData?: CustomHotMoneyFormData;
  onSubmit: (data: CustomHotMoneyFormData) => void;
  onCancel: () => void;
}

function TraderForm({ initialData, onSubmit, onCancel }: TraderFormProps) {
  const [name, setName] = useState(initialData?.name || '');
  const [alias, setAlias] = useState(initialData?.alias || '');
  const [seats, setSeats] = useState(initialData?.seats || '');
  const [capitalScale, setCapitalScale] = useState(initialData?.capitalScale || '5-15亿');
  const [styleTags, setStyleTags] = useState<StyleTag[]>(initialData?.styleTags || []);
  const [philosophy, setPhilosophy] = useState(initialData?.philosophy || '');
  const [operationMode, setOperationMode] = useState(initialData?.operationMode || '');
  const [riskControl, setRiskControl] = useState(initialData?.riskControl || '');
  const [typicalFeatures, setTypicalFeatures] = useState(initialData?.typicalFeatures || '');
  const [boardPref, setBoardPref] = useState(initialData?.boardPref || '首板');
  const [marketCapMin, setMarketCapMin] = useState(initialData?.marketCapMin || 20);
  const [marketCapMax, setMarketCapMax] = useState(initialData?.marketCapMax || 100);
  const [marketCapPreferred, setMarketCapPreferred] = useState<'小盘' | '中盘' | '大盘' | '全能'>(initialData?.marketCapPreferred || '小盘');
  const [minVolRatio, setMinVolRatio] = useState(initialData?.minVolRatio || 2);
  const [preferEarly, setPreferEarly] = useState(initialData?.preferEarly ?? true);
  const [preferLow, setPreferLow] = useState(initialData?.preferLow ?? true);
  const [maxDistanceFromHigh, setMaxDistanceFromHigh] = useState(initialData?.maxDistanceFromHigh || 15);
  const [strongSentiment, setStrongSentiment] = useState<SentimentPhase[]>(initialData?.strongSentiment || ['冰点', '分歧']);
  const [weakSentiment, setWeakSentiment] = useState<SentimentPhase[]>(initialData?.weakSentiment || ['修复']);
  const [avoidSentiment, setAvoidSentiment] = useState<SentimentPhase[]>(initialData?.avoidSentiment || ['高潮', '退潮']);
  const [preferredSectors, setPreferredSectors] = useState(initialData?.preferredSectors || '');

  const toggleStyleTag = (tag: StyleTag) => {
    setStyleTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]);
  };

  const toggleSentiment = (phase: SentimentPhase, list: SentimentPhase[], setter: (v: SentimentPhase[]) => void) => {
    setter(list.includes(phase) ? list.filter(p => p !== phase) : [...list, phase]);
  };

  const handleSubmit = () => {
    if (!name.trim()) return;
    onSubmit({
      name, alias, seats, capitalScale, styleTags, philosophy, operationMode, riskControl, typicalFeatures,
      boardPref, marketCapMin, marketCapMax, marketCapPreferred, minVolRatio, preferEarly, preferLow,
      maxDistanceFromHigh, strongSentiment, weakSentiment, avoidSentiment, preferredSectors,
    });
  };

  return (
    <div className="space-y-3">
      <div className="text-[14px] font-medium text-[#c9a84c] mb-2">{initialData ? '编辑游资' : '添加新游资'}</div>
      
      {/* 基础信息 */}
      <div className="grid grid-cols-2 gap-2">
        <input value={name} onChange={e => setName(e.target.value)} placeholder="游资名称 *" className="input-dark" />
        <input value={alias} onChange={e => setAlias(e.target.value)} placeholder="别名/绰号" className="input-dark" />
      </div>
      <input value={seats} onChange={e => setSeats(e.target.value)} placeholder="席位列表（逗号分隔）" className="input-dark" />
      <div className="grid grid-cols-2 gap-2">
        <input value={capitalScale} onChange={e => setCapitalScale(e.target.value)} placeholder="资金体量（如5-15亿）" className="input-dark" />
        <input value={preferredSectors} onChange={e => setPreferredSectors(e.target.value)} placeholder="偏好板块（逗号分隔）" className="input-dark" />
      </div>

      {/* 风格标签 */}
      <div>
        <div className="text-[11px] text-[#94a3b8] mb-1">风格标签（多选）</div>
        <div className="flex flex-wrap gap-1.5">
          {ALL_STYLE_TAGS.map(tag => (
            <button
              key={tag}
              onClick={() => toggleStyleTag(tag)}
              className={cn(
                'text-[10px] px-2 py-1 rounded-full border transition-all',
                styleTags.includes(tag)
                  ? 'border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.15)]'
                  : 'border-[rgba(148,163,184,0.15)] text-[#475569] hover:text-[#94a3b8]'
              )}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* 模式参数 */}
      <div className="p-2 rounded-lg bg-[#0f1929] border border-[rgba(148,163,184,0.1)] space-y-2">
        <div className="text-[11px] text-[#c9a84c] font-medium">模式参数</div>
        <div className="grid grid-cols-3 gap-2">
          <select value={boardPref} onChange={e => setBoardPref(e.target.value)} className="input-dark">
            <option value="首板">首板</option>
            <option value="二板">二板</option>
            <option value="连板">连板</option>
            <option value="趋势板">趋势板</option>
          </select>
          <input type="number" value={marketCapMin} onChange={e => setMarketCapMin(Number(e.target.value))} placeholder="最小市值(亿)" className="input-dark" />
          <input type="number" value={marketCapMax} onChange={e => setMarketCapMax(Number(e.target.value))} placeholder="最大市值(亿)" className="input-dark" />
        </div>
        <div className="grid grid-cols-3 gap-2">
          <select value={marketCapPreferred} onChange={e => setMarketCapPreferred(e.target.value as any)} className="input-dark">
            <option value="小盘">小盘</option>
            <option value="中盘">中盘</option>
            <option value="大盘">大盘</option>
            <option value="全能">全能</option>
          </select>
          <input type="number" step="0.5" value={minVolRatio} onChange={e => setMinVolRatio(Number(e.target.value))} placeholder="最小量比" className="input-dark" />
          <input type="number" value={maxDistanceFromHigh} onChange={e => setMaxDistanceFromHigh(Number(e.target.value))} placeholder="距前高%" className="input-dark" />
        </div>
        <div className="flex gap-4">
          <label className="flex items-center gap-1.5 text-[11px] text-[#94a3b8] cursor-pointer">
            <input type="checkbox" checked={preferEarly} onChange={e => setPreferEarly(e.target.checked)} className="accent-[#c9a84c]" />
            偏好早板
          </label>
          <label className="flex items-center gap-1.5 text-[11px] text-[#94a3b8] cursor-pointer">
            <input type="checkbox" checked={preferLow} onChange={e => setPreferLow(e.target.checked)} className="accent-[#c9a84c]" />
            偏好低位
          </label>
        </div>
      </div>

      {/* 情绪适配 */}
      <div className="p-2 rounded-lg bg-[#0f1929] border border-[rgba(148,163,184,0.1)] space-y-2">
        <div className="text-[11px] text-[#c9a84c] font-medium">情绪适配</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#22c55e] w-12">强适配</span>
            <div className="flex flex-wrap gap-1">
              {ALL_SENTIMENT_PHASES.map(p => (
                <button key={p} onClick={() => toggleSentiment(p, strongSentiment, setStrongSentiment)}
                  className={cn('text-[9px] px-1.5 py-0.5 rounded border', strongSentiment.includes(p) ? 'border-[#22c55e] text-[#22c55e] bg-[rgba(34,197,94,0.15)]' : 'border-[rgba(148,163,184,0.1)] text-[#475569]')}>{p}</button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#f59e0b] w-12">弱适配</span>
            <div className="flex flex-wrap gap-1">
              {ALL_SENTIMENT_PHASES.map(p => (
                <button key={p} onClick={() => toggleSentiment(p, weakSentiment, setWeakSentiment)}
                  className={cn('text-[9px] px-1.5 py-0.5 rounded border', weakSentiment.includes(p) ? 'border-[#f59e0b] text-[#f59e0b] bg-[rgba(245,158,11,0.15)]' : 'border-[rgba(148,163,184,0.1)] text-[#475569]')}>{p}</button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#ef4444] w-12">回避</span>
            <div className="flex flex-wrap gap-1">
              {ALL_SENTIMENT_PHASES.map(p => (
                <button key={p} onClick={() => toggleSentiment(p, avoidSentiment, setAvoidSentiment)}
                  className={cn('text-[9px] px-1.5 py-0.5 rounded border', avoidSentiment.includes(p) ? 'border-[#ef4444] text-[#ef4444] bg-[rgba(239,68,68,0.15)]' : 'border-[rgba(148,163,184,0.1)] text-[#475569]')}>{p}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 文本字段 */}
      <textarea value={philosophy} onChange={e => setPhilosophy(e.target.value)} placeholder="核心交易理念（一句话）" rows={2} className="input-dark resize-none" />
      <textarea value={operationMode} onChange={e => setOperationMode(e.target.value)} placeholder="操作要点（分号分隔）" rows={2} className="input-dark resize-none" />
      <textarea value={riskControl} onChange={e => setRiskControl(e.target.value)} placeholder="风控纪律（分号分隔）" rows={2} className="input-dark resize-none" />
      <input value={typicalFeatures} onChange={e => setTypicalFeatures(e.target.value)} placeholder="典型特征" className="input-dark" />

      {/* 按钮 */}
      <div className="flex gap-2 pt-2">
        <button onClick={handleSubmit} className="flex items-center gap-1 bg-[#c9a84c] text-[#060b14] px-4 py-2 rounded text-[12px] font-medium hover:bg-[#d4b76a] transition-colors">
          <Check size={14} />{initialData ? '保存' : '确认添加'}
        </button>
        <button onClick={onCancel} className="bg-[#141e33] text-[#94a3b8] px-4 py-2 rounded text-[12px] hover:text-[#f1f5f9] transition-colors">
          取消
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// 游资深度卡片
// ═══════════════════════════════════════════════════════════════

function TraderDeepCard({ trader, marketState }: { trader: HotMoneyTrader; marketState: MarketState }) {
  const { base, mode } = trader;
  const fitLabel = getMarketFitLabel(mode.sentimentAdapt, marketState.sentimentPhase);
  
  const radarOption = useMemo(() => ({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item' as const },
    radar: {
      indicator: ['情绪适配', '板型适配', '市值适配', '量能适配', '位置适配', '胜率', '收益', '回撤控制'].map(name => ({ name, max: 100 })),
      center: ['50%', '50%'],
      radius: '65%',
      axisName: { color: '#94a3b8', fontSize: 10 },
      splitArea: { areaStyle: { color: ['transparent'] } },
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.15)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: trader.radarData || [70, 60, 55, 65, 60, 58, 62, 60],
        name: base.name,
        areaStyle: { color: 'rgba(201,168,76,0.2)' },
        lineStyle: { color: '#c9a84c', width: 2 },
        itemStyle: { color: '#c9a84c' },
      }],
    }],
  }), [trader, base.name]);

  return (
    <div className="space-y-4">
      {/* 头部 */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-[24px] font-semibold text-[#c9a84c]">{base.name}</h2>
            {base.isCustom && <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#3b82f6] text-white">自定义</span>}
          </div>
          {base.alias && <p className="text-[12px] text-[#94a3b8] mt-0.5">{base.alias}</p>}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={fitLabel.label as any} />
          <span className="text-[10px] text-[#94a3b8]">当前: {marketState.sentimentPhase}</span>
        </div>
      </div>

      {/* 风格标签 */}
      <div className="flex flex-wrap gap-1.5">
        {base.styleTags.map(tag => (
          <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full border" style={{ borderColor: getStyleTagColor(tag), color: getStyleTagColor(tag), backgroundColor: getStyleTagColor(tag) + '15' }}>
            {tag}
          </span>
        ))}
      </div>

      {/* 核心交易理念 */}
      <div className="relative bg-[#141e33] rounded-lg p-3 pl-4">
        <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-[#c9a84c] rounded-l-lg" />
        <p className="text-[13px] text-[#f1f5f9] italic leading-relaxed">"{mode.philosophy.soul}"</p>
      </div>

      {/* 核心交易模式（可量化规则） */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-2 rounded-lg bg-[#141e33]">
          <div className="text-[10px] text-[#475569] mb-1">板型偏好</div>
          <div className="text-[13px] text-[#f1f5f9]">{mode.boardPref.primary}{mode.boardPref.secondary ? ` / ${mode.boardPref.secondary}` : ''}</div>
        </div>
        <div className="p-2 rounded-lg bg-[#141e33]">
          <div className="text-[10px] text-[#475569] mb-1">市值偏好</div>
          <div className="text-[13px] text-[#f1f5f9]">{mode.marketCapPref.min}-{mode.marketCapPref.max}亿 ({mode.marketCapPref.preferred})</div>
        </div>
        <div className="p-2 rounded-lg bg-[#141e33]">
          <div className="text-[10px] text-[#475569] mb-1">量能要求</div>
          <div className="text-[13px] text-[#f1f5f9]">量比≥{mode.volumeReq.minVolRatio}{mode.volumeReq.preferExplosive ? ' 偏好爆量' : ''}</div>
        </div>
        <div className="p-2 rounded-lg bg-[#141e33]">
          <div className="text-[10px] text-[#475569] mb-1">封板时间</div>
          <div className="text-[13px] text-[#f1f5f9]">{mode.sealTimePref.preferEarly ? `偏好早板${mode.sealTimePref.latestTime ? ` (${mode.sealTimePref.latestTime}前)` : ''}` : '不限'}</div>
        </div>
      </div>

      {/* 情绪适配 */}
      <div className="p-2 rounded-lg bg-[#0f1929] border border-[rgba(148,163,184,0.1)]">
        <div className="text-[11px] text-[#94a3b8] mb-2">情绪周期适配</div>
        <div className="flex flex-wrap gap-2">
          {ALL_SENTIMENT_PHASES.map(phase => {
            const label = getMarketFitLabel(mode.sentimentAdapt, phase);
            return (
              <div key={phase} className="flex items-center gap-1">
                <span className="text-[10px] text-[#94a3b8]">{phase}</span>
                <StatusBadge status={label.label as any} />
              </div>
            );
          })}
        </div>
      </div>

      {/* 操作要点 */}
      {mode.operationKeys.length > 0 && (
        <div>
          <div className="text-[10px] text-[#475569] font-medium mb-1.5">操作要点</div>
          {mode.operationKeys.map((op, i) => (
            <div key={i} className="flex items-start gap-1.5 text-[11px] text-[#94a3b8] leading-relaxed mb-1">
              <span className="text-[#c9a84c] shrink-0">•</span>
              <span><strong className="text-[#f1f5f9]">{op.title}：</strong>{op.description}</span>
            </div>
          ))}
        </div>
      )}

      {/* 风控 */}
      {mode.riskControl.length > 0 && (
        <div>
          <div className="text-[10px] text-[#475569] font-medium mb-1.5">风控纪律</div>
          {mode.riskControl.map((rule, i) => (
            <div key={i} className="flex items-start gap-1.5 text-[11px] text-[#94a3b8] leading-relaxed mb-1">
              <ShieldAlert size={12} className="text-[#ef4444] shrink-0 mt-0.5" />
              <span>{rule}</span>
            </div>
          ))}
        </div>
      )}

      {/* 偏好板块 */}
      <div className="flex flex-wrap gap-1.5">
        {mode.sectorPref.sectors.map(s => (
          <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-[rgba(20,30,51,0.8)] text-[#06d7d7] border border-[rgba(6,215,215,0.2)]">{s}</span>
        ))}
      </div>

      {/* 典型特征 */}
      <div className="text-[11px] text-[#06d7d7] leading-relaxed italic">{mode.typicalFeatures}</div>

      {/* 雷达图 */}
      <div className="relative">
        <ReactEChartsCore option={radarOption} style={{ height: 280 }} notMerge={true} />
      </div>

      {/* 统计数据 */}
      <div className="grid grid-cols-4 gap-2">
        <div className="text-center p-2 rounded-lg bg-[#141e33]">
          <div className="text-[16px] font-mono font-semibold text-[#ef4444]">{base.winRate}%</div>
          <div className="text-[10px] text-[#94a3b8]">胜率</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-[#141e33]">
          <div className="text-[16px] font-mono font-semibold text-[#22c55e]">+{base.monthlyReturn}%</div>
          <div className="text-[10px] text-[#94a3b8]">月收益</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-[#141e33]">
          <div className="text-[16px] font-mono font-semibold text-[#f59e0b]">{base.maxDrawdown}%</div>
          <div className="text-[10px] text-[#94a3b8]">最大回撤</div>
        </div>
        <div className="text-center p-2 rounded-lg bg-[#141e33]">
          <div className="text-[16px] font-mono font-semibold text-[#3b82f6]">{base.capitalScale}</div>
          <div className="text-[10px] text-[#94a3b8]">资金体量</div>
        </div>
      </div>

      {/* 席位 */}
      <div>
        <div className="text-[10px] text-[#475569] mb-1">知名席位</div>
        <div className="flex flex-wrap gap-1">
          {base.seats.map(seat => (
            <span key={seat} className="text-[10px] px-1.5 py-0.5 rounded border border-[rgba(201,168,76,0.3)] text-[#c9a84c] bg-[rgba(201,168,76,0.08)]">{seat}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// 主页面
// ═══════════════════════════════════════════════════════════════

export default function Yingyou() {
  // 数据状态
  const [customTraders, setCustomTraders] = useState<HotMoneyTrader[]>(loadCustomTraders);
  const [marketStateIndex, setMarketStateIndex] = useState(0);
  const marketState = MOCK_MARKET_STATES[marketStateIndex];
  
  // UI状态
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingTrader, setEditingTrader] = useState<HotMoneyTrader | null>(null);
  const [selectedId, setSelectedId] = useState<string>('');
  const [showDeepCard, setShowDeepCard] = useState(false);

  // 合并所有游资
  const allTraders = useMemo(() => {
    const builtIn = BUILT_IN_HOT_MONEY.map(t => ({ ...t }));
    return [...builtIn, ...customTraders];
  }, [customTraders]);

  // 计算匹配分并排序
  const sortedTraders = useMemo(() => {
    const scores = calculateAllMatchScores(allTraders, marketState);
    const scoreMap = new Map(scores.map(s => [s.traderId, s.totalScore]));
    return [...allTraders].sort((a, b) => (scoreMap.get(b.base.id) || 0) - (scoreMap.get(a.base.id) || 0));
  }, [allTraders, marketState]);

  // 设置默认选中
  useState(() => {
    if (!selectedId && sortedTraders.length > 0) {
      setSelectedId(sortedTraders[0].base.id);
    }
  });

  const selectedTrader = useMemo(() => sortedTraders.find(t => t.base.id === selectedId), [sortedTraders, selectedId]);

  // 计算每只股票的游资参与概率
  const stockProbabilities = useMemo(() => {
    return MOCK_STOCKS.map(stock => 
      calculateStockProbability(stock, allTraders, marketState)
    ).sort((a, b) => b.totalScore - a.totalScore).slice(0, 3);
  }, [allTraders, marketState]);

  // 添加游资
  const handleAddTrader = useCallback((data: CustomHotMoneyFormData) => {
    const id = 'custom_' + Date.now();
    const newTrader = createCustomHotMoney(data, id);
    const updated = [...customTraders, newTrader];
    setCustomTraders(updated);
    saveCustomTraders(updated);
    setShowAddForm(false);
  }, [customTraders]);

  // 编辑游资
  const handleEditTrader = useCallback((data: CustomHotMoneyFormData) => {
    if (!editingTrader) return;
    const updated = customTraders.map(t => {
      if (t.base.id === editingTrader.base.id) {
        return createCustomHotMoney(data, t.base.id);
      }
      return t;
    });
    setCustomTraders(updated);
    saveCustomTraders(updated);
    setEditingTrader(null);
  }, [customTraders, editingTrader]);

  // 删除游资
  const handleDeleteTrader = useCallback((id: string) => {
    const updated = customTraders.filter(t => t.base.id !== id);
    setCustomTraders(updated);
    saveCustomTraders(updated);
    if (selectedId === id) setSelectedId(sortedTraders[0]?.base.id || '');
  }, [customTraders, selectedId, sortedTraders]);

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[32px] font-bold text-[#f1f5f9] leading-tight">游资诊股</h1>
          <p className="text-[#94a3b8] text-[14px] mt-1">20位主流游资模式匹配与实时推荐系统</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0d1526] rounded-lg border border-[rgba(148,163,184,0.1)]">
            <Users size={16} className="text-[#c9a84c]" />
            <span className="text-[12px] text-[#94a3b8]">{allTraders.length}位游资监测中</span>
          </div>
        </div>
      </div>

      {/* 行情状态栏 */}
      <DataCard delay={100} header={
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-[#c9a84c]" />
            <h2 className="text-[14px] font-medium text-[#f1f5f9]">当日行情状态</h2>
          </div>
          <div className="flex gap-1">
            {MOCK_MARKET_STATES.map((state, i) => (
              <button
                key={i}
                onClick={() => setMarketStateIndex(i)}
                className={cn(
                  'text-[10px] px-2 py-1 rounded border transition-all',
                  marketStateIndex === i
                    ? 'border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.15)]'
                    : 'border-[rgba(148,163,184,0.1)] text-[#475569] hover:text-[#94a3b8]'
                )}
              >
                {state.sentimentPhase}
              </button>
            ))}
          </div>
        </div>
      }>
        <div className="grid grid-cols-5 gap-3">
          <div className="text-center p-2 rounded-lg bg-[#141e33]">
            <div className="text-[10px] text-[#94a3b8] mb-1">情绪周期</div>
            <div className="text-[16px] font-semibold" style={{ color: getSentimentPhaseColor(marketState.sentimentPhase) }}>
              {marketState.sentimentPhase}
            </div>
            <div className="text-[11px] text-[#94a3b8]">{marketState.sentimentScore}/10</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#141e33]">
            <div className="text-[10px] text-[#94a3b8] mb-1">主线强度</div>
            <div className="text-[16px] font-semibold text-[#c9a84c]">{marketState.mainLineStrength}/10</div>
            <div className="text-[11px] text-[#94a3b8]">{marketState.mainLineType}</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#141e33]">
            <div className="text-[10px] text-[#94a3b8] mb-1">连板高度</div>
            <div className="text-[16px] font-semibold text-[#ef4444]">{marketState.maxConsecutive}板</div>
            <div className="text-[11px] text-[#94a3b8]">{marketState.consecutiveCount}家</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#141e33]">
            <div className="text-[10px] text-[#94a3b8] mb-1">量能环境</div>
            <div className="text-[16px] font-semibold text-[#22c55e]">{(marketState.totalVolume / 10000).toFixed(1)}万亿</div>
            <div className="text-[11px] text-[#94a3b8]">{marketState.volumeStatus}</div>
          </div>
          <div className="text-center p-2 rounded-lg bg-[#141e33]">
            <div className="text-[10px] text-[#94a3b8] mb-1">市值偏好</div>
            <div className="text-[16px] font-semibold text-[#3b82f6]">{marketState.preferredMarketCap}</div>
            <div className="text-[11px] text-[#94a3b8]">首板{marketState.firstBoardCount}家</div>
          </div>
        </div>
      </DataCard>

      {/* 游资动态排序列表 */}
      <DataCard delay={200} header={
        <div className="flex items-center justify-between">
          <h2 className="text-[14px] font-medium text-[#f1f5f9]">游资适配排行（按当日匹配分排序）</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className={cn(
              'flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full border transition-all',
              showAddForm ? 'border-[#ef4444] text-[#ef4444] bg-[rgba(239,68,68,0.1)]' : 'border-[#c9a84c] text-[#c9a84c] bg-[rgba(201,168,76,0.1)] hover:bg-[rgba(201,168,76,0.2)]'
            )}
          >
            <Plus size={12} />{showAddForm ? '取消' : '添加游资'}
          </button>
        </div>
      }>
        {/* 添加表单 */}
        <AnimatePresence>
          {showAddForm && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-4 p-3 rounded-lg bg-[#0f1929] border border-[rgba(201,168,76,0.2)]">
              <TraderForm onSubmit={handleAddTrader} onCancel={() => setShowAddForm(false)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* 编辑表单 */}
        <AnimatePresence>
          {editingTrader && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-4 p-3 rounded-lg bg-[#0f1929] border border-[rgba(59,130,246,0.2)]">
              <TraderForm
                initialData={{
                  name: editingTrader.base.name,
                  alias: editingTrader.base.alias,
                  seats: editingTrader.base.seats.join(', '),
                  capitalScale: editingTrader.base.capitalScale,
                  styleTags: editingTrader.base.styleTags,
                  philosophy: editingTrader.mode.philosophy.soul,
                  operationMode: editingTrader.mode.operationKeys.map(o => o.description).join('；'),
                  riskControl: editingTrader.mode.riskControl.join('；'),
                  typicalFeatures: editingTrader.mode.typicalFeatures,
                  boardPref: editingTrader.mode.boardPref.primary,
                  marketCapMin: editingTrader.mode.marketCapPref.min,
                  marketCapMax: editingTrader.mode.marketCapPref.max,
                  marketCapPreferred: editingTrader.mode.marketCapPref.preferred,
                  minVolRatio: editingTrader.mode.volumeReq.minVolRatio,
                  preferEarly: editingTrader.mode.sealTimePref.preferEarly,
                  preferLow: editingTrader.mode.positionPref.preferLow,
                  maxDistanceFromHigh: editingTrader.mode.positionPref.maxDistanceFromHigh,
                  strongSentiment: editingTrader.mode.sentimentAdapt.strong,
                  weakSentiment: editingTrader.mode.sentimentAdapt.weak,
                  avoidSentiment: editingTrader.mode.sentimentAdapt.avoid,
                  preferredSectors: editingTrader.mode.sectorPref.sectors.join(', '),
                }}
                onSubmit={handleEditTrader}
                onCancel={() => setEditingTrader(null)}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* 游资列表 */}
        <div className="grid grid-cols-5 gap-2">
          {sortedTraders.map((trader, i) => {
            const score = calculateAllMatchScores([trader], marketState)[0];
            const fitLabel = getMarketFitLabel(trader.mode.sentimentAdapt, marketState.sentimentPhase);
            return (
              <motion.button
                key={trader.base.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                onClick={() => { setSelectedId(trader.base.id); setShowDeepCard(true); }}
                className={cn(
                  'relative rounded-lg border p-2.5 text-left transition-all hover:-translate-y-[2px]',
                  selectedId === trader.base.id
                    ? 'bg-[#141e33] border-[#c9a84c] shadow-[0_0_15px_rgba(201,168,76,0.1)]'
                    : 'bg-transparent border-[rgba(148,163,184,0.1)] hover:bg-[#141e33] hover:border-[rgba(201,168,76,0.3)]'
                )}
              >
                {/* 排名 */}
                <div className="absolute -top-1.5 -left-1.5 w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold"
                  style={{ backgroundColor: i < 3 ? '#c9a84c' : '#141e33', color: i < 3 ? '#060b14' : '#94a3b8', border: '1px solid rgba(148,163,184,0.2)' }}>
                  {i + 1}
                </div>
                
                {/* 自定义/编辑/删除按钮 */}
                {trader.base.isCustom && (
                  <div className="absolute top-1 right-1 flex gap-0.5">
                    <button onClick={e => { e.stopPropagation(); setEditingTrader(trader); }} className="w-4 h-4 rounded bg-[rgba(59,130,246,0.2)] text-[#3b82f6] flex items-center justify-center hover:bg-[rgba(59,130,246,0.3)]">
                      <Edit size={8} />
                    </button>
                    <button onClick={e => { e.stopPropagation(); handleDeleteTrader(trader.base.id); }} className="w-4 h-4 rounded bg-[rgba(239,68,68,0.2)] text-[#ef4444] flex items-center justify-center hover:bg-[rgba(239,68,68,0.3)]">
                      <Trash2 size={8} />
                    </button>
                  </div>
                )}

                <div className="flex items-center gap-1.5 mb-1.5 mt-1">
                  <div className="w-7 h-7 rounded-full bg-[#141e33] border border-[rgba(201,168,76,0.3)] flex items-center justify-center text-[10px] text-[#c9a84c] font-bold">
                    {trader.base.avatar}
                  </div>
                  <div>
                    <div className="text-[12px] font-medium text-[#f1f5f9]">{trader.base.name}</div>
                    <div className="text-[9px] text-[#475569]">{trader.base.alias}</div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-[#94a3b8]">匹配分</span>
                  <span className="text-[14px] font-mono font-bold" style={{ color: score.totalScore >= 80 ? '#22c55e' : score.totalScore >= 60 ? '#c9a84c' : '#f59e0b' }}>
                    {score.totalScore}
                  </span>
                </div>
                
                {/* 匹配条 */}
                <div className="w-full h-1.5 bg-[#141e33] rounded-full overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${score.totalScore}%` }} transition={{ duration: 0.8, delay: i * 0.05 }} className="h-full rounded-full" style={{ background: `linear-gradient(to right, #8a7530, ${score.totalScore >= 80 ? '#22c55e' : '#c9a84c'})` }} />
                </div>
                
                <div className="mt-1.5">
                  <StatusBadge status={fitLabel.label as any} />
                </div>
                
                {/* 风格标签 */}
                <div className="flex flex-wrap gap-0.5 mt-1.5">
                  {trader.base.styleTags.slice(0, 3).map(tag => (
                    <span key={tag} className="text-[8px] px-1 py-0.5 rounded" style={{ color: getStyleTagColor(tag), backgroundColor: getStyleTagColor(tag) + '15' }}>{tag}</span>
                  ))}
                </div>
              </motion.button>
            );
          })}
        </div>
      </DataCard>

      {/* 游资深度分析卡片 */}
      <AnimatePresence>
        {showDeepCard && selectedTrader && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
            <DataCard delay={300} header={
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BarChart3 size={16} className="text-[#c9a84c]" />
                  <h2 className="text-[16px] font-semibold text-[#f1f5f9]">深度分析 - {selectedTrader.base.name}</h2>
                </div>
                <button onClick={() => setShowDeepCard(false)} className="text-[#94a3b8] hover:text-[#f1f5f9] transition-colors">
                  <X size={16} />
                </button>
              </div>
            }>
              <TraderDeepCard trader={selectedTrader} marketState={marketState} />
            </DataCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 当日综合推荐Top3 */}
      <DataCard delay={400} header={
        <div className="flex items-center gap-2">
          <Target size={18} className="text-[#c9a84c]" />
          <h2 className="text-[18px] font-semibold text-[#f1f5f9]">当日综合推荐 Top3</h2>
          <span className="text-[11px] text-[#94a3b8]">多游资匹配概率排序</span>
        </div>
      }>
        <div className="grid grid-cols-3 gap-4">
          {stockProbabilities.map((stock, i) => (
            <motion.div
              key={stock.code}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={cn(
                'rounded-lg border p-4 transition-all hover:-translate-y-[3px]',
                i === 0 ? 'border-[#c9a84c] bg-[rgba(201,168,76,0.05)] shadow-[0_0_20px_rgba(201,168,76,0.1)]' :
                i === 1 ? 'border-[rgba(148,163,184,0.2)] bg-[#0f1929]' :
                'border-[rgba(148,163,184,0.1)] bg-[#0f1929]'
              )}
            >
              {/* 排名徽章 */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-[14px] font-bold"
                    style={{ backgroundColor: i === 0 ? '#c9a84c' : i === 1 ? '#94a3b8' : '#cd7f32', color: '#060b14' }}>
                    {i + 1}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[16px] font-mono font-semibold text-[#f1f5f9]">{stock.code}</span>
                      <span className="text-[14px] text-[#f1f5f9]">{stock.name}</span>
                    </div>
                    <div className="text-[10px] text-[#94a3b8]">主线: {stock.mainSector}</div>
                  </div>
                </div>
                <ScoreRing percent={Math.min(stock.totalScore, 100)} size={44} />
              </div>

              {/* 适配游资 */}
              <div className="mb-2">
                <div className="text-[10px] text-[#475569] mb-1">适配游资</div>
                <div className="flex flex-wrap gap-1">
                  {stock.matchedTraders.slice(0, 4).map(t => (
                    <span key={t.traderId} className="text-[10px] px-1.5 py-0.5 rounded-full border border-[rgba(201,168,76,0.3)] text-[#c9a84c] bg-[rgba(201,168,76,0.08)]">
                      {t.traderName} ({t.score})
                    </span>
                  ))}
                </div>
              </div>

              {/* 综合分 */}
              <div className="flex items-center justify-between pt-2 border-t border-[rgba(148,163,184,0.1)]">
                <span className="text-[11px] text-[#94a3b8]">综合分: <span className="text-[#c9a84c] font-mono font-bold">{stock.totalScore}</span></span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[rgba(34,197,94,0.15)] text-[#22c55e]">关注</span>
              </div>
            </motion.div>
          ))}
        </div>
      </DataCard>

      {/* 组合策略推荐 */}
      <DataCard delay={500} header={
        <div className="flex items-center gap-2">
          <Award size={18} className="text-[#c9a84c]" />
          <h2 className="text-[18px] font-semibold text-[#f1f5f9]">组合策略推荐</h2>
        </div>
      }>
        <div className="grid grid-cols-3 gap-4">
          {[
            { level: '新手', icon: <Award size={20} className="text-[#22c55e]" />, color: '#22c55e', desc: '跟随单一游资，稳健起步', strategy: '选择匹配度最高的游资，严格跟随推荐', rules: ['只做推荐榜前2名', '止损-3%严格执行', '每日最多1笔'], winRate: '60%+', return_: '5-8%/月' },
            { level: '进阶', icon: <Zap size={20} className="text-[#c9a84c]" />, color: '#c9a84c', desc: '多游资共振，提升胜率', strategy: '跟踪3-4位游资，选择共同推荐标的', rules: ['关注共识标的', '允许持有隔夜', '止损-5%线'], winRate: '65%+', return_: '10-15%/月' },
            { level: '高手', icon: <TrendingUp size={20} className="text-[#ef4444]" />, color: '#ef4444', desc: '灵活运用，追逐高收益', strategy: '全量游资跟踪，结合情绪周期自主判断', rules: ['全市场机会', '龙头可重仓', '浮动止损'], winRate: '70%+', return_: '20%+/月' },
          ].map((s, i) => (
            <motion.div key={s.level} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 + i * 0.1 }} className="rounded-lg border border-[rgba(148,163,184,0.1)] bg-[#0f1929] p-4 hover:border-[rgba(201,168,76,0.3)] transition-all">
              <div className="flex items-center gap-2 mb-3">
                {s.icon}
                <h3 className="text-[16px] font-semibold" style={{ color: s.color }}>{s.level}</h3>
              </div>
              <p className="text-[12px] text-[#94a3b8] mb-3">{s.desc}</p>
              <p className="text-[13px] text-[#f1f5f9] mb-3">{s.strategy}</p>
              <div className="space-y-1.5 mb-3">
                {s.rules.map((r, j) => (
                  <div key={j} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: s.color }} />
                    <span className="text-[11px] text-[#94a3b8]">{r}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-3 pt-2 border-t border-[rgba(148,163,184,0.1)]">
                <div className="text-center flex-1">
                  <div className="text-[14px] font-mono font-semibold text-[#f1f5f9]">{s.winRate}</div>
                  <div className="text-[10px] text-[#94a3b8]">预期胜率</div>
                </div>
                <div className="text-center flex-1">
                  <div className="text-[14px] font-mono font-semibold text-[#c9a84c]">{s.return_}</div>
                  <div className="text-[10px] text-[#94a3b8]">预期收益</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </DataCard>

      {/* 分歧预警 */}
      <div className="rounded-lg border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.03)] p-3 flex items-center gap-3">
        <AlertTriangle size={16} className="text-[#ef4444] shrink-0" />
        <div>
          <p className="text-[13px] font-medium text-[#f1f5f9]">分歧预警</p>
          <p className="text-[11px] text-[#94a3b8]">部分游资对当前市场方向存在分歧，建议谨慎操作，控制仓位在50%以内</p>
        </div>
      </div>
    </div>
  );
}