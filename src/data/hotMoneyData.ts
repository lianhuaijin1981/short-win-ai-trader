/**
 * 游资诊股模块 - 核心数据层
 * 
 * 包含：
 * 1. 20个内置游资完整数据（基础信息 + 模式参数 + 深度分析模板）
 * 2. 用户自定义游资管理
 * 3. 行情状态量化
 * 4. 游资模式匹配算法
 * 5. 多游资综合推荐
 */

// ═══════════════════════════════════════════════════════════════
// 类型定义
// ═══════════════════════════════════════════════════════════════

/** 风格标签 */
export type StyleTag = 
  | '首板' | '连板' | '趋势' | '低吸' | '打板' 
  | '大票' | '小票' | '情绪' | '主线' | '套利'
  | '龙头' | '补涨' | '反包' | '做T' | '隔日'
  | '高标' | '全能';

/** 行情适配级别 */
export type MarketFitLevel = '强适配' | '弱适配' | '回避';

/** 情绪周期阶段 */
export type SentimentPhase = '冰点' | '分歧' | '修复' | '高潮' | '退潮' | '混沌';

/** 游资基础信息 */
export interface HotMoneyBase {
  id: string;
  name: string;
  alias?: string;
  seats: string[];
  capitalScale: string; // 资金体量（如"10-50亿"）
  styleTags: StyleTag[];
  activeYears: string;
  winRate: number; // 历史胜率
  monthlyReturn: number; // 月均收益
  maxDrawdown: number; // 最大回撤
  avatar: string;
  isCustom?: boolean;
}

/** 核心交易理念 */
export interface TradingPhilosophy {
  soul: string; // 一句话灵魂
  detail: string; // 详细阐述
}

/** 可量化规则 */
export interface QuantRule {
  name: string;
  condition: string;
  weight: number; // 权重 0-100
}

/** 板型偏好 */
export interface BoardPreference {
  primary: string; // 主要板型（首板/二板/三板+）
  secondary?: string;
  minConsecutive?: number;
}

/** 市值偏好 */
export interface MarketCapPreference {
  min: number; // 最小市值（亿）
  max: number; // 最大市值（亿）
  preferred: '小盘' | '中盘' | '大盘' | '全能';
}

/** 量能要求 */
export interface VolumeRequirement {
  minVolRatio: number; // 最小量比
  minVolTo20d: number; // 最小成交量/20日均量
  preferExplosive: boolean; // 是否偏好爆量
}

/** 封板时间偏好 */
export interface SealTimePreference {
  preferEarly: boolean; // 是否偏好早板
  latestTime?: string; // 最晚封板时间（如"10:30"）
  preferMorning: boolean; // 是否偏好上午
}

/** 位置偏好 */
export interface PositionPreference {
  preferLow: boolean; // 是否偏好低位
  maxDistanceFromHigh: number; // 距前高最大百分比
  avoidHighLevel: boolean; // 是否回避高位
}

/** 情绪适配配置 */
export interface SentimentAdaptation {
  strong: SentimentPhase[]; // 强适配
  weak: SentimentPhase[]; // 弱适配
  avoid: SentimentPhase[]; // 回避
}

/** 板块偏好 */
export interface SectorPreference {
  sectors: string[];
  year: number;
}

/** 操作要点 */
export interface OperationKeyPoint {
  title: string;
  description: string;
}

/** 游资模式参数（完整模板） */
export interface HotMoneyMode {
  id: string; // 关联游资ID
  philosophy: TradingPhilosophy;
  boardPref: BoardPreference;
  marketCapPref: MarketCapPreference;
  volumeReq: VolumeRequirement;
  sealTimePref: SealTimePreference;
  positionPref: PositionPreference;
  sentimentAdapt: SentimentAdaptation;
  sectorPref: SectorPreference;
  operationKeys: OperationKeyPoint[];
  riskControl: string[];
  typicalFeatures: string;
}

/** 完整游资数据 */
export interface HotMoneyTrader {
  base: HotMoneyBase;
  mode: HotMoneyMode;
  // 运行时数据
  matchScore?: number; // 当日匹配分 0-100
  radarData?: number[]; // 雷达图数据
  operations?: OperationRecord[];
  recommendations?: StockRecommendation[];
}

/** 操作记录 */
export interface OperationRecord {
  date: string;
  code: string;
  name: string;
  action: 'buy' | 'sell';
  price: number;
  pnl?: number;
}

/** 股票推荐 */
export interface StockRecommendation {
  code: string;
  name: string;
  matchScore: number;
  tactics: string[];
  reasons: string[];
  action: 'intervene' | 'observe';
  currentPrice: number;
  changePercent: number;
  marketCap: number;
  volRatio: number;
  sealTime?: string;
  position: string;
  sector: string;
}

// ═══════════════════════════════════════════════════════════════
// 行情状态量化
// ═══════════════════════════════════════════════════════════════

export interface MarketState {
  date: string;
  // 情绪周期
  sentimentPhase: SentimentPhase;
  sentimentScore: number; // 0-10
  // 主线强度
  mainLineStrength: number; // 0-10
  mainLineType: '单一主线' | '多主线' | '无主线';
  // 连板高度
  maxConsecutive: number;
  consecutiveCount: number; // 连板家数
  // 量能环境
  totalVolume: number; // 两市成交额（亿）
  volumeStatus: '放量' | '平量' | '缩量';
  // 市值偏好
  preferredMarketCap: '小盘' | '中盘' | '大盘' | '均衡';
  // 涨停时间分布
  earlySealCount: number; // 10:30前封板数
  // 首板/连板结构
  firstBoardCount: number;
  consecutiveBoardCount: number;
}

// ═══════════════════════════════════════════════════════════════
// 匹配算法
// ═══════════════════════════════════════════════════════════════

/** 匹配分计算结果 */
export interface MatchScoreResult {
  traderId: string;
  traderName: string;
  totalScore: number; // 0-100
  emotionScore: number; // 0-30
  boardScore: number; // 0-25
  marketCapScore: number; // 0-20
  volumeScore: number; // 0-15
  positionScore: number; // 0-10
  rank: number;
}

/** 股票游资参与概率 */
export interface StockHotMoneyProbability {
  code: string;
  name: string;
  totalScore: number;
  matchedTraders: { traderId: string; traderName: string; score: number }[];
  mainSector: string;
}

// ═══════════════════════════════════════════════════════════════
// 20个内置游资完整数据
// ═══════════════════════════════════════════════════════════════

