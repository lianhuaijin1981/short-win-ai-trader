import { useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Upload,
  FileSpreadsheet,
  Image,
  Mic,
  MicOff,
  X,
  Search,
  TrendingUp,
  TrendingDown,
  Eye,
  Trash2,
  BarChart3,
  AlertTriangle,
  Download,
  GitCompare,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTradeRecords } from '@/hooks/useTradeStorage';
import type { TradeRecord, UserProfile, HighFreqError } from '@/data/tradeData';
import * as XLSX from 'xlsx';

// ── 工具函数 ───────────────────────────────────────────────────
const generateId = () => Math.random().toString(36).substring(2, 11);

const MARKET_MAP: Record<string, string> = {
  'SH': '沪市',
  'SZ': '深市',
  'CYB': '创业板',
  'KCB': '科创板',
  'BSE': '北交所',
};

const getMarketLabel = (market: string) => MARKET_MAP[market] || market;

// ── 主组件 ─────────────────────────────────────────────────────
export default function TradeHistory() {
  const { records, addRecord, addRecords, deleteRecord } = useTradeRecords();
  const [showImportModal, setShowImportModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedTrade, setSelectedTrade] = useState<TradeRecord | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'buy' | 'sell'>('all');
  const [_sortName] = useState('tradeTime');
  const [_sortDir] = useState<'asc' | 'desc'>('desc');
  const [importMethod, setImportMethod] = useState<'excel' | 'image' | 'voice' | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null!);
  const imageInputRef = useRef<HTMLInputElement>(null!);

  // 过滤和排序
  const filteredRecords = records
    .filter(r => {
      if (filterType !== 'all' && r.tradeType !== filterType) return false;
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          r.stockCode.toLowerCase().includes(term) ||
          r.stockName.toLowerCase().includes(term) ||
          r.userNote.toLowerCase().includes(term)
        );
      }
      return true;
    })
    .sort((a, b) => {
      const aVal = a[_sortName as keyof TradeRecord];
      const bVal = b[_sortName as keyof TradeRecord];
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return _sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return _sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      return 0;
    });

  // 用户画像计算
  const userProfile: UserProfile = (() => {
    if (records.length === 0) {
      return {
        totalTrades: 0,
        winRate: 0,
        avgProfit: 0,
        avgLoss: 0,
        maxDrawdown: 0,
        maxConsecutiveWins: 0,
        maxConsecutiveLosses: 0,
        preferredTimeSlots: [],
        preferredSectors: [],
        preferredStyles: [],
        highFreqErrors: [],
        tradeHabitSummary: '暂无交易记录',
      };
    }

    const wins = records.filter(r => r.profitLoss > 0);
    const losses = records.filter(r => r.profitLoss <= 0);
    const winRate = (wins.length / records.length) * 100;
    const avgProfit = wins.length > 0 ? wins.reduce((sum, r) => sum + r.profitLoss, 0) / wins.length : 0;
    const avgLoss = losses.length > 0 ? losses.reduce((sum, r) => sum + r.profitLoss, 0) / losses.length : 0;

    // 高频错误分析
    const errorPatterns: Record<string, { count: number; totalLoss: number }> = {};
    losses.forEach(r => {
      const hour = new Date(r.tradeTime).getHours();
      let errorType = '';
      if (hour >= 9 && hour < 10) errorType = '早盘追高';
      else if (hour >= 14 && hour < 15) errorType = '尾盘冲动';
      else if (r.positionRatio > 50) errorType = '重仓亏损';
      else if (r.tradeType === 'buy' && r.profitLoss < -500) errorType = '买入被套';
      else errorType = '其他错误';

      if (!errorPatterns[errorType]) {
        errorPatterns[errorType] = { count: 0, totalLoss: 0 };
      }
      errorPatterns[errorType].count++;
      errorPatterns[errorType].totalLoss += r.profitLoss;
    });

    const highFreqErrors: HighFreqError[] = Object.entries(errorPatterns)
      .map(([type, data]) => ({
        errorType: type,
        count: data.count,
        totalLoss: data.totalLoss,
        description: `${type}共${data.count}次，累计亏损${Math.abs(data.totalLoss).toFixed(0)}元`,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // 时段偏好
    const timeSlots = [
      { timeSlot: '9:30-10:00', tradeCount: 0, winRate: 0 },
      { timeSlot: '10:00-11:30', tradeCount: 0, winRate: 0 },
      { timeSlot: '13:00-14:00', tradeCount: 0, winRate: 0 },
      { timeSlot: '14:00-15:00', tradeCount: 0, winRate: 0 },
    ];
    records.forEach(r => {
      const hour = new Date(r.tradeTime).getHours();
      const minute = new Date(r.tradeTime).getMinutes();
      const time = hour + minute / 60;
      let idx = -1;
      if (time >= 9.5 && time < 10) idx = 0;
      else if (time >= 10 && time < 11.5) idx = 1;
      else if (time >= 13 && time < 14) idx = 2;
      else if (time >= 14 && time < 15) idx = 3;
      if (idx >= 0) {
        timeSlots[idx].tradeCount++;
        if (r.profitLoss > 0) timeSlots[idx].winRate++;
      }
    });
    timeSlots.forEach(ts => {
      ts.winRate = ts.tradeCount > 0 ? (ts.winRate / ts.tradeCount) * 100 : 0;
    });

    return {
      totalTrades: records.length,
      winRate,
      avgProfit,
      avgLoss,
      maxDrawdown: Math.min(...records.map(r => r.profitLoss), 0),
      maxConsecutiveWins: 0,
      maxConsecutiveLosses: 0,
      preferredTimeSlots: timeSlots,
      preferredSectors: [],
      preferredStyles: [],
      highFreqErrors,
      tradeHabitSummary: `共${records.length}笔交易，胜率${winRate.toFixed(1)}%，平均盈利${avgProfit.toFixed(0)}元，平均亏损${avgLoss.toFixed(0)}元`,
    };
  })();

  // Excel 导入
  const handleExcelImport = useCallback((file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json<any>(worksheet);

        const importedTrades: TradeRecord[] = jsonData.map((row: any, _index: number) => {
          const dateStr = row['成交日期'] || row['日期'] || '';
          const timeStr = row['成交时间'] || row['时间'] || '';
          const tradeTime = `${dateStr} ${timeStr}`.trim();
          const code = String(row['证券代码'] || row['代码'] || '');
          const name = String(row['证券名称'] || row['名称'] || '');
          const operation = String(row['操作'] || row['买卖方向'] || '');
          const price = Number(row['成交价格'] || row['价格'] || 0);
          const volume = Number(row['成交数量'] || row['数量'] || 0);
          const amount = Number(row['成交金额'] || row['金额'] || price * volume);
          const fee = Number(row['手续费'] || row['佣金'] || 0);
          const stampTax = Number(row['印花税'] || 0);
          const transferFee = Number(row['过户费'] || 0);
          const profitLoss = Number(row['盈亏'] || row['发生金额'] || 0);

          let market: TradeRecord['market'] = 'SZ';
          if (code.startsWith('6')) market = 'SH';
          else if (code.startsWith('3')) market = 'CYB';
          else if (code.startsWith('688')) market = 'KCB';
          else if (code.startsWith('8') || code.startsWith('4')) market = 'BSE';

          return {
            id: generateId(),
            tradeTime: tradeTime || new Date().toISOString(),
            tradeDate: dateStr || new Date().toISOString().split('T')[0],
            stockCode: code,
            stockName: name,
            market,
            tradeType: operation.includes('买') ? 'buy' : 'sell',
            orderType: 'limit',
            tradePrice: price,
            tradeVolume: volume,
            tradeAmount: amount,
            fee,
            stampTax,
            transferFee,
            profitLoss,
            positionRatio: 0,
            accountBalance: 0,
            dailyPnL: 0,
            currentHolding: 0,
            orderTime: tradeTime,
            cancelRecords: [],
            matchStatus: 'full',
            source: 'excel',
            userNote: '',
            tradeLogic: '',
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };
        });

        addRecords(importedTrades);
        setShowImportModal(false);
        setImportMethod(null);
      } catch (error) {
        console.error('Excel 导入失败:', error);
        alert('Excel 文件解析失败，请检查文件格式');
      }
    };
    reader.readAsArrayBuffer(file);
  }, [addRecords]);

  // 语音输入
  const startVoiceInput = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('您的浏览器不支持语音输入');
      return;
    }
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsRecording(true);
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      parseVoiceInput(transcript);
      setIsRecording(false);
    };
    recognition.onerror = () => setIsRecording(false);
    recognition.onend = () => setIsRecording(false);
    recognition.start();
  }, []);

  // 解析语音输入
  const parseVoiceInput = (text: string) => {
    // 简单解析：今天买入贵州茅台100股价格1800
    const patterns = [
      /(?<action>买入|卖出)\s*(?<name>[\u4e00-\u9fa5]+)\s*(?<volume>\d+)\s*股\s*(?:价格)?\s*(?<price>\d+\.?\d*)/,
      /(?<name>[\u4e00-\u9fa5]+)\s*(?<action>买入|卖出)\s*(?<volume>\d+)\s*股\s*(?<price>\d+\.?\d*)/,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        const groups = match.groups || {};
        const newTrade: TradeRecord = {
          id: generateId(),
          tradeTime: new Date().toISOString(),
          tradeDate: new Date().toISOString().split('T')[0],
          stockCode: '',
          stockName: groups.name || '',
          market: 'SZ',
          tradeType: groups.action?.includes('买') ? 'buy' : 'sell',
          orderType: 'limit',
          tradePrice: Number(groups.price) || 0,
          tradeVolume: Number(groups.volume) || 0,
          tradeAmount: (Number(groups.price) || 0) * (Number(groups.volume) || 0),
          fee: 0,
          stampTax: 0,
          transferFee: 0,
          profitLoss: 0,
          positionRatio: 0,
          accountBalance: 0,
          dailyPnL: 0,
          currentHolding: 0,
          orderTime: new Date().toISOString(),
          cancelRecords: [],
          matchStatus: 'full',
          source: 'voice',
          userNote: `语音识别: ${text}`,
          tradeLogic: '',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        addRecord(newTrade);
        setShowImportModal(false);
        return;
      }
    }
    alert('未能识别交易内容，请使用格式："买入/卖出 股票名 数量 股 价格"');
  };

  // 统计数据
  const totalTrades = records.length;
  const totalProfit = records.reduce((sum, r) => sum + r.profitLoss, 0);
  const winCount = records.filter(r => r.profitLoss > 0).length;
  const winRate = totalTrades > 0 ? (winCount / totalTrades) * 100 : 0;

  return (
    <div className="h-full flex flex-col bg-[#0d1526] text-[#e2e8f0]">
      {/* 顶部统计栏 */}
      <div className="grid grid-cols-4 gap-4 px-4 py-3 border-b border-[rgba(148,163,184,0.1)] bg-[#111827]">
        <StatCard label="总交易笔数" value={totalTrades} icon={<BarChart3 size={20} />} />
        <StatCard label="总盈亏" value={`${totalProfit >= 0 ? '+' : ''}${totalProfit.toFixed(0)}`} icon={totalProfit >= 0 ? <TrendingUp size={20} className="text-[#22c55e]" /> : <TrendingDown size={20} className="text-[#ef4444]" />} />
        <StatCard label="盈利笔数" value={winCount} icon={<TrendingUp size={20} className="text-[#22c55e]" />} />
        <StatCard label="胜率" value={`${winRate.toFixed(1)}%`} icon={<BarChart3 size={20} />} />
      </div>

      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)] bg-[#0f172a]">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={16} className="absolute left-2 top-1/2 -translate-y-1/2 text-[#64748b]" />
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="搜索股票代码/名称/备注"
              className="pl-8 pr-3 py-1.5 bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded text-sm text-[#e2e8f0] w-64"
            />
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setFilterType('all')}
              className={cn(
                'px-3 py-1.5 rounded text-sm transition-colors',
                filterType === 'all' ? 'bg-[#c9a84c] text-[#0d1526]' : 'bg-[#1e293b] text-[#94a3b8] hover:bg-[#334155]'
              )}
            >
              全部
            </button>
            <button
              onClick={() => setFilterType('buy')}
              className={cn(
                'px-3 py-1.5 rounded text-sm transition-colors',
                filterType === 'buy' ? 'bg-[#22c55e] text-white' : 'bg-[#1e293b] text-[#94a3b8] hover:bg-[#334155]'
              )}
            >
              买入
            </button>
            <button
              onClick={() => setFilterType('sell')}
              className={cn(
                'px-3 py-1.5 rounded text-sm transition-colors',
                filterType === 'sell' ? 'bg-[#ef4444] text-white' : 'bg-[#1e293b] text-[#94a3b8] hover:bg-[#334155]'
              )}
            >
              卖出
            </button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowProfileModal(true)}
            className="flex items-center gap-1 px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] rounded text-sm transition-colors"
          >
            <BarChart3 size={14} />
            用户画像
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-1 px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] rounded text-sm transition-colors"
          >
            <Upload size={14} />
            导入交易
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1 px-4 py-1.5 bg-[#c9a84c] hover:bg-[#b8943f] text-[#0d1526] rounded text-sm font-medium transition-colors"
          >
            <Plus size={14} />
            手动录入
          </button>
        </div>
      </div>

      {/* 交易记录列表 */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[#111827] z-10">
            <tr className="border-b border-[rgba(148,163,184,0.1)]">
              <th className="px-4 py-2 text-left text-[#64748b] font-medium">时间</th>
              <th className="px-4 py-2 text-left text-[#64748b] font-medium">代码</th>
              <th className="px-4 py-2 text-left text-[#64748b] font-medium">名称</th>
              <th className="px-4 py-2 text-left text-[#64748b] font-medium">方向</th>
              <th className="px-4 py-2 text-right text-[#64748b] font-medium">价格</th>
              <th className="px-4 py-2 text-right text-[#64748b] font-medium">数量</th>
              <th className="px-4 py-2 text-right text-[#64748b] font-medium">金额</th>
              <th className="px-4 py-2 text-right text-[#64748b] font-medium">盈亏</th>
              <th className="px-4 py-2 text-center text-[#64748b] font-medium">来源</th>
              <th className="px-4 py-2 text-center text-[#64748b] font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            {filteredRecords.map(record => (
              <tr
                key={record.id}
                className="border-b border-[rgba(148,163,184,0.05)] hover:bg-[#111827] transition-colors cursor-pointer"
                onClick={() => setSelectedTrade(record)}
              >
                <td className="px-4 py-2 text-[#94a3b8]">{record.tradeTime}</td>
                <td className="px-4 py-2 text-[#e2e8f0] font-mono">{record.stockCode}</td>
                <td className="px-4 py-2 text-[#e2e8f0]">{record.stockName}</td>
                <td className="px-4 py-2">
                  <span className={cn(
                    'px-2 py-0.5 rounded text-xs',
                    record.tradeType === 'buy' ? 'bg-[#22c55e]/20 text-[#22c55e]' : 'bg-[#ef4444]/20 text-[#ef4444]'
                  )}>
                    {record.tradeType === 'buy' ? '买入' : '卖出'}
                  </span>
                </td>
                <td className="px-4 py-2 text-right text-[#e2e8f0] font-mono">{record.tradePrice.toFixed(2)}</td>
                <td className="px-4 py-2 text-right text-[#e2e8f0] font-mono">{record.tradeVolume}</td>
                <td className="px-4 py-2 text-right text-[#e2e8f0] font-mono">{record.tradeAmount.toFixed(0)}</td>
                <td className={cn(
                  'px-4 py-2 text-right font-mono font-medium',
                  record.profitLoss >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'
                )}>
                  {record.profitLoss >= 0 ? '+' : ''}{record.profitLoss.toFixed(0)}
                </td>
                <td className="px-4 py-2 text-center">
                  <span className="px-2 py-0.5 bg-[#1e293b] rounded text-xs text-[#64748b]">
                    {record.source === 'excel' ? 'Excel' : record.source === 'voice' ? '语音' : record.source === 'ocr' ? '截图' : '手动'}
                  </span>
                </td>
                <td className="px-4 py-2 text-center">
                  <div className="flex items-center justify-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedTrade(record);
                      }}
                      className="p-1 text-[#64748b] hover:text-[#c9a84c] transition-colors"
                      title="查看详情"
                    >
                      <Eye size={14} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        window.location.href = `/trade-environment/${record.id}`;
                      }}
                      className="p-1 text-[#64748b] hover:text-[#c9a84c] transition-colors"
                      title="环境重构"
                    >
                      <GitCompare size={14} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteRecord(record.id);
                      }}
                      className="p-1 text-[#64748b] hover:text-[#ef4444] transition-colors"
                      title="删除"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredRecords.length === 0 && (
              <tr>
                <td colSpan={10} className="px-4 py-12 text-center text-[#64748b]">
                  暂无交易记录，请点击"导入交易"或"手动录入"
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 导入弹窗 */}
      <AnimatePresence>
        {showImportModal && (
          <ImportModal
            onClose={() => {
              setShowImportModal(false);
              setImportMethod(null);
            }}
            importMethod={importMethod}
            setImportMethod={setImportMethod}
            onExcelImport={handleExcelImport}
            onVoiceStart={startVoiceInput}
            isRecording={isRecording}
            fileInputRef={fileInputRef}
            imageInputRef={imageInputRef}
          />
        )}
      </AnimatePresence>

      {/* 手动录入弹窗 */}
      <AnimatePresence>
        {showAddModal && (
          <AddTradeModal
            onClose={() => setShowAddModal(false)}
            onAdd={(trade) => {
              addRecord(trade);
              setShowAddModal(false);
            }}
          />
        )}
      </AnimatePresence>

      {/* 交易详情弹窗 */}
      <AnimatePresence>
        {selectedTrade && (
          <TradeDetailModal
            trade={selectedTrade}
            onClose={() => setSelectedTrade(null)}
          />
        )}
      </AnimatePresence>

      {/* 用户画像弹窗 */}
      <AnimatePresence>
        {showProfileModal && (
          <UserProfileModal
            profile={userProfile}
            onClose={() => setShowProfileModal(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ── 统计卡片 ───────────────────────────────────────────────────
interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
}

function StatCard({ label, value, icon }: StatCardProps) {
  return (
    <div className="flex items-center gap-3 p-3 bg-[#1e293b] rounded-lg">
      <div className="p-2 bg-[#0f172a] rounded text-[#c9a84c]">{icon}</div>
      <div>
        <div className="text-xs text-[#64748b]">{label}</div>
        <div className="text-lg font-bold text-[#e2e8f0]">{value}</div>
      </div>
    </div>
  );
}

// ── 导入弹窗 ───────────────────────────────────────────────────
interface ImportModalProps {
  onClose: () => void;
  importMethod: string | null;
  setImportMethod: (method: 'excel' | 'image' | 'voice' | null) => void;
  onExcelImport: (file: File) => void;
  onVoiceStart: () => void;
  isRecording: boolean;
  fileInputRef: React.RefObject<HTMLInputElement>;
  imageInputRef: React.RefObject<HTMLInputElement>;
}

function ImportModal({
  onClose,
  importMethod,
  setImportMethod,
  onExcelImport,
  onVoiceStart,
  isRecording,
  fileInputRef,
  imageInputRef,
}: ImportModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-[500px] bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.2)] overflow-hidden"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
          <h3 className="text-sm font-medium text-[#e2e8f0]">导入交易记录</h3>
          <button onClick={onClose} className="text-[#64748b] hover:text-[#e2e8f0]">
            <X size={16} />
          </button>
        </div>
        <div className="p-6">
          {!importMethod ? (
            <div className="grid grid-cols-2 gap-4">
              <ImportOption
                icon={<FileSpreadsheet size={24} />}
                title="Excel 导入"
                description="支持券商交割单 Excel 文件"
                onClick={() => setImportMethod('excel')}
              />
              <ImportOption
                icon={<Image size={24} />}
                title="截图识别"
                description="上传交易软件截图"
                onClick={() => setImportMethod('image')}
              />
              <ImportOption
                icon={<Mic size={24} />}
                title="语音输入"
                description="语音描述交易内容"
                onClick={() => setImportMethod('voice')}
              />
              <ImportOption
                icon={<Download size={24} />}
                title="下载模板"
                description="获取标准 Excel 模板"
                onClick={() => {
                  // 下载模板逻辑
                  const template = XLSX.utils.json_to_sheet([
                    { '成交日期': '20260522', '成交时间': '09:30:00', '证券代码': '000001', '证券名称': '平安银行', '操作': '买入', '成交价格': 12.50, '成交数量': 100, '手续费': 5 },
                  ]);
                  const wb = XLSX.utils.book_new();
                  XLSX.utils.book_append_sheet(wb, template, '交易记录');
                  XLSX.writeFile(wb, '交易记录模板.xlsx');
                }}
              />
            </div>
          ) : (
            <div className="space-y-4">
              {importMethod === 'excel' && (
                <div>
                  <p className="text-sm text-[#94a3b8] mb-3">请选择 Excel 文件（.xlsx/.xls）</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(_e: React.ChangeEvent<HTMLInputElement>) => {
                      const file = _e.target.files?.[0];
                      if (file) onExcelImport(file);
                    }}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full py-8 border-2 border-dashed border-[rgba(148,163,184,0.2)] rounded-lg text-[#64748b] hover:border-[#c9a84c] hover:text-[#c9a84c] transition-colors"
                  >
                    <FileSpreadsheet size={32} className="mx-auto mb-2" />
                    点击选择 Excel 文件
                  </button>
                </div>
              )}
              {importMethod === 'image' && (
                <div>
                  <p className="text-sm text-[#94a3b8] mb-3">上传交易软件截图（OCR 识别）</p>
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/*"
                    onChange={e => {
                      // TODO: OCR 识别逻辑
                      alert('OCR 识别功能需要后端支持，请使用手动录入');
                    }}
                    className="hidden"
                  />
                  <button
                    onClick={() => imageInputRef.current?.click()}
                    className="w-full py-8 border-2 border-dashed border-[rgba(148,163,184,0.2)] rounded-lg text-[#64748b] hover:border-[#c9a84c] hover:text-[#c9a84c] transition-colors"
                  >
                    <Image size={32} className="mx-auto mb-2" />
                    点击上传图片
                  </button>
                </div>
              )}
              {importMethod === 'voice' && (
                <div className="text-center">
                  <p className="text-sm text-[#94a3b8] mb-4">
                    语音格式示例："买入贵州茅台100股价格1800"
                  </p>
                  <button
                    onClick={onVoiceStart}
                    className={cn(
                      'w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-4 transition-all',
                      isRecording
                        ? 'bg-[#ef4444] animate-pulse'
                        : 'bg-[#1e293b] hover:bg-[#334155]'
                    )}
                  >
                    {isRecording ? <MicOff size={32} className="text-white" /> : <Mic size={32} className="text-[#c9a84c]" />}
                  </button>
                  <p className="text-sm text-[#64748b]">
                    {isRecording ? '正在录音...' : '点击开始录音'}
                  </p>
                </div>
              )}
              <button
                onClick={() => setImportMethod(null)}
                className="w-full py-2 bg-[#1e293b] hover:bg-[#334155] rounded text-sm transition-colors"
              >
                返回
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

// ── 导入选项 ───────────────────────────────────────────────────
interface ImportOptionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}

function ImportOption({ icon, title, description, onClick }: ImportOptionProps) {
  return (
    <button
      onClick={onClick}
      className="p-4 bg-[#1e293b] hover:bg-[#334155] rounded-lg transition-colors text-center"
    >
      <div className="text-[#c9a84c] mb-2 flex justify-center">{icon}</div>
      <div className="text-sm font-medium text-[#e2e8f0]">{title}</div>
      <div className="text-xs text-[#64748b] mt-1">{description}</div>
    </button>
  );
}

// ── 手动录入弹窗 ───────────────────────────────────────────────
interface AddTradeModalProps {
  onClose: () => void;
  onAdd: (trade: TradeRecord) => void;
}

function AddTradeModal({ onClose, onAdd }: AddTradeModalProps) {
  const [form, setForm] = useState({
    tradeDate: new Date().toISOString().split('T')[0],
    tradeTime: new Date().toTimeString().slice(0, 8),
    stockCode: '',
    stockName: '',
    market: 'SZ' as TradeRecord['market'],
    tradeType: 'buy' as TradeRecord['tradeType'],
    tradePrice: '',
    tradeVolume: '',
    fee: '',
    stampTax: '',
    transferFee: '',
    userNote: '',
    tradeLogic: '',
  });

  const handleSubmit = () => {
    if (!form.stockCode || !form.stockName || !form.tradePrice || !form.tradeVolume) {
      alert('请填写必填字段');
      return;
    }
    const price = Number(form.tradePrice);
    const volume = Number(form.tradeVolume);
    const trade: TradeRecord = {
      id: generateId(),
      tradeTime: `${form.tradeDate} ${form.tradeTime}`,
      tradeDate: form.tradeDate,
      stockCode: form.stockCode,
      stockName: form.stockName,
      market: form.market,
      tradeType: form.tradeType,
      orderType: 'limit',
      tradePrice: price,
      tradeVolume: volume,
      tradeAmount: price * volume,
      fee: Number(form.fee) || 0,
      stampTax: Number(form.stampTax) || 0,
      transferFee: Number(form.transferFee) || 0,
      profitLoss: 0,
      positionRatio: 0,
      accountBalance: 0,
      dailyPnL: 0,
      currentHolding: 0,
      orderTime: `${form.tradeDate} ${form.tradeTime}`,
      cancelRecords: [],
      matchStatus: 'full',
      source: 'manual',
      userNote: form.userNote,
      tradeLogic: form.tradeLogic,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    onAdd(trade);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-[600px] max-h-[90vh] bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.2)] overflow-hidden"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
          <h3 className="text-sm font-medium text-[#e2e8f0]">手动录入交易</h3>
          <button onClick={onClose} className="text-[#64748b] hover:text-[#e2e8f0]">
            <X size={16} />
          </button>
        </div>
        <div className="p-4 overflow-y-auto max-h-[70vh] space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <FormField label="交易日期" required>
              <input
                type="date"
                value={form.tradeDate}
                onChange={e => setForm({ ...form, tradeDate: e.target.value })}
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
            <FormField label="交易时间" required>
              <input
                type="time"
                value={form.tradeTime}
                onChange={e => setForm({ ...form, tradeTime: e.target.value })}
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <FormField label="股票代码" required>
              <input
                type="text"
                value={form.stockCode}
                onChange={e => setForm({ ...form, stockCode: e.target.value })}
                placeholder="如: 000001"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
            <FormField label="股票名称" required>
              <input
                type="text"
                value={form.stockName}
                onChange={e => setForm({ ...form, stockName: e.target.value })}
                placeholder="如: 平安银行"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
            <FormField label="市场">
              <select
                value={form.market}
                onChange={e => setForm({ ...form, market: e.target.value as TradeRecord['market'] })}
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              >
                <option value="SZ">深市</option>
                <option value="SH">沪市</option>
                <option value="CYB">创业板</option>
                <option value="KCB">科创板</option>
                <option value="BSE">北交所</option>
              </select>
            </FormField>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <FormField label="方向" required>
              <select
                value={form.tradeType}
                onChange={e => setForm({ ...form, tradeType: e.target.value as TradeRecord['tradeType'] })}
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              >
                <option value="buy">买入</option>
                <option value="sell">卖出</option>
              </select>
            </FormField>
            <FormField label="成交价格" required>
              <input
                type="number"
                step="0.01"
                value={form.tradePrice}
                onChange={e => setForm({ ...form, tradePrice: e.target.value })}
                placeholder="0.00"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
            <FormField label="成交数量" required>
              <input
                type="number"
                value={form.tradeVolume}
                onChange={e => setForm({ ...form, tradeVolume: e.target.value })}
                placeholder="0"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <FormField label="手续费">
              <input
                type="number"
                step="0.01"
                value={form.fee}
                onChange={e => setForm({ ...form, fee: e.target.value })}
                placeholder="0.00"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
            <FormField label="印花税">
              <input
                type="number"
                step="0.01"
                value={form.stampTax}
                onChange={e => setForm({ ...form, stampTax: e.target.value })}
                placeholder="0.00"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
            <FormField label="过户费">
              <input
                type="number"
                step="0.01"
                value={form.transferFee}
                onChange={e => setForm({ ...form, transferFee: e.target.value })}
                placeholder="0.00"
                className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0]"
              />
            </FormField>
          </div>
          <FormField label="交易备注">
            <textarea
              value={form.userNote}
              onChange={e => setForm({ ...form, userNote: e.target.value })}
              placeholder="记录这笔交易的备注..."
              rows={2}
              className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0] resize-none"
            />
          </FormField>
          <FormField label="下单思路">
            <textarea
              value={form.tradeLogic}
              onChange={e => setForm({ ...form, tradeLogic: e.target.value })}
              placeholder="记录当时的决策逻辑..."
              rows={2}
              className="w-full bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-3 py-2 text-sm text-[#e2e8f0] resize-none"
            />
          </FormField>
        </div>
        <div className="flex justify-end gap-2 px-4 py-3 border-t border-[rgba(148,163,184,0.1)]">
          <button onClick={onClose} className="px-4 py-2 bg-[#334155] rounded text-sm">
            取消
          </button>
          <button onClick={handleSubmit} className="px-4 py-2 bg-[#c9a84c] text-[#0d1526] rounded text-sm font-medium">
            确认添加
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── 表单字段 ───────────────────────────────────────────────────
interface FormFieldProps {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}

function FormField({ label, required, children }: FormFieldProps) {
  return (
    <div>
      <label className="block text-xs text-[#64748b] mb-1">
        {label}
        {required && <span className="text-[#ef4444] ml-1">*</span>}
      </label>
      {children}
    </div>
  );
}

// ── 交易详情弹窗 ───────────────────────────────────────────────
interface TradeDetailModalProps {
  trade: TradeRecord;
  onClose: () => void;
}

function TradeDetailModal({ trade, onClose }: TradeDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-[700px] max-h-[90vh] bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.2)] overflow-hidden"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
          <h3 className="text-sm font-medium text-[#e2e8f0]">
            交易详情 - {trade.stockName}({trade.stockCode})
          </h3>
          <button onClick={onClose} className="text-[#64748b] hover:text-[#e2e8f0]">
            <X size={16} />
          </button>
        </div>
        <div className="p-4 overflow-y-auto max-h-[70vh]">
          <div className="grid grid-cols-3 gap-4 mb-4">
            <DetailItem label="交易时间" value={trade.tradeTime} />
            <DetailItem label="交易方向" value={trade.tradeType === 'buy' ? '买入' : '卖出'} />
            <DetailItem label="市场" value={getMarketLabel(trade.market)} />
            <DetailItem label="成交价格" value={trade.tradePrice.toFixed(2)} />
            <DetailItem label="成交数量" value={trade.tradeVolume} />
            <DetailItem label="成交金额" value={trade.tradeAmount.toFixed(2)} />
            <DetailItem label="手续费" value={trade.fee.toFixed(2)} />
            <DetailItem label="印花税" value={trade.stampTax.toFixed(2)} />
            <DetailItem label="过户费" value={trade.transferFee.toFixed(2)} />
          </div>
          {trade.userNote && (
            <div className="mb-4 p-3 bg-[#1e293b] rounded">
              <div className="text-xs text-[#64748b] mb-1">备注</div>
              <div className="text-sm text-[#e2e8f0]">{trade.userNote}</div>
            </div>
          )}
          {trade.tradeLogic && (
            <div className="mb-4 p-3 bg-[#1e293b] rounded">
              <div className="text-xs text-[#64748b] mb-1">下单思路</div>
              <div className="text-sm text-[#e2e8f0]">{trade.tradeLogic}</div>
            </div>
          )}
          <button
            onClick={() => {
              window.location.href = `/trade-environment/${trade.id}`;
            }}
            className="w-full py-2 bg-[#c9a84c] text-[#0d1526] rounded text-sm font-medium hover:bg-[#b8943f] transition-colors"
          >
            重构完整交易环境
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ── 详情项 ─────────────────────────────────────────────────────
interface DetailItemProps {
  label: string;
  value: string | number;
}

function DetailItem({ label, value }: DetailItemProps) {
  return (
    <div className="p-2 bg-[#1e293b] rounded">
      <div className="text-xs text-[#64748b]">{label}</div>
      <div className="text-sm text-[#e2e8f0] font-mono">{value}</div>
    </div>
  );
}

// ── 用户画像弹窗 ───────────────────────────────────────────────
interface UserProfileModalProps {
  profile: UserProfile;
  onClose: () => void;
}

function UserProfileModal({ profile, onClose }: UserProfileModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-[700px] max-h-[90vh] bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.2)] overflow-hidden"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
          <h3 className="text-sm font-medium text-[#e2e8f0]">用户画像分析</h3>
          <button onClick={onClose} className="text-[#64748b] hover:text-[#e2e8f0]">
            <X size={16} />
          </button>
        </div>
        <div className="p-4 overflow-y-auto max-h-[70vh]">
          {/* 概览 */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            <StatCard label="总交易" value={profile.totalTrades} icon={<BarChart3 size={16} />} />
            <StatCard label="胜率" value={`${profile.winRate.toFixed(1)}%`} icon={<BarChart3 size={16} />} />
            <StatCard label="平均盈利" value={profile.avgProfit.toFixed(0)} icon={<TrendingUp size={16} className="text-[#22c55e]" />} />
            <StatCard label="平均亏损" value={profile.avgLoss.toFixed(0)} icon={<TrendingDown size={16} className="text-[#ef4444]" />} />
          </div>

          {/* 高频错误 */}
          {profile.highFreqErrors.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-[#ef4444] mb-2 flex items-center gap-2">
                <AlertTriangle size={16} />
                高频交易错误
              </h4>
              <div className="space-y-2">
                {profile.highFreqErrors.map((error, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-[#1e293b] rounded">
                    <div>
                      <div className="text-sm text-[#e2e8f0]">{error.errorType}</div>
                      <div className="text-xs text-[#64748b]">{error.description}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-[#ef4444]">{error.count}次</div>
                      <div className="text-xs text-[#64748b]">亏损{Math.abs(error.totalLoss).toFixed(0)}元</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 时段偏好 */}
          {profile.preferredTimeSlots.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-[#e2e8f0] mb-2">时段交易偏好</h4>
              <div className="grid grid-cols-4 gap-2">
                {profile.preferredTimeSlots.map((slot, i) => (
                  <div key={i} className="p-2 bg-[#1e293b] rounded text-center">
                    <div className="text-xs text-[#64748b]">{slot.timeSlot}</div>
                    <div className="text-sm text-[#e2e8f0]">{slot.tradeCount}笔</div>
                    <div className={cn(
                      'text-xs',
                      slot.winRate >= 50 ? 'text-[#22c55e]' : 'text-[#ef4444]'
                    )}>
                      胜率{slot.winRate.toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="p-3 bg-[#1e293b] rounded">
            <div className="text-xs text-[#64748b] mb-1">交易习惯总结</div>
            <div className="text-sm text-[#e2e8f0]">{profile.tradeHabitSummary}</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}