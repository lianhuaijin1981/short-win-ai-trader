import { cn } from '@/lib/utils';

interface MetricBadgeProps {
  value: number;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  className?: string;
  size?: 'sm' | 'md';
}

export default function MetricBadge({
  value,
  suffix = '%',
  prefix = '',
  decimals = 2,
  className,
  size = 'md',
}: MetricBadgeProps) {
  const isUp = value >= 0;
  const formattedValue = value > 0 && prefix !== '+' ? `+${value.toFixed(decimals)}` : value.toFixed(decimals);

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center font-mono font-medium rounded-full whitespace-nowrap',
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-0.5 text-[13px]',
        isUp
          ? 'bg-[rgba(239,68,68,0.15)] text-[#ef4444]'
          : 'bg-[rgba(34,197,94,0.15)] text-[#22c55e]',
        className
      )}
    >
      {isUp ? '+' : ''}{formattedValue}{suffix}
    </span>
  );
}
