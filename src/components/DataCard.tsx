import { motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface DataCardProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  header?: ReactNode;
  noPadding?: boolean;
}

export default function DataCard({ children, className, delay = 0, header, noPadding = false }: DataCardProps) {
  return (
    <motion.div
      initial={{ scale: 0.97, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        duration: 0.5,
        delay: delay / 1000,
        ease: [0.16, 1, 0.3, 1] as [number, number, number, number],
      }}
      className={cn(
        'rounded-[10px] border border-[rgba(148,163,184,0.1)] bg-[#0d1526]',
        'transition-all duration-200',
        'hover:-translate-y-0.5 hover:border-[rgba(201,168,76,0.3)] hover:shadow-elevated',
        className
      )}
    >
      {header && (
        <div className="px-4 pt-4 pb-2 flex items-center justify-between">{header}</div>
      )}
      <div className={cn(!noPadding && 'p-4', !noPadding && header && 'pt-0')}>{children}</div>
    </motion.div>
  );
}
