"use client";

import { usePathname } from "@/i18n/routing";
import { Link } from "@/i18n/routing";
import { Home, FileText, Briefcase, TrendingUp, User } from "lucide-react";

const navItems = [
  { icon: Home, label: "首页", href: "/dashboard" },
  { icon: FileText, label: "简历", href: "/vault" },
  { icon: Briefcase, label: "求职", href: "/jobs" },
  { icon: TrendingUp, label: "数据", href: "/analytics" },
  { icon: User, label: "我的", href: "/settings" },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-border-subtle z-50">
      <div className="flex items-center justify-around py-2">
        {navItems.map((item) => {
          const isActive = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center px-3 py-1 ${
                isActive ? "text-terra" : "text-text-muted"
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span className="text-xs mt-0.5">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
