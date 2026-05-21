// ═══════════════════════════════════════════════════════════════
//  全域多维度战法诊股 - 诊断报告UI组件
// ═══════════════════════════════════════════════════════════════

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  AlertTriangle,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Target,
  TrendingUp,
  Brain,
  Shield,
  Scale,
  Clock,
  MapPin,
  Newspaper,
  DollarSign,
  Building,
  Repeat,
  BarChart3,
  Lightbulb,
  BookOpen,
  AlertOctagon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type {
  FullDiagnosisReport,
  DiagnosisIssue,
  DiagnosisDimension,
  DimensionDiagnosis,
  IssueSeverity,
  IssueRootCause,
} from '@/types/diagnosis';
import {
  DIMENSION_CONFIG,
  SCORE_GRADE_CONFIG,
} from '@/types/diagnosis';

// ── 工具函数 ───────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<IssueSeverity, {
  label: string;
  color: string;
  bgColor: string;
  icon: React.ReactNode;
}> = {
  critical: {
    label: '严重失误',
    color: 'text-[#ef4444]',
    bgColor: 'bg-[#ef4444]/10 border-[#ef4444]/30',
    icon: <AlertOctagon size={14} />,
  },
  moderate: {
    label: '中度瑕疵',
    color: 'text-[#f59e0b]',
    bgColor: 'bg-[#f59e0b]/10 border-[#f59e0b]/30',
    icon: <AlertTriangle size={14} />,
  },
  minor: {
    label: '细微不足',
    color: 'text-[#3b82f6]',
    bgColor: 'bg-[#3b82f6]/10 border-[#3b82f6]/30',
    icon: <Info size={14} />,
  },
};

const ROOT_CAUSE_CONFIG: Record<IssueRootCause, {
  label: string;
  color: string;
}> = {
  objective_market: { label: '客观行情', color: 'text-[#64748b]' },
  psychology_bias: { label: '心态偏差', color: 'text-[#f97316]' },
  discipline_failure: { label: '纪律问题', color: 'text-[#a855f7]' },
  cognitive_gap: { label: '认知不足', color: 'text-[#3b82f6]' },
  planning_missing: { label: '规划缺失', color: 'text-[#ef4444]' },
};

// ── 主组件 ─────────────────────────────────────────────────────

interface DiagnosisReportProps {
  report: FullDiagnosisReport;
  onClose: () => void;
}

