import type { ReactNode } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-[100dvh] bg-[#060b14] relative">
      {/* Background pattern */}
      <div
        className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none"
        style={{ backgroundImage: 'url(/hero-bg-pattern.png)', backgroundSize: 'cover', backgroundPosition: 'center' }}
      />

      <Sidebar />
      <TopBar />

      {/* Main content area */}
      <main className="relative z-10 pt-14 pl-[240px] transition-all duration-300">
        <div className="p-6 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
