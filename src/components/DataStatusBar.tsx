import { motion } from 'framer-motion';
import type { DataStatus } from '@/data/mockData';

interface DataStatusBarProps {
  status: DataStatus;
}

export default function DataStatusBar({ status }: DataStatusBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 1.8, duration: 0.5 }}
      className="w-full h-8 flex items-center justify-between px-4 text-[11px]"
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-pulse-dot absolute inline-flex h-full w-full rounded-full bg-[#22c55e] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22c55e]" />
          </span>
          <span className="text-[#94a3b8]">iFind实时连接中</span>
          <span className="text-[#475569]">最后更新: {status.lastUpdate}</span>
        </div>
        <span className="text-[#475569]">延迟: {status.delay}</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-[#475569]">
          已分析股票: <span className="text-[#94a3b8]">{status.analyzedCount.toLocaleString()}只</span>
          {' | '}
          触发信号: <span className="text-[#94a3b8]">{status.signalCount}次</span>
          {' | '}
          生成交易计划: <span className="text-[#94a3b8]">{status.planCount}份</span>
        </span>
        <span className="text-[#334155]">AI交易智能体 {status.version}</span>
      </div>
    </motion.div>
  );
}
