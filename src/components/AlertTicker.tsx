import { cn } from '@/lib/utils';
import type { AlertMessage } from '@/data/mockData';

interface AlertTickerProps {
  messages: AlertMessage[];
}

const typeStyles = {
  '机会': 'bg-[#c9a84c]/20 text-[#c9a84c] border-[#c9a84c]/30',
  '风险': 'bg-[#ef4444]/20 text-[#ef4444] border-[#ef4444]/30',
  '提示': 'bg-[#3b82f6]/20 text-[#3b82f6] border-[#3b82f6]/30',
};

export default function AlertTicker({ messages }: AlertTickerProps) {
  const doubled = [...messages, ...messages];

  return (
    <div className="w-full h-10 bg-[#0d1526] border-y border-[rgba(148,163,184,0.1)] overflow-hidden flex items-center hover:[&_div]:animation-play-state-paused">
      <div className="flex animate-ticker-scroll whitespace-nowrap">
        {doubled.map((msg, i) => (
          <div key={i} className="inline-flex items-center gap-2 px-6">
            <span className="font-mono text-[11px] text-[#475569]">[{msg.time}]</span>
            <span className={cn('px-1.5 py-0.5 rounded text-[10px] border', typeStyles[msg.type])}>
              {msg.type}
            </span>
            <span className="text-[12px] text-[#94a3b8]">{msg.content}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
