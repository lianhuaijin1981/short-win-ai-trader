import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Activity,
  Eye,
  Fingerprint,
  Target,
  BarChart3,
  ClipboardCheck,
  Newspaper,
  FileText,
  History,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { navItems } from '@/data/mockData';

const iconMap: Record<string, React.ElementType> = {
  LayoutDashboard,
  Activity,
  Eye,
  Fingerprint,
  Target,
  BarChart3,
  ClipboardCheck,
  Newspaper,
  FileText,
  History,
};

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 240 }}
      transition={{ duration: 0.3, ease: [0.25, 1, 0.5, 1] as [number, number, number, number] }}
      className="fixed left-0 top-0 h-screen z-50 bg-[#0d1526] border-r border-[rgba(148,163,184,0.1)] flex flex-col"
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-[rgba(148,163,184,0.1)]">
        <img src="/logo-icon.png" alt="logo" className="w-8 h-8 shrink-0" />
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="ml-3 text-[14px] font-mono font-bold text-[#c9a84c] whitespace-nowrap overflow-hidden"
          >
            AI交易智能体
          </motion.span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) => {
          const Icon = iconMap[item.icon] || LayoutDashboard;
          const isActive = location.pathname === item.path;

          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 relative group',
                isActive
                  ? 'bg-[#141e33] text-[#c9a84c]'
                  : 'text-[#94a3b8] hover:bg-[#141e33] hover:text-[#f1f5f9]'
              )}
            >
              {/* Active indicator */}
              {isActive && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-[#c9a84c] rounded-r-full"
                />
              )}

              <Icon size={20} className="shrink-0" />

              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-[14px] font-medium whitespace-nowrap overflow-hidden"
                >
                  {item.label}
                </motion.span>
              )}

              {/* Tooltip for collapsed */}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2.5 py-1 bg-[#1a2744] text-[#f1f5f9] text-[12px] rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity duration-200 border border-[rgba(148,163,184,0.1)]">
                  {item.label}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom: iFind status + time */}
      <div className="p-3 border-t border-[rgba(148,163,184,0.1)]">
        <div className="flex items-center gap-2 px-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-pulse-dot absolute inline-flex h-full w-full rounded-full bg-[#22c55e] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22c55e]" />
          </span>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-[11px] text-[#94a3b8] whitespace-nowrap"
            >
              iFind实时连接中
            </motion.span>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-[#141e33] border border-[rgba(148,163,184,0.1)] flex items-center justify-center text-[#94a3b8] hover:text-[#c9a84c] transition-colors z-50"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>
    </motion.aside>
  );
}
