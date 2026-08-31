"use client";

import { usePathname } from "@/i18n/routing";
import { BottomNav } from "./BottomNav";
import { PageHeader } from "./PageHeader";

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-paper flex flex-col">
      <PageHeader />
      <main className="flex-1 pb-20">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
