import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { cn } from '@/lib/utils';

const pathTitleMap: Record<string, string> = {
  '/': '首页总览',
  '/sentiment': '市场情绪',
  '/intraday': '盘中监控',
  '/yingyou': '游资诊断',
  '/tactics': '战法选股',
  '/scoring': '评分决策',
  '/diagnosis': '交割单诊断',
};

function getMarketStatus(): { label: string; color: string } {
  const hour = new Date().getHours();
  const minute = new Date().getMinutes();
  const time = hour * 60 + minute;

  if ((time >= 570 && time <= 690) || (time >= 780 && time <= 900)) {
    return { label: '交易中', color: 'bg-[#22c55e]' };
  } else if (time < 570) {
    return { label: '盘前', color: 'bg-[#3b82f6]' };
  } else {
    return { label: '已收盘', color: 'bg-[#6b7280]' };
  }
}

export default function TopBar() {
  const location = useLocation();
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const marketStatus = getMarketStatus();
  const title = pathTitleMap[location.pathname] || '首页总览';

  const timeStr = time.toLocaleTimeString('zh-CN', { hour12: false });
  const dateStr = time.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' });

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-[#0d1526]/80 backdrop-blur-xl border-b border-[rgba(148,163,184,0.1)] z-40 flex items-center justify-between px-6">
      {/* Left: Title + breadcrumb */}
      <div className="flex items-center gap-3">
        <h1 className="text-[18px] font-semibold text-[#f1f5f9] font-orbitron tracking-wide">{title}</h1>
        <span className="text-[#475569]">/</span>
        <span className="text-[13px] text-[#94a3b8]">Dashboard</span>
      </div>

      {/* Center: Market status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0f1929] border border-[rgba(148,163,184,0.1)]">
          <span className={cn('w-2 h-2 rounded-full', marketStatus.color)} />
          <span className="text-[12px] text-[#94a3b8]">{marketStatus.label}</span>
        </div>
      </div>

      {/* Right: DateTime + notification */}
      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className="text-[13px] text-[#f1f5f9] font-mono">{timeStr}</div>
          <div className="text-[11px] text-[#475569]">{dateStr}</div>
        </div>
        <button className="relative p-2 rounded-lg hover:bg-[#141e33] transition-colors">
          <Bell size={18} className="text-[#94a3b8]" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#ef4444] rounded-full" />
        </button>
      </div>
    </header>
  );
}