export const BUILT_IN_HOT_MONEY: HotMoneyTrader[] = [
  {
    base: {
      id: 'zhangmengzhu',
      name: '章盟主',
      alias: '章建平',
      seats: ['国泰君安证券上海江苏路', '中信证券杭州四季路'],
      capitalScale: '50-100亿',
      styleTags: ['趋势', '大票', '龙头', '主线'],
      activeYears: '2006-至今',
      winRate: 65.8,
      monthlyReturn: 12.5,
      maxDrawdown: -15.2,
      avatar: '章盟',
    },
    mode: {
      id: 'zhangmengzhu',
      philosophy: {
        soul: '格局大票，做趋势龙头的主升浪',
        detail: '专注于大市值趋势龙头，不追求连板高度，而是把握主线题材的核心标的在主升段的确定性收益。资金体量大，偏好流动性好的大票。',
      },
      boardPref: { primary: '趋势板', secondary: '首板', minConsecutive: 1 },
      marketCapPref: { min: 100, max: 1000, preferred: '大盘' },
      volumeReq: { minVolRatio: 1.5, minVolTo20d: 1.2, preferExplosive: true },
      sealTimePref: { preferEarly: false, preferMorning: false },
      positionPref: { preferLow: false, maxDistanceFromHigh: 30, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮'],
        weak: ['分歧'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '半导体', '新能源', '消费电子'], year: 2026 },
      operationKeys: [
        { title: '只做主线龙头', description: '非主线不参与，非龙头不重仓' },
        { title: '趋势持股', description: '均线多头排列期间坚定持有，不被盘中波动震出' },
        { title: '大资金分仓', description: '单票不超过总仓位20%，分散3-5只标的' },
      ],
      riskControl: ['跌破20日线减仓50%', '跌破60日线清仓', '单票最大回撤≤15%'],
      typicalFeatures: '"大格局游资"，以超大资金参与大市值趋势股，持股周期长，单笔收益高，是趋势交易的标杆。',
    },
    radarData: [40, 75, 90, 85, 95, 80, 70, 65],
    matchScore: 0,
  },
  {
    base: {
      id: 'fangxinxia',
      name: '方新侠',
      alias: '格局大票王',
      seats: ['中信证券西安朱雀大街', '申万宏源证券西安南大街'],
      capitalScale: '20-50亿',
      styleTags: ['趋势', '大票', '龙头', '连板'],
      activeYears: '2015-至今',
      winRate: 63.2,
      monthlyReturn: 14.8,
      maxDrawdown: -18.5,
      avatar: '方侠',
    },
    mode: {
      id: 'fangxinxia',
      philosophy: {
        soul: '格局大票，趋势与连板结合',
        detail: '既做趋势龙头也做连板龙头，但核心是"格局"——看准了就重仓持有，不轻易下车。偏好有基本面支撑的题材龙头。',
      },
      boardPref: { primary: '趋势板', secondary: '连板', minConsecutive: 2 },
      marketCapPref: { min: 50, max: 500, preferred: '中盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: true },
      sealTimePref: { preferEarly: true, preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 20, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮', '分歧'],
        weak: ['混沌'],
        avoid: ['退潮'],
      },
      sectorPref: { sectors: ['AI算力', '机器人', '商业航天', '半导体'], year: 2026 },
      operationKeys: [
        { title: '龙头信仰', description: '只做市场辨识度最高的龙头' },
        { title: '格局持有', description: '看准后敢于重仓并持有，不轻易止盈' },
        { title: '基本面驱动', description: '偏好有业绩或强逻辑支撑的题材' },
      ],
      riskControl: ['龙头断板次日不反包离场', '单票仓位≤30%', '总回撤超10%降仓'],
      typicalFeatures: '"格局侠"，以敢于重仓龙头并坚定持有闻名，操作风格大开大合，是趋势+连板结合的代表。',
    },
    radarData: [60, 70, 80, 88, 92, 85, 65, 72],
    matchScore: 0,
  },
  {
    base: {
      id: 'zuoshouxinyi',
      name: '作手新一',
      alias: '高标连板王',
      seats: ['国泰君安证券南京太平南路', '华泰证券南京金融城'],
      capitalScale: '10-30亿',
      styleTags: ['连板', '高标', '情绪', '龙头'],
      activeYears: '2017-至今',
      winRate: 61.5,
      monthlyReturn: 18.2,
      maxDrawdown: -22.3,
      avatar: '新一',
    },
    mode: {
      id: 'zuoshouxinyi',
      philosophy: {
        soul: '高标连板，主升加速段吃肉',
        detail: '专注于市场最高连板标的，在3-5板的主升加速段介入，享受强者恒强的溢价。不低吸，只做确认后的龙头。',
      },
      boardPref: { primary: '连板', secondary: '三板+', minConsecutive: 3 },
      marketCapPref: { min: 30, max: 300, preferred: '中盘' },
      volumeReq: { minVolRatio: 2.5, minVolTo20d: 2, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:00', preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 10, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['高潮', '修复'],
        weak: ['分歧'],
        avoid: ['冰点', '退潮', '混沌'],
      },
      sectorPref: { sectors: ['AI应用', '机器人', '低空经济', '商业航天'], year: 2026 },
      operationKeys: [
        { title: '只做最高标', description: '市场总龙头或并列最高连板' },
        { title: '加速段介入', description: '3-5板是最佳介入窗口' },
        { title: '不低吸', description: '只做确认强势的标的，不抄底' },
      ],
      riskControl: ['断板次日不反包坚决离场', '单票≤25%', '不做补涨龙'],
      typicalFeatures: '"高标王"，以极致的龙头信仰和高标接力闻名，操作干净利落，是连板高标交易的标杆。',
    },
    radarData: [90, 40, 50, 95, 98, 90, 55, 78],
    matchScore: 0,
  },
  {
    base: {
      id: 'sunge',
      name: '孙哥',
      alias: '古北路/溧阳路',
      seats: ['中信证券上海溧阳路', '海通证券上海古北路'],
      capitalScale: '10-30亿',
      styleTags: ['连板', '高标', '情绪', '打板'],
      activeYears: '2014-至今',
      winRate: 60.8,
      monthlyReturn: 16.5,
      maxDrawdown: -20.1,
      avatar: '孙哥',
    },
    mode: {
      id: 'sunge',
      philosophy: {
        soul: '三板+高标，情绪接力引导加速',
        detail: '专注于三板及以上的高标接力，在情绪确认期介入，享受连板加速段的溢价。擅长引导市场情绪，是情绪接力的代表人物。',
      },
      boardPref: { primary: '连板', secondary: '三板+', minConsecutive: 3 },
      marketCapPref: { min: 20, max: 200, preferred: '小盘' },
      volumeReq: { minVolRatio: 3, minVolTo20d: 2, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:30', preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 15, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮'],
        weak: ['分歧'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '半导体', '机器人', '低空经济'], year: 2026 },
      operationKeys: [
        { title: '三板定龙头', description: '三板是确认龙头的关键节点' },
        { title: '情绪共振', description: '只在情绪确认期出手' },
        { title: '引导加速', description: '善于引导市场情绪推动连板加速' },
      ],
      riskControl: ['断板即减仓', '炸板次日低开止损', '单票≤20%'],
      typicalFeatures: '"情绪引导者"，以三板及以上高标接力闻名，擅长把握情绪周期节点，是情绪接力的代表。',
    },
    radarData: [88, 45, 55, 92, 95, 88, 58, 75],
    matchScore: 0,
  },
  {
    base: {
      id: 'chenxiaoqun',
      name: '陈小群',
      alias: '金马路',
      seats: ['中国银河证券大连金马路', '中国银河证券大连黄河路'],
      capitalScale: '10-30亿',
      styleTags: ['主线', '趋势', '连板', '龙头'],
      activeYears: '2019-至今',
      winRate: 67.3,
      monthlyReturn: 19.5,
      maxDrawdown: -13.8,
      avatar: '小群',
    },
    mode: {
      id: 'chenxiaoqun',
      philosophy: {
        soul: '主线赛道，趋势与连板结合，3倍量启动',
        detail: '专注于主线赛道的趋势龙头，偏好3倍量启动的标的，结合机构资金协同。既做连板也做趋势，核心是主线确定性。',
      },
      boardPref: { primary: '趋势板', secondary: '连板', minConsecutive: 2 },
      marketCapPref: { min: 30, max: 300, preferred: '中盘' },
      volumeReq: { minVolRatio: 3, minVolTo20d: 2.5, preferExplosive: true },
      sealTimePref: { preferEarly: true, preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 20, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮', '分歧'],
        weak: ['混沌'],
        avoid: ['退潮'],
      },
      sectorPref: { sectors: ['AI算力', '半导体', '机器人', '新能源'], year: 2026 },
      operationKeys: [
        { title: '3倍量启动', description: '成交量达到20日均量3倍是核心信号' },
        { title: '主线赛道', description: '只做市场主线题材' },
        { title: '机构协同', description: '偏好有机构资金参与的标的' },
      ],
      riskControl: ['跌破5日线减仓', '主线退潮离场', '单票≤25%'],
      typicalFeatures: '"金马路"，以主线赛道趋势交易闻名，擅长3倍量启动信号，是机构与游资协同的代表。',
    },
    radarData: [75, 65, 75, 85, 88, 82, 68, 70],
    matchScore: 0,
  },
  {
    base: {
      id: 'hujialou',
      name: '呼家楼',
      alias: 'LV/北京帮',
      seats: ['中信证券北京呼家楼', '广发证券北京金融街'],
      capitalScale: '20-50亿',
      styleTags: ['情绪', '打板', '主线', '龙头'],
      activeYears: '2016-至今',
      winRate: 58.5,
      monthlyReturn: 15.2,
      maxDrawdown: -25.8,
      avatar: '呼家',
    },
    mode: {
      id: 'hujialou',
      philosophy: {
        soul: '退潮硬顶，AI/半导体情绪风向标',
        detail: '在退潮末期敢于硬顶龙头，是市场情绪的风向标。专注于AI和半导体主线，在情绪冰点敢于左侧布局。',
      },
      boardPref: { primary: '连板', secondary: '首板', minConsecutive: 1 },
      marketCapPref: { min: 50, max: 500, preferred: '中盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: true },
      sealTimePref: { preferEarly: false, preferMorning: false },
      positionPref: { preferLow: true, maxDistanceFromHigh: 25, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['冰点', '退潮'],
        weak: ['分歧'],
        avoid: ['高潮'],
      },
      sectorPref: { sectors: ['AI算力', '半导体', 'AI应用', '存储芯片'], year: 2026 },
      operationKeys: [
        { title: '退潮硬顶', description: '在退潮末期敢于硬顶龙头' },
        { title: '左侧布局', description: '情绪冰点敢于左侧介入' },
        { title: 'AI信仰', description: '专注于AI和半导体主线' },
      ],
      riskControl: ['退潮延续止损', '单票≤20%', '总仓位随情绪调整'],
      typicalFeatures: '"情绪风向标"，以退潮期硬顶龙头闻名，是市场情绪转折的先行指标。',
    },
    radarData: [82, 70, 60, 88, 85, 75, 50, 68],
    matchScore: 0,
  },
  {
    base: {
      id: 'shangtanglu',
      name: '上塘路',
      alias: '杭州',
      seats: ['财通证券杭州上塘路', '财通证券杭州文二西路'],
      capitalScale: '5-15亿',
      styleTags: ['首板', '打板', '小票', '情绪'],
      activeYears: '2018-至今',
      winRate: 72.5,
      monthlyReturn: 11.8,
      maxDrawdown: -8.5,
      avatar: '上塘',
    },
    mode: {
      id: 'shangtanglu',
      philosophy: {
        soul: '冰点做首板，分歧硬封二板，不贪隔日必走',
        detail: '专注于冰点期的首板和分歧日的二板硬封，只赚确定性的溢价。次日不贪，有赚就走，不及预期直接砸。是首板交易的极致代表。',
      },
      boardPref: { primary: '首板', secondary: '二板', minConsecutive: 1 },
      marketCapPref: { min: 30, max: 80, preferred: '小盘' },
      volumeReq: { minVolRatio: 3, minVolTo20d: 2, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:30', preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 10, avoidHighLevel: true },
      sentimentAdapt: {
        strong: ['冰点', '分歧'],
        weak: ['修复'],
        avoid: ['高潮', '混沌'],
      },
      sectorPref: { sectors: ['AI应用', '消费电子', '汽配', '低位题材'], year: 2026 },
      operationKeys: [
        { title: '只做首板辨识度', description: '首板必须有板块辨识度' },
        { title: '冰点硬封二板', description: '冰点日硬封二板是确定性最高的模式' },
        { title: '弱转强必上', description: '首板烂板次日弱转强直接介入' },
        { title: '次日不贪', description: '有赚就走，不及预期直接砸' },
      ],
      riskControl: ['不碰ST', '不碰次新<30天', '流通市值<30亿不做', '首板炸板次日低开≤-3%止损'],
      typicalFeatures: '"首板冰点之王"，以极高的首板封板率和次日溢价率闻名，是低风险超短交易的典范。',
    },
    radarData: [95, 60, 40, 85, 70, 92, 85, 80],
    matchScore: 0,
  },
  {
    base: {
      id: 'sangtianlu',
      name: '桑田路',
      alias: '宁波',
      seats: ['华泰证券宁波桑田路', '国盛证券宁波桑田路'],
      capitalScale: '5-15亿',
      styleTags: ['首板', '连板', '小票', '低吸'],
      activeYears: '2017-至今',
      winRate: 68.2,
      monthlyReturn: 10.5,
      maxDrawdown: -9.2,
      avatar: '桑田',
    },
    mode: {
      id: 'sangtianlu',
      philosophy: {
        soul: '低位首板到二板，小盘换手，稳健低吸',
        detail: '专注于低位首板到二板的换手板，偏好小盘股，通过稳健低吸获取收益。不追高，只做确认后的换手板。',
      },
      boardPref: { primary: '首板', secondary: '二板', minConsecutive: 1 },
      marketCapPref: { min: 20, max: 60, preferred: '小盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: false },
      sealTimePref: { preferEarly: false, preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 15, avoidHighLevel: true },
      sentimentAdapt: {
        strong: ['冰点', '分歧', '修复'],
        weak: ['高潮'],
        avoid: ['混沌'],
      },
      sectorPref: { sectors: ['低位题材', '消费电子', '汽配', '化工'], year: 2026 },
      operationKeys: [
        { title: '低位换手板', description: '只做充分换手后的低位板' },
        { title: '稳健低吸', description: '不追高，低吸确认后的标的' },
        { title: '小盘偏好', description: '偏好20-60亿小盘股' },
      ],
      riskControl: ['不追一字板', '单票≤15%', '炸板次日低开止损'],
      typicalFeatures: '"稳健低吸王"，以低位换手板的稳健低吸闻名，胜率极高，回撤控制优秀。',
    },
    radarData: [80, 85, 50, 75, 65, 78, 88, 75],
    matchScore: 0,
  },
  {
    base: {
      id: 'foshan',
      name: '佛山无影脚',
      alias: '廖国沛',
      seats: ['光大证券佛山绿景路', '华福证券佛山南海大道'],
      capitalScale: '5-10亿',
      styleTags: ['首板', '打板', '小票', '隔日'],
      activeYears: '2010-至今',
      winRate: 70.8,
      monthlyReturn: 9.5,
      maxDrawdown: -7.8,
      avatar: '佛山',
    },
    mode: {
      id: 'foshan',
      philosophy: {
        soul: '低位点火，首板顶板，次日必走',
        detail: '专注于低位股的首板点火，封板后次日必走，不贪连板。是超短线隔日套利的极致代表。',
      },
      boardPref: { primary: '首板', minConsecutive: 1 },
      marketCapPref: { min: 20, max: 100, preferred: '小盘' },
      volumeReq: { minVolRatio: 2.5, minVolTo20d: 1.8, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:00', preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 10, avoidHighLevel: true },
      sentimentAdapt: {
        strong: ['冰点', '分歧', '修复'],
        weak: ['高潮'],
        avoid: ['混沌'],
      },
      sectorPref: { sectors: ['低位题材', '超跌反弹', '轮动题材'], year: 2026 },
      operationKeys: [
        { title: '低位点火', description: '在低位股启动时点火封板' },
        { title: '次日必走', description: '无论盈亏次日必走' },
        { title: '不贪连板', description: '只做首板隔日套利' },
      ],
      riskControl: ['次日低开≤-3%竞价止损', '单票≤10%', '每日最多3笔'],
      typicalFeatures: '"隔日套利王"，以首板次日必走的纪律闻名，是超短线隔日套利的极致代表。',
    },
    radarData: [92, 55, 35, 80, 60, 88, 90, 85],
    matchScore: 0,
  },
  {
    base: {
      id: 'xinzhalu',
      name: '新闸路',
      alias: '全周期龙头',
      seats: ['中信证券上海新闸路'],
      capitalScale: '10-30亿',
      styleTags: ['龙头', '趋势', '连板', '全能'],
      activeYears: '2015-至今',
      winRate: 66.5,
      monthlyReturn: 16.8,
      maxDrawdown: -14.2,
      avatar: '新闸',
    },
    mode: {
      id: 'xinzhalu',
      philosophy: {
        soul: '全周期龙头，低位敢扫，中位敢顶，高位敢转',
        detail: '覆盖情绪全周期，在低位敢于扫货，在中位敢于顶板，在高位敢于转换。是全能力最强的游资之一。',
      },
      boardPref: { primary: '连板', secondary: '趋势板', minConsecutive: 2 },
      marketCapPref: { min: 30, max: 300, preferred: '全能' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: true },
      sealTimePref: { preferEarly: true, preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 30, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['冰点', '分歧', '修复', '高潮'],
        weak: [],
        avoid: ['混沌'],
      },
      sectorPref: { sectors: ['AI应用', '机器人', '半导体', '新能源'], year: 2026 },
      operationKeys: [
        { title: '低位扫货', description: '冰点期低位龙头敢于重仓' },
        { title: '中位顶板', description: '确认期敢于顶板接力' },
        { title: '高位转换', description: '高位龙头断板后快速转换新标的' },
      ],
      riskControl: ['混沌期降仓', '单票≤25%', '总回撤超12%强制空仓'],
      typicalFeatures: '"全周期王"，以覆盖情绪全周期的交易能力闻名，是全能型游资的代表。',
    },
    radarData: [78, 72, 75, 82, 85, 80, 72, 78],
    matchScore: 0,
  },
  {
    base: {
      id: 'huzhou',
      name: '湖州劳动路',
      alias: '做T大师',
      seats: ['中国银河证券湖州劳动路'],
      capitalScale: '5-15亿',
      styleTags: ['连板', '做T', '情绪', '龙头'],
      activeYears: '2016-至今',
      winRate: 64.8,
      monthlyReturn: 13.5,
      maxDrawdown: -11.5,
      avatar: '湖州',
    },
    mode: {
      id: 'huzhou',
      philosophy: {
        soul: '二板后接力，多日做T，团控筹码',
        detail: '专注于二板后的接力机会，通过多日做T降低成本，团体控制筹码。是筹码控制最精细的游资。',
      },
      boardPref: { primary: '连板', secondary: '二板', minConsecutive: 2 },
      marketCapPref: { min: 20, max: 150, preferred: '小盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: false },
      sealTimePref: { preferEarly: false, preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 20, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮'],
        weak: ['分歧'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '消费电子', '机器人'], year: 2026 },
      operationKeys: [
        { title: '二板后接力', description: '二板确认后介入做T' },
        { title: '多日做T', description: '通过日内做T持续降低成本' },
        { title: '团控筹码', description: '团体协作控制筹码节奏' },
      ],
      riskControl: ['做T失败次日止损', '单票≤20%', '筹码松动离场'],
      typicalFeatures: '"做T大师"，以精细的筹码控制和多日做T能力闻名，是团体协作的代表。',
    },
    radarData: [70, 78, 65, 75, 72, 70, 82, 85],
    matchScore: 0,
  },
  {
    base: {
      id: 'yinxiulu',
      name: '隐秀路',
      alias: '高标接力王',
      seats: ['华泰证券深圳益田路隐秀路'],
      capitalScale: '10-20亿',
      styleTags: ['连板', '高标', '情绪', '龙头'],
      activeYears: '2017-至今',
      winRate: 59.5,
      monthlyReturn: 17.2,
      maxDrawdown: -23.5,
      avatar: '隐秀',
    },
    mode: {
      id: 'yinxiulu',
      philosophy: {
        soul: '高标接力，连板抱团，情绪高潮',
        detail: '专注于高标连板的接力，在情绪高潮期抱团龙头，享受连板溢价。是情绪高潮期的极致参与者。',
      },
      boardPref: { primary: '连板', secondary: '三板+', minConsecutive: 3 },
      marketCapPref: { min: 20, max: 200, preferred: '小盘' },
      volumeReq: { minVolRatio: 2.5, minVolTo20d: 2, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:00', preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 10, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['高潮'],
        weak: ['修复'],
        avoid: ['冰点', '分歧', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '机器人', '低空经济'], year: 2026 },
      operationKeys: [
        { title: '高标抱团', description: '情绪高潮期抱团最高标' },
        { title: '连板接力', description: '3板以上接力为主' },
        { title: '快进快出', description: '断板即走不恋战' },
      ],
      riskControl: ['断板次日必走', '单票≤20%', '退潮期空仓'],
      typicalFeatures: '"高标抱团王"，以情绪高潮期抱团最高标闻名，是高潮期的极致参与者。',
    },
    radarData: [90, 45, 45, 90, 95, 85, 48, 72],
    matchScore: 0,
  },
  {
    base: {
      id: 'zhaolaoge',
      name: '赵老哥',
      alias: '八年一万倍',
      seats: ['中国银河证券绍兴', '浙商证券绍兴人民中路'],
      capitalScale: '50-100亿',
      styleTags: ['连板', '龙头', '打板', '趋势'],
      activeYears: '2008-至今',
      winRate: 68.5,
      monthlyReturn: 22.5,
      maxDrawdown: -18.8,
      avatar: '老哥',
    },
    mode: {
      id: 'zhaolaoge',
      philosophy: {
        soul: '短线龙头，连板接力，换手板，强趋势',
        detail: ' legendary游资，八年一万倍的传奇。专注于短线龙头的连板接力，偏好换手板，把握强趋势行情。是短线交易的传奇人物。',
      },
      boardPref: { primary: '连板', secondary: '换手板', minConsecutive: 2 },
      marketCapPref: { min: 20, max: 300, preferred: '中盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: true },
      sealTimePref: { preferEarly: true, preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 20, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮'],
        weak: ['分歧'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '半导体', '机器人', '新能源'], year: 2026 },
      operationKeys: [
        { title: '龙头信仰', description: '只做市场总龙头' },
        { title: '换手板偏好', description: '偏好充分换手的连板' },
        { title: '强趋势', description: '把握强趋势行情的主升段' },
      ],
      riskControl: ['龙头断板离场', '单票≤25%', '总回撤超15%降仓'],
      typicalFeatures: '"八年一万倍"，短线交易的传奇人物，以龙头连板接力闻名，是短线交易的标杆。',
    },
    radarData: [85, 60, 65, 92, 96, 88, 62, 80],
    matchScore: 0,
  },
  {
    base: {
      id: 'ningbo',
      name: '宁波解放南',
      alias: '首板二板专家',
      seats: ['光大证券宁波解放南路'],
      capitalScale: '5-15亿',
      styleTags: ['首板', '连板', '小票', '情绪', '打板'],
      activeYears: '2012-至今',
      winRate: 66.2,
      monthlyReturn: 11.2,
      maxDrawdown: -10.5,
      avatar: '解放南',
    },
    mode: {
      id: 'ningbo',
      philosophy: {
        soul: '首板二板，小盘情绪启动，打板为主',
        detail: '专注于首板和二板的小盘股，在情绪启动期打板介入。是情绪启动期的先行指标。',
      },
      boardPref: { primary: '首板', secondary: '二板', minConsecutive: 1 },
      marketCapPref: { min: 15, max: 80, preferred: '小盘' },
      volumeReq: { minVolRatio: 2.5, minVolTo20d: 2, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:30', preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 15, avoidHighLevel: true },
      sentimentAdapt: {
        strong: ['冰点', '修复'],
        weak: ['分歧'],
        avoid: ['高潮', '退潮'],
      },
      sectorPref: { sectors: ['低位题材', '新题材', '轮动题材'], year: 2026 },
      operationKeys: [
        { title: '情绪启动', description: '在情绪启动期打板介入' },
        { title: '小盘偏好', description: '偏好15-80亿小盘股' },
        { title: '打板为主', description: '以打板为主要交易方式' },
      ],
      riskControl: ['炸板次日止损', '单票≤15%', '退潮期空仓'],
      typicalFeatures: '"情绪启动先锋"，以首板二板的小盘股打板闻名，是情绪启动期的先行指标。',
    },
    radarData: [88, 65, 45, 82, 70, 85, 78, 72],
    matchScore: 0,
  },
  {
    base: {
      id: 'jintianlu',
      name: '金田路',
      alias: '高位接力王',
      seats: ['华泰证券深圳金田路'],
      capitalScale: '10-20亿',
      styleTags: ['连板', '高标', '情绪', '龙头'],
      activeYears: '2015-至今',
      winRate: 57.8,
      monthlyReturn: 16.8,
      maxDrawdown: -24.5,
      avatar: '金田',
    },
    mode: {
      id: 'jintianlu',
      philosophy: {
        soul: '高位接力，龙头加速，强情绪，不低吸',
        detail: '专注于高位龙头的接力，在加速段介入，只做强情绪行情。不低吸，只做确认后的强势股。',
      },
      boardPref: { primary: '连板', secondary: '三板+', minConsecutive: 3 },
      marketCapPref: { min: 30, max: 200, preferred: '中盘' },
      volumeReq: { minVolRatio: 3, minVolTo20d: 2.5, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:00', preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 10, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['高潮'],
        weak: ['修复'],
        avoid: ['冰点', '分歧', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '机器人', '低空经济'], year: 2026 },
      operationKeys: [
        { title: '高位接力', description: '3板以上高位接力' },
        { title: '龙头加速', description: '在龙头加速段介入' },
        { title: '不低吸', description: '只做确认后的强势股' },
      ],
      riskControl: ['断板即走', '单票≤20%', '退潮期空仓'],
      typicalFeatures: '"高位接力王"，以高位龙头接力闻名，是强情绪行情的极致参与者。',
    },
    radarData: [92, 40, 40, 95, 98, 90, 45, 70],
    matchScore: 0,
  },
  {
    base: {
      id: 'chaogu',
      name: '炒股养家',
      alias: '养家心法',
      seats: ['华鑫证券上海宛平南路', '华鑫证券上海茅台路'],
      capitalScale: '10-30亿',
      styleTags: ['主线', '龙头', '低吸', '趋势'],
      activeYears: '2010-至今',
      winRate: 68.5,
      monthlyReturn: 12.3,
      maxDrawdown: -8.1,
      avatar: '养家',
    },
    mode: {
      id: 'chaogu',
      philosophy: {
        soul: '情绪为王，龙头为锚，买在分歧，卖在一致',
        detail: '将市场情绪周期作为第一决策维度，先看情绪，再看板块，最后选个股。在分歧期介入龙头，在一致期兑现离场。',
      },
      boardPref: { primary: '首板', secondary: '趋势板', minConsecutive: 1 },
      marketCapPref: { min: 50, max: 200, preferred: '中盘' },
      volumeReq: { minVolRatio: 1.5, minVolTo20d: 1.2, preferExplosive: false },
      sealTimePref: { preferEarly: false, preferMorning: false },
      positionPref: { preferLow: false, maxDistanceFromHigh: 25, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['分歧', '修复'],
        weak: ['高潮'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '半导体', '机器人', '新能源'], year: 2026 },
      operationKeys: [
        { title: '情绪周期', description: '情绪是第一决策维度' },
        { title: '买在分歧', description: '在分歧期介入龙头' },
        { title: '卖在一致', description: '在一致期兑现离场' },
      ],
      riskControl: ['短线亏损>3%预警', '>5%强制止损', '单票≤30%'],
      typicalFeatures: '"情绪周期交易体系奠基者"，以情绪周期为核心的交易体系，影响了后续几代游资。',
    },
    radarData: [75, 80, 70, 88, 85, 75, 82, 88],
    matchScore: 0,
  },
  {
    base: {
      id: 'beijing',
      name: '北京炒家',
      alias: '首板专业户',
      seats: ['中信证券北京总部', '华泰证券北京总部'],
      capitalScale: '5-10亿',
      styleTags: ['首板', '低吸', '小票'],
      activeYears: '2016-至今',
      winRate: 71.5,
      monthlyReturn: 8.8,
      maxDrawdown: -6.5,
      avatar: '北京',
    },
    mode: {
      id: 'beijing',
      philosophy: {
        soul: '首板低位，量能突破，不做连板',
        detail: '专注于低位首板的量能突破，不做连板接力。是低风险首板交易的代表。',
      },
      boardPref: { primary: '首板', minConsecutive: 1 },
      marketCapPref: { min: 20, max: 100, preferred: '小盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:30', preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 15, avoidHighLevel: true },
      sentimentAdapt: {
        strong: ['冰点', '分歧', '修复'],
        weak: ['高潮'],
        avoid: ['混沌'],
      },
      sectorPref: { sectors: ['低位题材', '轮动题材', '超跌反弹'], year: 2026 },
      operationKeys: [
        { title: '低位首板', description: '只做低位启动的首板' },
        { title: '量能突破', description: '成交量突破是核心信号' },
        { title: '不做连板', description: '首板后次日必走' },
      ],
      riskControl: ['首板炸板次日止损', '单票≤15%', '每日最多2笔'],
      typicalFeatures: '"首板专业户"，以低位首板的量能突破交易闻名，是低风险首板交易的代表。',
    },
    radarData: [85, 75, 40, 78, 60, 82, 88, 80],
    matchScore: 0,
  },
  {
    base: {
      id: 'ruhexian',
      name: '瑞鹤仙',
      alias: '题材首板专家',
      seats: ['华泰证券武汉瑞鹤路'],
      capitalScale: '5-10亿',
      styleTags: ['首板', '小票', '隔日', '套利'],
      activeYears: '2014-至今',
      winRate: 69.8,
      monthlyReturn: 9.2,
      maxDrawdown: -7.5,
      avatar: '瑞鹤',
    },
    mode: {
      id: 'ruhexian',
      philosophy: {
        soul: '题材首板，小盘快进快出，隔日为主',
        detail: '专注于题材首板的小盘股交易，快进快出，以隔日套利为主。是超短线题材套利的代表。',
      },
      boardPref: { primary: '首板', minConsecutive: 1 },
      marketCapPref: { min: 15, max: 60, preferred: '小盘' },
      volumeReq: { minVolRatio: 2.5, minVolTo20d: 2, preferExplosive: true },
      sealTimePref: { preferEarly: true, latestTime: '10:00', preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 15, avoidHighLevel: true },
      sentimentAdapt: {
        strong: ['修复', '分歧'],
        weak: ['高潮'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['新题材', '轮动题材', '低位题材'], year: 2026 },
      operationKeys: [
        { title: '题材首板', description: '只做题材启动的首板' },
        { title: '快进快出', description: '隔日必走，不恋战' },
        { title: '小盘偏好', description: '偏好15-60亿小盘股' },
      ],
      riskControl: ['隔日必走', '单票≤10%', '每日最多3笔'],
      typicalFeatures: '"题材首板专家"，以题材首板的小盘股隔日套利闻名，是超短线题材套利的代表。',
    },
    radarData: [82, 70, 35, 85, 65, 80, 85, 78],
    matchScore: 0,
  },
  {
    base: {
      id: 'huaxin',
      name: '华鑫深圳',
      alias: '劳动路协同',
      seats: ['华鑫证券深圳分公司', '华鑫证券上海分公司'],
      capitalScale: '10-20亿',
      styleTags: ['连板', '情绪', '套利'],
      activeYears: '2015-至今',
      winRate: 62.5,
      monthlyReturn: 12.8,
      maxDrawdown: -12.5,
      avatar: '华鑫',
    },
    mode: {
      id: 'huaxin',
      philosophy: {
        soul: '接力交易，多席位联动，流动性溢价',
        detail: '通过多席位联动进行接力交易，把握流动性溢价。是团体协作和席位联动的代表。',
      },
      boardPref: { primary: '连板', secondary: '二板', minConsecutive: 2 },
      marketCapPref: { min: 30, max: 200, preferred: '中盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: false },
      sealTimePref: { preferEarly: false, preferMorning: true },
      positionPref: { preferLow: false, maxDistanceFromHigh: 20, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '高潮'],
        weak: ['分歧'],
        avoid: ['冰点', '退潮'],
      },
      sectorPref: { sectors: ['AI应用', '机器人', '消费电子'], year: 2026 },
      operationKeys: [
        { title: '多席位联动', description: '多席位协同交易' },
        { title: '接力交易', description: '连板接力为主' },
        { title: '流动性溢价', description: '把握流动性溢价机会' },
      ],
      riskControl: ['断板离场', '单票≤20%', '退潮期降仓'],
      typicalFeatures: '"席位联动王"，以多席位联动和接力交易闻名，是团体协作的代表。',
    },
    radarData: [72, 68, 60, 78, 75, 72, 75, 80],
    matchScore: 0,
  },
  {
    base: {
      id: 'lianghua',
      name: '量化新贵',
      alias: '华鑫上海',
      seats: ['华鑫证券上海分公司', '东方财富证券拉萨团结路'],
      capitalScale: '20-50亿',
      styleTags: ['首板', '连板', '打板', '套利'],
      activeYears: '2020-至今',
      winRate: 55.2,
      monthlyReturn: 8.5,
      maxDrawdown: -5.8,
      avatar: '量化',
    },
    mode: {
      id: 'lianghua',
      philosophy: {
        soul: '量化打板，首板二板，纪律极强',
        detail: '通过量化模型进行打板交易，首板二板为主，纪律性极强。是量化交易在超短领域的代表。',
      },
      boardPref: { primary: '首板', secondary: '二板', minConsecutive: 1 },
      marketCapPref: { min: 20, max: 150, preferred: '小盘' },
      volumeReq: { minVolRatio: 2, minVolTo20d: 1.5, preferExplosive: false },
      sealTimePref: { preferEarly: true, latestTime: '10:30', preferMorning: true },
      positionPref: { preferLow: true, maxDistanceFromHigh: 20, avoidHighLevel: false },
      sentimentAdapt: {
        strong: ['修复', '分歧'],
        weak: ['高潮', '冰点'],
        avoid: ['混沌'],
      },
      sectorPref: { sectors: ['轮动题材', '低位题材', '新题材'], year: 2026 },
      operationKeys: [
        { title: '量化模型', description: '基于量化模型筛选标的' },
        { title: '纪律交易', description: '严格执行模型信号' },
        { title: '分散交易', description: '分散多标的交易' },
      ],
      riskControl: ['模型止损', '单票≤5%', '日回撤超2%暂停'],
      typicalFeatures: '"量化打板王"，以量化模型和纪律交易闻名，是量化超短交易的代表。',
    },
    radarData: [78, 60, 45, 75, 65, 70, 92, 95],
    matchScore: 0,
  },
];

// ═══════════════════════════════════════════════════════════════
// 用户自定义游资管理
// ═══════════════════════════════════════════════════════════════

export interface CustomHotMoneyFormData {
  name: string;
  alias?: string;
  seats: string;
  capitalScale: string;
  styleTags: StyleTag[];
  philosophy: string;
  operationMode: string;
  riskControl: string;
  typicalFeatures: string;
  // 模式参数
  boardPref: string;
  marketCapMin: number;
  marketCapMax: number;
  marketCapPreferred: '小盘' | '中盘' | '大盘' | '全能';
  minVolRatio: number;
  preferEarly: boolean;
  preferLow: boolean;
  maxDistanceFromHigh: number;
  strongSentiment: SentimentPhase[];
  weakSentiment: SentimentPhase[];
  avoidSentiment: SentimentPhase[];
  preferredSectors: string;
}

export function createCustomHotMoney(data: CustomHotMoneyFormData, id: string): HotMoneyTrader {
  return {
    base: {
      id,
      name: data.name,
      alias: data.alias,
      seats: data.seats.split(/[,，]/).map(s => s.trim()).filter(Boolean),
      capitalScale: data.capitalScale,
      styleTags: data.styleTags,
      activeYears: '至今',
      winRate: 60,
      monthlyReturn: 8,
      maxDrawdown: -10,
      avatar: data.name.slice(0, 2),
      isCustom: true,
    },
    mode: {
      id,
      philosophy: {
        soul: data.philosophy,
        detail: data.philosophy,
      },
      boardPref: {
        primary: data.boardPref,
        minConsecutive: 1,
      },
      marketCapPref: {
        min: data.marketCapMin,
        max: data.marketCapMax,
        preferred: data.marketCapPreferred,
      },
      volumeReq: {
        minVolRatio: data.minVolRatio,
        minVolTo20d: 1.5,
        preferExplosive: false,
      },
      sealTimePref: {
        preferEarly: data.preferEarly,
        preferMorning: data.preferEarly,
      },
      positionPref: {
        preferLow: data.preferLow,
        maxDistanceFromHigh: data.maxDistanceFromHigh,
        avoidHighLevel: data.preferLow,
      },
      sentimentAdapt: {
        strong: data.strongSentiment,
        weak: data.weakSentiment,
        avoid: data.avoidSentiment,
      },
      sectorPref: {
        sectors: data.preferredSectors.split(/[,，]/).map(s => s.trim()).filter(Boolean),
        year: 2026,
      },
      operationKeys: data.operationMode.split(/[；;]/).map(s => ({
        title: s.trim().slice(0, 10),
        description: s.trim(),
      })).filter(k => k.description),
      riskControl: data.riskControl.split(/[；;]/).map(s => s.trim()).filter(Boolean),
      typicalFeatures: data.typicalFeatures,
    },
    radarData: [70, 60, 55, 65, 60, 58, 62, 60],
    matchScore: 0,
  };
}

// ═══════════════════════════════════════════════════════════════
// 行情状态量化
// ═══════════════════════════════════════════════════════════════

export const DEFAULT_MARKET_STATE: MarketState = {
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
};

// ═══════════════════════════════════════════════════════════════
// 匹配算法实现
// ═══════════════════════════════════════════════════════════════

/**
 * 计算单个游资的当日匹配分
 * 
 * 匹配分 = 情绪适配分(0-30) + 板型适配分(0-25) + 市值适配分(0-20) + 量能适配分(0-15) + 位置适配分(0-10)
 */
export function calculateMatchScore(
  trader: HotMoneyTrader,
  marketState: MarketState
): MatchScoreResult {
  const { mode } = trader;
  
  // 1. 情绪适配分 (0-30)
  let emotionScore = 0;
  if (mode.sentimentAdapt.strong.includes(marketState.sentimentPhase)) {
    emotionScore = 30;
  } else if (mode.sentimentAdapt.weak.includes(marketState.sentimentPhase)) {
    emotionScore = 15;
  } else if (mode.sentimentAdapt.avoid.includes(marketState.sentimentPhase)) {
    emotionScore = 0;
  } else {
    emotionScore = 15; // 默认中等
  }
  
  // 2. 板型适配分 (0-25)
  let boardScore = 0;
  const firstBoardRatio = marketState.firstBoardCount / (marketState.firstBoardCount + marketState.consecutiveBoardCount);
  if (mode.boardPref.primary === '首板' && firstBoardRatio > 0.6) {
    boardScore = 25;
  } else if (mode.boardPref.primary === '连板' && marketState.consecutiveBoardCount > 10) {
    boardScore = 25;
  } else if (mode.boardPref.primary === '趋势板' && marketState.maxConsecutive >= 3) {
    boardScore = 20;
  } else if (mode.boardPref.primary === '首板' && firstBoardRatio > 0.4) {
    boardScore = 15;
  } else {
    boardScore = 10;
  }
  
  // 3. 市值适配分 (0-20)
  let marketCapScore = 0;
  if (mode.marketCapPref.preferred === marketState.preferredMarketCap) {
    marketCapScore = 20;
  } else if (mode.marketCapPref.preferred === '全能') {
    marketCapScore = 18;
  } else if (
    (mode.marketCapPref.preferred === '小盘' && marketState.preferredMarketCap === '均衡') ||
    (mode.marketCapPref.preferred === '中盘' && (marketState.preferredMarketCap === '小盘' || marketState.preferredMarketCap === '大盘'))
  ) {
    marketCapScore = 12;
  } else {
    marketCapScore = 5;
  }
  
  // 4. 量能适配分 (0-15)
  let volumeScore = 0;
  const isVolumeGood = marketState.volumeStatus === '放量' || marketState.totalVolume > 15000;
  if (isVolumeGood && mode.volumeReq.minVolRatio <= 2) {
    volumeScore = 15;
  } else if (isVolumeGood) {
    volumeScore = 10;
  } else if (marketState.volumeStatus === '平量') {
    volumeScore = 8;
  } else {
    volumeScore = 5;
  }
  
  // 5. 位置适配分 (0-10)
  let positionScore = 0;
  const isLowPreference = marketState.sentimentPhase === '冰点' || marketState.sentimentPhase === '退潮';
  if (mode.positionPref.preferLow && isLowPreference) {
    positionScore = 10;
  } else if (!mode.positionPref.preferLow && !isLowPreference) {
    positionScore = 10;
  } else if (mode.positionPref.preferLow) {
    positionScore = 5;
  } else {
    positionScore = 7;
  }
  
  const totalScore = emotionScore + boardScore + marketCapScore + volumeScore + positionScore;
  
  return {
    traderId: trader.base.id,
    traderName: trader.base.name,
    totalScore,
    emotionScore,
    boardScore,
    marketCapScore,
    volumeScore,
    positionScore,
    rank: 0,
  };
}

/**
 * 计算所有游资的匹配分并排序
 */
export function calculateAllMatchScores(
  traders: HotMoneyTrader[],
  marketState: MarketState
): MatchScoreResult[] {
  const scores = traders.map(t => calculateMatchScore(t, marketState));
  scores.sort((a, b) => b.totalScore - a.totalScore);
  scores.forEach((s, i) => s.rank = i + 1);
  return scores;
}

/**
 * 计算单只股票的游资参与概率
 */
export function calculateStockProbability(
  stock: {
    code: string;
    name: string;
    marketCap: number;
    volRatio: number;
    consecutive: number;
    position: '低位' | '中位' | '高位';
    sector: string;
    sealTime?: string;
  },
  traders: HotMoneyTrader[],
  marketState: MarketState
): StockHotMoneyProbability {
  const matchedTraders: { traderId: string; traderName: string; score: number }[] = [];
  
  for (const trader of traders) {
    const { mode } = trader;
    let score = 0;
    
    // 情绪适配
    if (mode.sentimentAdapt.strong.includes(marketState.sentimentPhase)) {
      score += 30;
    } else if (mode.sentimentAdapt.weak.includes(marketState.sentimentPhase)) {
      score += 15;
    } else if (mode.sentimentAdapt.avoid.includes(marketState.sentimentPhase)) {
      score = 0;
      continue;
    }
    
    // 板型适配
    if (mode.boardPref.primary === '首板' && stock.consecutive === 1) score += 25;
    else if (mode.boardPref.primary === '连板' && stock.consecutive >= 2) score += 25;
    else if (mode.boardPref.primary === '趋势板' && stock.consecutive >= 1) score += 20;
    
    // 市值适配
    if (stock.marketCap >= mode.marketCapPref.min && stock.marketCap <= mode.marketCapPref.max) {
      score += 20;
    }
    
    // 量能适配
    if (stock.volRatio >= mode.volumeReq.minVolRatio) {
      score += 15;
    }
    
    // 位置适配
    if (mode.positionPref.preferLow && stock.position === '低位') score += 10;
    else if (!mode.positionPref.avoidHighLevel && stock.position !== '高位') score += 7;
    
    if (score > 0) {
      matchedTraders.push({
        traderId: trader.base.id,
        traderName: trader.base.name,
        score,
      });
    }
  }
  
  const totalScore = matchedTraders.reduce((sum, t) => sum + t.score, 0);
  
  return {
    code: stock.code,
    name: stock.name,
    totalScore,
    matchedTraders: matchedTraders.sort((a, b) => b.score - a.score).slice(0, 5),
    mainSector: stock.sector,
  };
}

// ═══════════════════════════════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════════════════════════════

export function getSentimentPhaseColor(phase: SentimentPhase): string {
  const colors: Record<SentimentPhase, string> = {
    '冰点': '#3b82f6',
    '分歧': '#f97316',
    '修复': '#06d7d7',
    '高潮': '#c9a84c',
    '退潮': '#ef4444',
    '混沌': '#6b7280',
  };
  return colors[phase];
}

export function getMarketFitLabel(adapt: SentimentAdaptation, phase: SentimentPhase): { label: string; color: string } {
  if (adapt.strong.includes(phase)) return { label: '强适配', color: '#22c55e' };
  if (adapt.weak.includes(phase)) return { label: '弱适配', color: '#f59e0b' };
  if (adapt.avoid.includes(phase)) return { label: '回避', color: '#ef4444' };
  return { label: '中性', color: '#6b7280' };
}

export function getStyleTagColor(tag: StyleTag): string {
  const colors: Record<StyleTag, string> = {
    '首板': '#3b82f6',
    '连板': '#8b5cf6',
    '趋势': '#06d7d7',
    '低吸': '#22c55e',
    '打板': '#ef4444',
    '大票': '#f97316',
    '小票': '#ec4899',
    '情绪': '#c9a84c',
    '主线': '#14b8a6',
    '套利': '#6366f1',
    '龙头': '#f43f5e',
    '补涨': '#84cc16',
    '反包': '#a855f7',
    '做T': '#0ea5e9',
    '隔日': '#d946ef',
    '高标': '#f43f5e',
    '全能': '#14b8a6',
  };
  return colors[tag] || '#6b7280';
}
