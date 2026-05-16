import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import type { TopStock } from '@/data/mockData';

interface StockRowProps {
  stock: TopStock;
  delay?: number;
  onClick?: (code: string) => void;
}

const actionMap = {
  intervene: { label: '介入', className: 'bg-[#ef4444] text-white' },
  observe: { label: '观察', className: 'bg-[#f97316] text-black' },
  hold: { label: '持有', className: 'bg-[#c9a84c] text-black' },
};

const rankColors = [
  'bg-[#c9a84c] text-[#060b14]',
  'bg-[#94a3b8] text-[#060b14]',
  'bg-[#b87333] text-[#060b14]',
  'bg-[#141e33] text-[#94a3b8]',
  'bg-[#141e33] text-[#94a3b8]',
];

function MiniScoreRing({ score }: { score: number }) {
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    const duration = 1500;
    const start = performance.now();
    const animate = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimated(Math.round(score * eased));
      if (t < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  const diameter = 40;
  const strokeWidth = 3.5;
  const radius = (diameter - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = animated / 100;
  const color = score >= 90 ? '#c9a84c' : score >= 75 ? '#22c55e' : score >= 60 ? '#eab308' : '#ef4444';

  return (
    <svg width={diameter} height={diameter} className="transform -rotate-90">
      <circle cx={diameter / 2} cy={diameter / 2} r={radius} fill="none" stroke="#141e33" strokeWidth={strokeWidth} />
      <circle
        cx={diameter / 2} cy={diameter / 2} r={radius}
        fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round"
        strokeDasharray={circumference} strokeDashoffset={circumference * (1 - progress)}
        style={{ transition: 'stroke-dashoffset 100ms ease-out' }}
      />
      <text x={diameter / 2} y={diameter / 2} textAnchor="middle" dominantBaseline="central"
        fill={color} fontSize={11} fontWeight="700" fontFamily="'JetBrains Mono', monospace"
        transform={`rotate(90 ${diameter / 2} ${diameter / 2})`}
      >
        {animated}
      </text>
    </svg>
  );
}

export default function StockRow({ stock, delay = 0, onClick }: StockRowProps) {
  const action = actionMap[stock.action];

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{
        duration: 0.4,
        delay: delay / 1000,
        ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
      }}
      onClick={() => onClick?.(stock.code)}
      className={cn(
        'flex items-center gap-3 py-2.5 px-3 rounded-md cursor-pointer',
        'transition-all duration-200',
        'hover:bg-[#141e33] hover:translate-x-1',
        'relative group'
      )}
    >
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-0 bg-[#c9a84c] rounded-full transition-all duration-200 group-hover:h-6" />

      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{
          type: 'spring',
          stiffness: 300,
          damping: 15,
          delay: delay / 1000 + 0.1,
        }}
        className={cn(
          'w-7 h-7 rounded-full flex items-center justify-center text-[13px] font-mono font-bold shrink-0',
          rankColors[stock.rank - 1]
        )}
      >
        {stock.rank}
      </motion.div>

      <div className="min-w-[80px]">
        <div className="font-mono text-[11px] text-[#475569]">{stock.code}</div>
        <div className="text-[14px] text-[#f1f5f9] font-medium leading-tight">{stock.name}</div>
      </div>

      <div className="flex flex-wrap gap-1 flex-1">
        {stock.signals.map((s) => (
          <span
            key={s}
            className="px-1.5 py-0.5 rounded-full text-[10px] border border-[#8b5cf6]/40 text-[#8b5cf6] bg-[#8b5cf6]/10"
          >
            {s}
          </span>
        ))}
      </div>

      <div className="shrink-0">
        <MiniScoreRing score={stock.score} />
      </div>

      <span className="px-2 py-0.5 rounded-full text-[10px] border border-[#c9a84c]/40 text-[#c9a84c] bg-[#c9a84c]/10 whitespace-nowrap">
        {stock.matchYingyou}
      </span>

      <span className={cn('px-2.5 py-0.5 rounded-full text-[11px] font-medium whitespace-nowrap', action.className)}>
        {action.label}
      </span>
    </motion.div>
  );
}
