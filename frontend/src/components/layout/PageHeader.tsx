"use client";

import { usePathname } from "@/i18n/routing";
import { ChevronLeft } from "lucide-react";

const pageTitles: Record<string, string> = {
  "/dashboard": "首页",
  "/vault": "简历",
  "/jobs": "求职",
  "/interview": "面试准备",
  "/analytics": "数据分析",
  "/settings": "我的",
};

export function PageHeader() {
  const pathname = usePathname();
  const title = pageTitles[pathname || ""] || "AI Career Co-pilot";

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-border-subtle px-4 py-3">
      <div className="flex items-center justify-between">
        <h1 className="text-base font-bold text-dark">{title}</h1>
      </div>
    </header>
  );
}
