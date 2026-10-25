import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, HeartHandshake, Compass, UserCheck, Layers } from 'lucide-react';
import Badge from '../ui/Badge';

/**
 * Reusable top navigation shell for MatchLens.
 * Displays brand logo/wordmark, active section route indicators, and warm minimalist layout.
 */
export const AppShell = ({ children }) => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Welcome', icon: Sparkles },
    { path: '/interview', label: '1. Onboarding', icon: Compass },
    { path: '/profile/review', label: 'Review Profile', icon: UserCheck },
    { path: '/assessment', label: '2. Assessment', icon: Layers },
    { path: '/matches', label: '3. Matches', icon: HeartHandshake },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF6F0] text-[#2B2D42]">
      {/* Header Bar */}
      <header className="sticky top-0 z-30 bg-[#FAF6F0]/90 backdrop-blur-md border-b border-[#E8E3DC]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-[#E07A5F] flex items-center justify-center text-white shadow-xs group-hover:bg-[#C85A3F] transition-colors">
              <HeartHandshake className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-semibold text-base tracking-tight text-[#2B2D42]">
                MatchLens
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest text-[#E07A5F] -mt-1">
                Reciprocal Match
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5 bg-white/70 p-1 rounded-xl border border-[#E8E3DC]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-150 ${
                    isActive
                      ? 'bg-[#E07A5F] text-white shadow-xs font-semibold'
                      : 'text-[#5C627A] hover:text-[#2B2D42] hover:bg-[#FAF6F0]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Minimal Status Tag */}
          <div className="flex items-center gap-2">
            <Badge variant="rose" size="sm" icon={Sparkles}>
              AI-Assisted
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 flex flex-col">
        {children}
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-[#E8E3DC] py-6 text-center text-xs text-[#5C627A]">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>MatchLens &copy; {new Date().getFullYear()} — Reciprocal Compatibility Engine</span>
          <span className="text-[11px] text-[#A0A4B8]">
            Phase 7.1 Frontend Architecture
          </span>
        </div>
      </footer>
    </div>
  );
};

export default AppShell;
