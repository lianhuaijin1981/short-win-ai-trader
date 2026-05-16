import { useEffect, useState } from 'react';

interface ScoreRingProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  delay?: number;
}

const sizeConfig = {
  sm: { diameter: 56, strokeWidth: 4, fontSize: 16 },
  md: { diameter: 80, strokeWidth: 6, fontSize: 22 },
  lg: { diameter: 120, strokeWidth: 8, fontSize: 32 },
};

function getScoreColor(score: number): string {
  if (score >= 90) return '#c9a84c';
  if (score >= 75) return '#22c55e';
  if (score >= 60) return '#eab308';
  return '#ef4444';
}

export default function ScoreRing({ score, size = 'md', label, delay = 0 }: ScoreRingProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const config = sizeConfig[size];
  const radius = (config.diameter - config.strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = animatedScore / 100;
  const strokeDashoffset = circumference * (1 - progress);
  const color = getScoreColor(score);

  useEffect(() => {
    const timer = setTimeout(() => {
      const duration = 1500;
      const start = performance.now();
      const animate = (now: number) => {
        const elapsed = now - start;
        const t = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - t, 3);
        setAnimatedScore(Math.round(score * eased));
        if (t < 1) requestAnimationFrame(animate);
      };
      requestAnimationFrame(animate);
    }, delay);
    return () => clearTimeout(timer);
  }, [score, delay]);

  return (
    <div className="flex flex-col items-center justify-center">
      <svg
        width={config.diameter}
        height={config.diameter}
        className="transform -rotate-90"
      >
        <circle
          cx={config.diameter / 2}
          cy={config.diameter / 2}
          r={radius}
          fill="none"
          stroke="#141e33"
          strokeWidth={config.strokeWidth}
        />
        <circle
          cx={config.diameter / 2}
          cy={config.diameter / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={config.strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: 'stroke-dashoffset 100ms ease-out' }}
        />
        <text
          x={config.diameter / 2}
          y={config.diameter / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={color}
          fontSize={config.fontSize}
          fontWeight="700"
          fontFamily="'JetBrains Mono', monospace"
          transform={`rotate(90 ${config.diameter / 2} ${config.diameter / 2})`}
        >
          {animatedScore}
        </text>
      </svg>
      {label && (
        <span className="text-[12px] text-[#475569] mt-1 font-sans">{label}</span>
      )}
    </div>
  );
}