export default function DiagnosisReport({ report, onClose }: DiagnosisReportProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'issues' | 'dimensions' | 'plan'>('overview');
  const [expandedIssue, setExpandedIssue] = useState<string | null>(null);
  const [filterDimension, setFilterDimension] = useState<DiagnosisDimension | 'all'>('all');
  const [filterSeverity, setFilterSeverity] = useState<IssueSeverity | 'all'>('all');

  const gradeConfig = SCORE_GRADE_CONFIG[report.scoreGrade];

  const filteredIssues = report.allIssues.filter(issue => {
    if (filterDimension !== 'all' && issue.dimension !== filterDimension) return false;
    if (filterSeverity !== 'all' && issue.severity !== filterSeverity) return false;
    return true;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-[95vw] max-w-6xl max-h-[90vh] bg-[#0f172a] rounded-xl border border-[rgba(148,163,184,0.2)] overflow-hidden flex flex-col"
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(148,163,184,0.1)] bg-[#111827]">
          <div>
            <h2 className="text-lg font-bold text-[#c9a84c] flex items-center gap-2">
              <Target size={20} />
              全域多维度战法诊股报告
            </h2>
            <p className="text-xs text-[#64748b] mt-1">
              {report.tradeInfo.stockName}({report.tradeInfo.stockCode}) | {report.tradeInfo.tradeTime}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-[#1e293b] rounded-lg transition-colors text-[#64748b] hover:text-[#e2e8f0]"
          >
            <X size={18} />
          </button>
        </div>

        {/* 评分总览 */}
        <ScoreOverview report={report} gradeConfig={gradeConfig} />

        {/* Tab 导航 */}
        <div className="flex items-center gap-1 px-4 py-2 border-b border-[rgba(148,163,184,0.1)] bg-[#0f172a]">
          {[
            { id: 'overview' as const, label: '综合总览', icon: <BarChart3 size={14} /> },
            { id: 'issues' as const, label: `问题清单 (${report.allIssues.length})`, icon: <AlertTriangle size={14} /> },
            { id: 'dimensions' as const, label: '维度详情', icon: <BookOpen size={14} /> },
            { id: 'plan' as const, label: '优化方案', icon: <Lightbulb size={14} /> },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors',
                activeTab === tab.id
                  ? 'bg-[#1e293b] text-[#c9a84c]'
                  : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b]'
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* 内容区 */}
        <div className="flex-1 overflow-y-auto p-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {activeTab === 'overview' && <OverviewTab report={report} />}
              {activeTab === 'issues' && (
                <IssuesTab
                  issues={filteredIssues}
                  filterDimension={filterDimension}
                  filterSeverity={filterSeverity}
                  onFilterDimensionChange={setFilterDimension}
                  onFilterSeverityChange={setFilterSeverity}
                  expandedIssue={expandedIssue}
                  onExpandIssue={setExpandedIssue}
                />
              )}
              {activeTab === 'dimensions' && <DimensionsTab dimensions={report.dimensions} />}
              {activeTab === 'plan' && <PlanTab report={report} />}
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}

// ── 评分总览 ───────────────────────────────────────────────────

interface ScoreOverviewProps {
  report: FullDiagnosisReport;
  gradeConfig: { label: string; color: string };
}

function ScoreOverview({ report, gradeConfig }: ScoreOverviewProps) {
  const scoreColor = gradeConfig.color;
  
  return (
    <div className="px-6 py-4 bg-gradient-to-r from-[#111827] to-[#1e293b] border-b border-[rgba(148,163,184,0.1)]">
      <div className="flex items-center gap-6">
        {/* 分数圆环 */}
        <div className="relative w-20 h-20 flex-shrink-0">
          <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="35" fill="none" stroke="#1e293b" strokeWidth="6" />
            <circle
              cx="40"
              cy="40"
              r="35"
              fill="none"
              stroke={scoreColor}
              strokeWidth="6"
              strokeDasharray={`${report.overallScore * 2.2} 220`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold" style={{ color: scoreColor }}>{report.overallScore}</span>
            <span className="text-[10px] text-[#64748b]">分</span>
          </div>
        </div>

        {/* 等级和统计 */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-lg font-bold" style={{ color: scoreColor }}>{gradeConfig.label}</span>
            <span className="text-xs text-[#64748b]">|</span>
            <span className="text-xs text-[#64748b]">{report.summary}</span>
          </div>
          <div className="flex items-center gap-4">
            <StatBadge label="严重" count={report.criticalCount} color="text-[#ef4444]" bgColor="bg-[#ef4444]/10" />
            <StatBadge label="中度" count={report.moderateCount} color="text-[#f59e0b]" bgColor="bg-[#f59e0b]/10" />
            <StatBadge label="轻微" count={report.minorCount} color="text-[#3b82f6]" bgColor="bg-[#3b82f6]/10" />
            <StatBadge label="亮点" count={report.allHighlights.length} color="text-[#22c55e]" bgColor="bg-[#22c55e]/10" />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatBadge({ label, count, color, bgColor }: { label: string; count: number; color: string; bgColor: string }) {
  return (
    <div className={cn('flex items-center gap-1.5 px-2 py-1 rounded text-xs', bgColor)}>
      <span className={cn('font-medium', color)}>{count}</span>
      <span className="text-[#64748b]">{label}</span>
    </div>
  );
}

// ── 综合总览 Tab ───────────────────────────────────────────────

function OverviewTab({ report }: { report: FullDiagnosisReport }) {
  return (
    <div className="space-y-4">
      {/* 维度得分雷达 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3 flex items-center gap-2">
          <BarChart3 size={16} />
          各维度得分一览
        </h3>
        <div className="grid grid-cols-7 gap-2">
          {report.dimensions.map(dim => {
            const config = DIMENSION_CONFIG[dim.dimension];
            const scoreColor = dim.score >= 80 ? '#22c55e' : dim.score >= 60 ? '#f59e0b' : '#ef4444';
            return (
              <div key={dim.dimension} className="text-center p-2 bg-[#1e293b] rounded">
                <div className="text-lg mb-1">{config.icon}</div>
                <div className="text-xs text-[#64748b] truncate">{config.label}</div>
                <div className="text-lg font-bold mt-1" style={{ color: scoreColor }}>{dim.score}</div>
                <div className="w-full h-1.5 bg-[#0f172a] rounded-full mt-1 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${dim.score}%`, backgroundColor: scoreColor }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 亮点展示 */}
      {report.allHighlights.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(34,197,94,0.2)]">
          <h3 className="text-sm font-medium text-[#22c55e] mb-3 flex items-center gap-2">
            <CheckCircle size={16} />
            操作亮点
          </h3>
          <div className="space-y-2">
            {report.allHighlights.map((h, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-[#22c55e]">
                <CheckCircle size={14} className="mt-0.5 shrink-0" />
                {h}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 严重问题预警 */}
      {report.criticalCount > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(239,68,68,0.3)]">
          <h3 className="text-sm font-medium text-[#ef4444] mb-3 flex items-center gap-2">
            <AlertOctagon size={16} />
            严重问题预警
          </h3>
          <div className="space-y-2">
            {report.allIssues.filter(i => i.severity === 'critical').map(issue => (
              <div key={issue.id} className="flex items-start gap-2 text-sm text-[#ef4444]">
                <AlertTriangle size={14} className="mt-0.5 shrink-0" />
                <span className="font-medium">[{issue.dimensionLabel}]</span>
                <span>{issue.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 陋习提示 */}
      {report.badHabits.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(217,70,239,0.2)]">
          <h3 className="text-sm font-medium text-[#d946ef] mb-3 flex items-center gap-2">
            <Repeat size={16} />
            交易陋习警示
          </h3>
          <div className="space-y-2">
            {report.badHabits.slice(0, 3).map((habit, i) => (
              <div key={i} className="p-2 bg-[#1e293b] rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-[#e2e8f0] font-medium">{habit.habit}</span>
                  <span className="text-xs text-[#d946ef]">出现{habit.frequency}次</span>
                </div>
                <div className="text-xs text-[#64748b]">{habit.correction}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── 问题清单 Tab ───────────────────────────────────────────────

interface IssuesTabProps {
  issues: DiagnosisIssue[];
  filterDimension: DiagnosisDimension | 'all';
  filterSeverity: IssueSeverity | 'all';
  onFilterDimensionChange: (d: DiagnosisDimension | 'all') => void;
  onFilterSeverityChange: (s: IssueSeverity | 'all') => void;
  expandedIssue: string | null;
  onExpandIssue: (id: string | null) => void;
}

function IssuesTab({
  issues,
  filterDimension,
  filterSeverity,
  onFilterDimensionChange,
  onFilterSeverityChange,
  expandedIssue,
  onExpandIssue,
}: IssuesTabProps) {
  return (
    <div className="space-y-3">
      {/* 筛选器 */}
      <div className="flex items-center gap-3 p-3 bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.1)]">
        <span className="text-xs text-[#64748b]">筛选：</span>
        <select
          value={filterDimension}
          onChange={e => onFilterDimensionChange(e.target.value as DiagnosisDimension | 'all')}
          className="px-2 py-1 bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded text-xs text-[#e2e8f0]"
        >
          <option value="all">全部维度</option>
          {(Object.keys(DIMENSION_CONFIG) as DiagnosisDimension[]).map(d => (
            <option key={d} value={d}>{DIMENSION_CONFIG[d].label}</option>
          ))}
        </select>
        <select
          value={filterSeverity}
          onChange={e => onFilterSeverityChange(e.target.value as IssueSeverity | 'all')}
          className="px-2 py-1 bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded text-xs text-[#e2e8f0]"
        >
          <option value="all">全部等级</option>
          <option value="critical">严重失误</option>
          <option value="moderate">中度瑕疵</option>
          <option value="minor">细微不足</option>
        </select>
        <span className="text-xs text-[#64748b] ml-auto">共 {issues.length} 条问题</span>
      </div>

      {/* 问题列表 */}
      {issues.length === 0 ? (
        <div className="text-center py-12 text-[#64748b]">
          <CheckCircle size={48} className="mx-auto mb-3 text-[#22c55e]" />
          <p>暂无问题，操作良好！</p>
        </div>
      ) : (
        <div className="space-y-2">
          {issues.map(issue => (
            <IssueCard
              key={issue.id}
              issue={issue}
              isExpanded={expandedIssue === issue.id}
              onToggle={() => onExpandIssue(expandedIssue === issue.id ? null : issue.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── 问题卡片 ───────────────────────────────────────────────────

interface IssueCardProps {
  issue: DiagnosisIssue;
  isExpanded: boolean;
  onToggle: () => void;
}

function IssueCard({ issue, isExpanded, onToggle }: IssueCardProps) {
  const sevConfig = SEVERITY_CONFIG[issue.severity];
  const causeConfig = ROOT_CAUSE_CONFIG[issue.rootCause];
  const dimConfig = DIMENSION_CONFIG[issue.dimension];

  return (
    <div className={cn(
      'rounded-lg border overflow-hidden transition-all',
      isExpanded ? sevConfig.bgColor : 'bg-[#111827] border-[rgba(148,163,184,0.1)]'
    )}>
      {/* 头部 */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-[#1e293b]/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={cn('flex items-center gap-1 px-2 py-0.5 rounded text-xs', sevConfig.bgColor, sevConfig.color)}>
            {sevConfig.icon}
            {sevConfig.label}
          </span>
          <span className="text-xs text-[#64748b] px-2 py-0.5 bg-[#1e293b] rounded">
            {dimConfig.icon} {issue.dimensionLabel}
          </span>
          <span className="text-sm text-[#e2e8f0] font-medium">{issue.title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn('text-xs', causeConfig.color)}>{causeConfig.label}</span>
          {isExpanded ? <ChevronUp size={16} className="text-[#64748b]" /> : <ChevronDown size={16} className="text-[#64748b]" />}
        </div>
      </button>

      {/* 展开详情 */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-[rgba(148,163,184,0.1)]"
          >
            <div className="p-4 space-y-3">
              {/* 问题描述 */}
              <div>
                <div className="text-xs text-[#64748b] mb-1">问题描述</div>
                <div className="text-sm text-[#e2e8f0]">{issue.description}</div>
              </div>

              {/* 证据 */}
              <div>
                <div className="text-xs text-[#64748b] mb-1">证据依据</div>
                <div className="text-sm text-[#c9a84c] font-mono">{issue.evidence}</div>
              </div>

              {/* 散户通病 */}
              <div>
                <div className="text-xs text-[#64748b] mb-1">散户高频错误</div>
                <div className="text-sm text-[#f59e0b]">{issue.commonError}</div>
              </div>

              {/* 改进建议 */}
              <div className="p-3 bg-[#1e293b] rounded">
                <div className="text-xs text-[#64748b] mb-1">改进建议</div>
                <div className="text-sm text-[#22c55e]">{issue.suggestion}</div>
              </div>

              {/* 标准操作 */}
              <div className="p-3 bg-[#1e293b] rounded">
                <div className="text-xs text-[#64748b] mb-1">标准操作方式</div>
                <div className="text-sm text-[#3b82f6]">{issue.standardOperation}</div>
              </div>

              {/* 根源归类 */}
              <div className="flex items-center gap-2 text-xs">
                <span className="text-[#64748b]">问题根源：</span>
                <span className={cn('px-2 py-0.5 rounded', causeConfig.color)}>
                  {causeConfig.label}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── 维度详情 Tab ───────────────────────────────────────────────

function DimensionsTab({ dimensions }: { dimensions: DimensionDiagnosis[] }) {
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  return (
    <div className="space-y-2">
      {dimensions.map(dim => {
        const config = DIMENSION_CONFIG[dim.dimension];
        const scoreColor = dim.score >= 80 ? '#22c55e' : dim.score >= 60 ? '#f59e0b' : '#ef4444';
        const isExpanded = expandedDim === dim.dimension;

        return (
          <div
            key={dim.dimension}
            className={cn(
              'rounded-lg border overflow-hidden transition-all',
              isExpanded ? 'bg-[#111827] border-[rgba(148,163,184,0.2)]' : 'bg-[#111827] border-[rgba(148,163,184,0.1)]'
            )}
          >
            <button
              onClick={() => setExpandedDim(isExpanded ? null : dim.dimension)}
              className="w-full flex items-center justify-between p-3 hover:bg-[#1e293b]/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-lg" style={{ color: config.color }}>{config.icon}</span>
                <span className="text-sm text-[#e2e8f0] font-medium">{config.label}</span>
                {dim.issues.length > 0 && (
                  <span className="text-xs text-[#ef4444]">{dim.issues.length}个问题</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold" style={{ color: scoreColor }}>{dim.score}</span>
                <span className="text-xs text-[#64748b]">分</span>
                {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
            </button>

            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-[rgba(148,163,184,0.1)]"
                >
                  <div className="p-4 space-y-3">
                    {/* 维度总结 */}
                    <div className="text-sm text-[#e2e8f0]">{dim.summary}</div>

                    {/* 亮点 */}
                    {dim.highlights.length > 0 && (
                      <div className="space-y-1">
                        {dim.highlights.map((h, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-[#22c55e]">
                            <CheckCircle size={14} />
                            {h}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* 问题 */}
                    {dim.issues.map(issue => {
                      const sevConfig = SEVERITY_CONFIG[issue.severity];
                      return (
                        <div key={issue.id} className="p-2 bg-[#1e293b] rounded">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={cn('text-xs', sevConfig.color)}>{sevConfig.label}</span>
                            <span className="text-sm text-[#e2e8f0]">{issue.title}</span>
                          </div>
                          <div className="text-xs text-[#64748b]">{issue.suggestion}</div>
                        </div>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

// ── 优化方案 Tab ───────────────────────────────────────────────

function PlanTab({ report }: { report: FullDiagnosisReport }) {
  return (
    <div className="space-y-4">
      {/* 立即修正 */}
      {report.optimizationPlan.immediate.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(239,68,68,0.2)]">
          <h3 className="text-sm font-medium text-[#ef4444] mb-3 flex items-center gap-2">
            <AlertOctagon size={16} />
            立即修正（紧急）
          </h3>
          <div className="space-y-2">
            {report.optimizationPlan.immediate.map((item, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-[#e2e8f0]">
                <span className="w-5 h-5 rounded-full bg-[#ef4444]/20 text-[#ef4444] flex items-center justify-center text-xs shrink-0">
                  {i + 1}
                </span>
                {item}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 短期改进 */}
      {report.optimizationPlan.shortTerm.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(245,158,11,0.2)]">
          <h3 className="text-sm font-medium text-[#f59e0b] mb-3 flex items-center gap-2">
            <AlertTriangle size={16} />
            短期改进（1-2周）
          </h3>
          <div className="space-y-2">
            {report.optimizationPlan.shortTerm.map((item, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-[#e2e8f0]">
                <span className="w-5 h-5 rounded-full bg-[#f59e0b]/20 text-[#f59e0b] flex items-center justify-center text-xs shrink-0">
                  {i + 1}
                </span>
                {item}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 长期养成 */}
      {report.optimizationPlan.longTerm.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(59,130,246,0.2)]">
          <h3 className="text-sm font-medium text-[#3b82f6] mb-3 flex items-center gap-2">
            <Lightbulb size={16} />
            长期养成（持续）
          </h3>
          <div className="space-y-2">
            {report.optimizationPlan.longTerm.map((item, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-[#e2e8f0]">
                <span className="w-5 h-5 rounded-full bg-[#3b82f6]/20 text-[#3b82f6] flex items-center justify-center text-xs shrink-0">
                  {i + 1}
                </span>
                {item}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 陋习规避 */}
      {report.badHabits.length > 0 && (
        <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(217,70,239,0.2)]">
          <h3 className="text-sm font-medium text-[#d946ef] mb-3 flex items-center gap-2">
            <Repeat size={16} />
            陋习规避指南
          </h3>
          <div className="space-y-3">
            {report.badHabits.map((habit, i) => (
              <div key={i} className="p-3 bg-[#1e293b] rounded">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[#e2e8f0] font-medium">{habit.habit}</span>
                  <span className="text-xs text-[#d946ef]">累计{habit.frequency}次</span>
                </div>
                <div className="text-xs text-[#64748b] mb-2">影响：{habit.impact}</div>
                <div className="p-2 bg-[#0f172a] rounded text-xs text-[#22c55e]">
                  改正方法：{habit.correction}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 交易心法 */}
      <div className="p-4 bg-[#111827] rounded-lg border border-[rgba(201,168,76,0.2)]">
        <h3 className="text-sm font-medium text-[#c9a84c] mb-3 flex items-center gap-2">
          <BookOpen size={16} />
          交易心法提醒
        </h3>
        <div className="grid grid-cols-2 gap-3">
          {[
            '计划你的交易，交易你的计划',
            '止损是生存的第一法则',
            '不赚认知以外的钱',
            '控制仓位就是控制风险',
            '顺势而为，逆势而亡',
            '耐心等待，果断执行',
          ].map((rule, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-[#e2e8f0]">
              <span className="w-5 h-5 rounded-full bg-[#c9a84c]/20 text-[#c9a84c] flex items-center justify-center text-xs shrink-0">
                {i + 1}
              </span>
              {rule}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}